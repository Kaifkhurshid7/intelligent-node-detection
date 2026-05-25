"""
Edge and connection detection service.

Identifies arrows and lines connecting diagram nodes using the
Hough Line Transform, then maps them to logical source→target edges.
"""

import cv2
import math
import numpy as np
from typing import List, Dict, Any, Tuple

from app.core.config import (
    HOUGH_THRESHOLD,
    MIN_LINE_LENGTH,
    MAX_LINE_GAP,
    SEGMENT_CLUSTER_DISTANCE,
    SEGMENT_ANGLE_TOLERANCE,
    MAX_EDGE_NODE_DISTANCE,
    MAX_LABEL_EDGE_DISTANCE,
)
from app.core.logging import logger


class EdgeDetector:
    """
    Detects directed connections between diagram nodes.

    Pipeline:
        1. Detect raw line segments via Probabilistic Hough Transform
        2. Cluster co-linear segments into logical edges
        3. Map edge endpoints to nearest nodes
        4. Assign text labels (Yes/No) to their closest edges
    """

    def detect(
        self,
        binary_image: np.ndarray,
        nodes: List[Dict],
        label_elements: List[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect logical edges between nodes.

        Args:
            binary_image: Preprocessed binary mask.
            nodes: List of logical nodes with bounding boxes.
            label_elements: Small text nodes identified as edge labels.

        Returns:
            List of edge dictionaries with source, target, and label.
        """
        if len(nodes) < 2:
            return []

        # Step 1: Detect raw line segments
        raw_lines = self._detect_lines(binary_image)
        if not raw_lines:
            return []

        segments = [line[0] for line in raw_lines]

        # Step 2: Cluster segments that form the same logical connection
        clusters = self._cluster_segments(segments)

        # Step 3: Map cluster endpoints to nearest nodes
        edges = []
        for cluster in clusters:
            x1, y1, x2, y2 = cluster["endpoints"]
            source_id = self._find_nearest_node(nodes, (x1, y1))
            target_id = self._find_nearest_node(nodes, (x2, y2))

            if source_id and target_id and source_id != target_id:
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "direction": "->",
                    "label": "",
                    "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                })

        # Step 4: Assign labels from edge-label elements (e.g., "Yes", "No")
        if label_elements:
            self._assign_labels(edges, label_elements)

        # Deduplicate edges between same source-target pair
        unique = {}
        for edge in edges:
            key = (edge["source"], edge["target"], edge["label"])
            if key not in unique:
                unique[key] = edge

        result = list(unique.values())
        logger.info(
            f"Detected {len(result)} logical edges from {len(segments)} raw segments"
        )
        return result

    def _detect_lines(self, image: np.ndarray) -> List:
        """
        Apply Probabilistic Hough Line Transform.

        HoughLinesP is preferred over standard Hough because it returns
        actual line segment endpoints rather than infinite lines.
        """
        lines = cv2.HoughLinesP(
            image,
            rho=1,
            theta=np.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=MIN_LINE_LENGTH,
            maxLineGap=MAX_LINE_GAP,
        )
        return lines.tolist() if lines is not None else []

    def _cluster_segments(self, segments: List) -> List[Dict]:
        """
        Group co-linear, proximal segments into logical edges.

        Segments belonging to the same arrow/line are often fragmented
        by the Hough transform. We cluster them by:
            - Endpoint proximity (< SEGMENT_CLUSTER_DISTANCE px)
            - Angular similarity (< SEGMENT_ANGLE_TOLERANCE degrees)

        The cluster's final endpoints are the two most distant points
        across all member segments.
        """
        if not segments:
            return []

        # Pre-compute angles for all segments
        segment_data = []
        for s in segments:
            angle = math.degrees(math.atan2(s[3] - s[1], s[2] - s[0])) % 180
            segment_data.append({"coords": s, "angle": angle})

        clusters = []
        used = set()

        for i, s1 in enumerate(segment_data):
            if i in used:
                continue

            cluster_coords = [s1["coords"]]
            used.add(i)

            for j, s2 in enumerate(segment_data):
                if j in used:
                    continue

                # Check endpoint proximity
                dist = self._min_endpoint_distance(s1["coords"], s2["coords"])

                # Check angular alignment
                angle_diff = abs(s1["angle"] - s2["angle"])
                angle_diff = min(angle_diff, 180 - angle_diff)

                if dist < SEGMENT_CLUSTER_DISTANCE and angle_diff < SEGMENT_ANGLE_TOLERANCE:
                    cluster_coords.append(s2["coords"])
                    used.add(j)

            # Find the two most distant points in the cluster
            endpoints = self._find_extreme_points(cluster_coords)
            clusters.append({"segments": cluster_coords, "endpoints": endpoints})

        return clusters

    def _find_extreme_points(self, segments: List) -> Tuple[int, int, int, int]:
        """Find the pair of points with maximum distance in a segment cluster."""
        points = []
        for s in segments:
            points.append((s[0], s[1]))
            points.append((s[2], s[3]))

        max_dist = 0
        best = (points[0][0], points[0][1], points[1][0], points[1][1])

        for p1 in points:
            for p2 in points:
                d = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
                if d > max_dist:
                    max_dist = d
                    best = (p1[0], p1[1], p2[0], p2[1])

        return best

    def _min_endpoint_distance(self, s1: List, s2: List) -> float:
        """Compute minimum distance between any pair of endpoints from two segments."""
        points_1 = [(s1[0], s1[1]), (s1[2], s1[3])]
        points_2 = [(s2[0], s2[1]), (s2[2], s2[3])]

        return min(
            math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            for p1 in points_1
            for p2 in points_2
        )

    def _find_nearest_node(
        self, nodes: List[Dict], point: Tuple[float, float]
    ) -> str | None:
        """
        Find the node whose bounding box boundary is closest to a point.

        Uses distance-to-rectangle calculation rather than center distance,
        which is more accurate for connecting arrows to shape edges.
        """
        px, py = point
        min_dist = float("inf")
        best_id = None

        for node in nodes:
            bbox = node["bbox"]
            # Distance from point to nearest edge of the rectangle
            dx = max(bbox["x"] - px, 0, px - (bbox["x"] + bbox["w"]))
            dy = max(bbox["y"] - py, 0, py - (bbox["y"] + bbox["h"]))
            dist = math.hypot(dx, dy)

            if dist < min_dist and dist < MAX_EDGE_NODE_DISTANCE:
                min_dist = dist
                best_id = node["id"]

        return best_id

    def _assign_labels(
        self, edges: List[Dict], label_elements: List[Dict]
    ) -> None:
        """
        Assign text labels to their nearest edge.

        Edge labels like "Yes"/"No" are small text nodes positioned
        near the midpoint of their associated connection line.
        """
        for label_node in label_elements:
            label_text = " ".join(label_node.get("labels", []))
            label_center = label_node["center"]

            min_dist = float("inf")
            best_edge = None

            for edge in edges:
                edge_center = edge["center"]
                dist = math.hypot(
                    edge_center[0] - label_center["x"],
                    edge_center[1] - label_center["y"],
                )
                if dist < min_dist and dist < MAX_LABEL_EDGE_DISTANCE:
                    min_dist = dist
                    best_edge = edge

            if best_edge:
                best_edge["label"] = label_text
