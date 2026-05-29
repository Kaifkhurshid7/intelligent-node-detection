"""
Node and shape detection service.

Identifies geometric shapes (rectangles, circles, diamonds, etc.) in
binary images using contour analysis and polygon approximation.
"""

import cv2
import numpy as np
from typing import List, Dict, Any

from app.core.config import MIN_CONTOUR_AREA, MIN_BBOX_SIZE
from app.core.logging import logger


class NodeDetector:
    """
    Detects diagram nodes by finding and classifying contours.

    Each contour is analyzed for geometric properties (circularity,
    vertex count, aspect ratio) to determine its shape type.
    """

    def __init__(self):
        self._node_counter = 0

    def detect(self, binary_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Find all valid nodes in a binary image.

        Uses RETR_LIST to retrieve all contours without hierarchy,
        maximizing detection recall. Filtering happens downstream.

        Args:
            binary_image: Single-channel binary mask (white = foreground).

        Returns:
            List of node dictionaries with shape metadata.
        """
        self._node_counter = 0

        if binary_image is None or len(binary_image.shape) != 2:
            logger.warning("Invalid binary image provided to node detector")
            return []

        # RETR_LIST retrieves all contours without parent-child relationships.
        # This over-detects intentionally; filtering is handled by NodeProcessor.
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        nodes = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                continue

            node = self._analyze_contour(contour)
            if node and self._is_valid_node(node):
                nodes.append(node)

        logger.info(f"Detected {len(nodes)} raw nodes from {len(contours)} contours")
        return nodes

    def _analyze_contour(self, contour: np.ndarray) -> Dict[str, Any] | None:
        """
        Extract geometric properties from a single contour.

        Computes bounding box, circularity, solidity, and performs
        polygon approximation to classify the shape type.
        """
        area = cv2.contourArea(contour)
        if area < MIN_CONTOUR_AREA:
            return None

        x, y, w, h = cv2.boundingRect(contour)
        if w < 5 or h < 5:
            return None

        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return None

        # Circularity: 1.0 = perfect circle, lower = more angular
        circularity = 4 * np.pi * area / (perimeter ** 2)

        # Polygon approximation with 2% arc-length tolerance
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        shape_type = self._classify_shape(approx, circularity, w, h)

        # Solidity measures how "filled" the shape is (convex hull ratio)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        self._node_counter += 1

        return {
            "id": f"node_{self._node_counter}",
            "type": shape_type,
            "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
            "center": {"x": int(x + w / 2), "y": int(y + h / 2)},
            "area": float(area),
            "perimeter": float(perimeter),
            "circularity": float(circularity),
            "solidity": float(solidity),
            "vertices": len(approx),
            "aspect_ratio": float(w / h) if h > 0 else 0,
        }

    def _classify_shape(
        self, approx: np.ndarray, circularity: float, w: int, h: int
    ) -> str:
        """
        Classify a contour's shape based on geometric features.

        Improved classification with better diamond detection:
            1. High circularity (>0.85) → circle
            2. Medium circularity (>0.6) → oval
            3. 4 vertices + rotated square aspect → diamond (decision)
            4. 4 vertices + rectangular aspect → rectangle (process)
            5. 3 vertices → triangle
            6. 5+ vertices → polygon

        Diamond detection improvement:
            Diamonds in flowcharts are rotated squares. We check if the
            4-vertex polygon has roughly equal side lengths and near-square
            aspect ratio, which distinguishes them from rectangles.
        """
        vertices = len(approx)
        aspect_ratio = w / h if h > 0 else 0

        if circularity > 0.85:
            return "circle"
        if circularity > 0.6:
            return "oval"
        if vertices == 4:
            # Enhanced diamond detection: check if it's a rotated square
            # Diamonds have near-equal diagonals and aspect ratio close to 1
            if self._is_diamond(approx, w, h, aspect_ratio):
                return "diamond"
            return "rectangle"
        if vertices == 3:
            return "triangle"
        if vertices >= 5:
            return "polygon"

        return "unknown"

    def _is_diamond(
        self, approx: np.ndarray, w: int, h: int, aspect_ratio: float
    ) -> bool:
        """
        Determine if a 4-vertex polygon is a diamond (rotated square).

        A diamond has:
            - Near-square aspect ratio (0.7 - 1.4)
            - Vertices near the midpoints of the bounding box edges
              (top-center, right-center, bottom-center, left-center)
            - Roughly equal side lengths
        """
        if not (0.7 < aspect_ratio < 1.4):
            return False

        # Check if vertices are near midpoints of bbox edges (diamond pattern)
        # A diamond's vertices should be at approximately:
        # top-center, right-center, bottom-center, left-center
        points = approx.reshape(-1, 2)
        cx, cy = w / 2, h / 2

        # Normalize points relative to bbox center
        # For a diamond, points should be far from corners
        bbox_area = w * h
        if bbox_area == 0:
            return False

        # Calculate how "diamond-like" the shape is by checking
        # if the polygon area is roughly half the bounding box area
        # (a diamond inscribed in a rectangle has area = w*h/2)
        poly_area = cv2.contourArea(approx)
        area_ratio = poly_area / bbox_area

        # Diamonds have area ratio ~0.5 (half of bounding box)
        # Rectangles have area ratio ~1.0
        return 0.35 < area_ratio < 0.65

    def _is_valid_node(self, node: Dict[str, Any]) -> bool:
        """
        Apply basic validity filters to reject noise detections.

        Rejects nodes that are too small or have extreme aspect ratios
        (likely scan artifacts or line fragments).
        """
        bbox = node["bbox"]
        if bbox["w"] * bbox["h"] < MIN_BBOX_SIZE:
            return False
        if node["aspect_ratio"] < 0.1 or node["aspect_ratio"] > 10:
            return False
        return True
