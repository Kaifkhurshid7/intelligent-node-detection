"""
Logical Node Consolidation Engine.

Transforms raw fragmented visual detections into clean, deduplicated
workflow nodes. This is the critical accuracy layer that sits between
raw detection and semantic classification.

Consolidation strategy:
    1. Remove tiny noise detections (area < threshold)
    2. Merge heavily overlapping bounding boxes (IoU > 0.5)
    3. Eliminate nodes that are likely arrow fragments (extreme aspect ratios)
    4. Deduplicate nodes with identical text labels
    5. Merge nodes whose centers are within proximity threshold
    6. Validate final node set for workflow plausibility
"""

import numpy as np
from typing import List, Dict, Tuple

from app.core.config import MIN_NODE_AREA, PROXIMAL_MERGE_THRESHOLD
from app.core.logging import logger


class NodeConsolidator:
    """
    Reduces raw detection noise into clean logical workflow nodes.

    Applies multiple filtering and merging passes to eliminate
    the fragmentation that contour-based detection produces.
    """

    def __init__(
        self,
        iou_threshold: float = 0.5,
        proximity_threshold: int = None,
        min_area: int = None,
        max_aspect_ratio: float = 8.0,
    ):
        self._iou_threshold = iou_threshold
        self._proximity = proximity_threshold or PROXIMAL_MERGE_THRESHOLD
        self._min_area = min_area or MIN_NODE_AREA
        self._max_aspect = max_aspect_ratio

    def consolidate(self, nodes: List[Dict]) -> List[Dict]:
        """
        Run the full consolidation pipeline.

        Args:
            nodes: Raw detected nodes from NodeDetector.

        Returns:
            Clean, deduplicated logical nodes ready for classification.
        """
        initial_count = len(nodes)

        # Pass 1: Remove noise (tiny detections and extreme aspect ratios)
        nodes = self._filter_noise(nodes)

        # Pass 2: Merge overlapping bounding boxes (IoU-based)
        nodes = self._merge_overlapping(nodes)

        # Pass 3: Merge proximal nodes (center-distance based)
        nodes = self._merge_proximal(nodes)

        # Pass 4: Deduplicate by text content
        nodes = self._deduplicate_by_text(nodes)

        # Pass 5: Remove likely arrow fragments
        nodes = self._remove_arrow_fragments(nodes)

        logger.info(
            f"[Consolidation] {initial_count} raw → {len(nodes)} logical nodes "
            f"({100 - len(nodes)/max(initial_count,1)*100:.0f}% reduction)"
        )
        return nodes

    def _filter_noise(self, nodes: List[Dict]) -> List[Dict]:
        """Remove detections that are too small to be meaningful workflow nodes."""
        return [
            n for n in nodes
            if n.get("area", 0) >= self._min_area
        ]

    def _merge_overlapping(self, nodes: List[Dict]) -> List[Dict]:
        """
        Merge nodes with high bounding-box overlap (IoU > threshold).

        Uses connected-component analysis: if A overlaps B and B overlaps C,
        all three merge into one node.
        """
        if len(nodes) <= 1:
            return nodes

        # Build adjacency based on IoU
        n = len(nodes)
        adjacency = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if self._compute_iou(nodes[i]["bbox"], nodes[j]["bbox"]) > self._iou_threshold:
                    adjacency[i].append(j)
                    adjacency[j].append(i)

        # Extract connected components
        groups = self._find_components(adjacency, n)

        # Merge each group
        return [self._merge_group(group, nodes) for group in groups]

    def _merge_proximal(self, nodes: List[Dict]) -> List[Dict]:
        """Merge nodes whose centers are within proximity threshold."""
        if len(nodes) <= 1:
            return nodes

        n = len(nodes)
        adjacency = {i: [] for i in range(n)}
        for i in range(n):
            ci = nodes[i]["center"]
            for j in range(i + 1, n):
                cj = nodes[j]["center"]
                dist = np.sqrt((ci["x"] - cj["x"])**2 + (ci["y"] - cj["y"])**2)
                if dist < self._proximity:
                    adjacency[i].append(j)
                    adjacency[j].append(i)

        groups = self._find_components(adjacency, n)
        return [self._merge_group(group, nodes) for group in groups]

    def _deduplicate_by_text(self, nodes: List[Dict]) -> List[Dict]:
        """Remove duplicate nodes that have identical text labels."""
        seen_text = {}
        result = []

        for node in nodes:
            text = " ".join(node.get("labels", [])).strip().lower()
            if not text:
                result.append(node)
                continue

            if text not in seen_text:
                seen_text[text] = node
                result.append(node)
            else:
                # Keep the larger one
                existing = seen_text[text]
                if node.get("area", 0) > existing.get("area", 0):
                    result.remove(existing)
                    result.append(node)
                    seen_text[text] = node

        return result

    def _remove_arrow_fragments(self, nodes: List[Dict]) -> List[Dict]:
        """
        Remove detections that are likely arrow/line fragments.

        Arrow fragments typically have extreme aspect ratios (very thin and long)
        and low solidity (not filled shapes).
        """
        result = []
        for node in nodes:
            aspect = node.get("aspect_ratio", 1.0)
            solidity = node.get("solidity", 1.0)

            # Very thin shapes with low solidity are likely arrows
            is_arrow_like = (
                (aspect > self._max_aspect or aspect < 1.0 / self._max_aspect)
                and solidity < 0.5
            )

            if not is_arrow_like:
                result.append(node)

        return result

    def _compute_iou(self, bbox1: Dict, bbox2: Dict) -> float:
        """Compute Intersection over Union of two bounding boxes."""
        x1 = max(bbox1["x"], bbox2["x"])
        y1 = max(bbox1["y"], bbox2["y"])
        x2 = min(bbox1["x"] + bbox1["w"], bbox2["x"] + bbox2["w"])
        y2 = min(bbox1["y"] + bbox1["h"], bbox2["y"] + bbox2["h"])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = bbox1["w"] * bbox1["h"]
        area2 = bbox2["w"] * bbox2["h"]
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def _find_components(self, adjacency: Dict, n: int) -> List[List[int]]:
        """Find connected components via DFS."""
        visited = set()
        components = []

        for i in range(n):
            if i in visited:
                continue
            component = []
            stack = [i]
            visited.add(i)
            while stack:
                curr = stack.pop()
                component.append(curr)
                for neighbor in adjacency[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            components.append(component)

        return components

    def _merge_group(self, indices: List[int], nodes: List[Dict]) -> Dict:
        """Merge a group of node indices into a single logical node."""
        group = [nodes[i] for i in indices]

        # Union bounding box
        min_x = min(n["bbox"]["x"] for n in group)
        min_y = min(n["bbox"]["y"] for n in group)
        max_x = max(n["bbox"]["x"] + n["bbox"]["w"] for n in group)
        max_y = max(n["bbox"]["y"] + n["bbox"]["h"] for n in group)

        # Use properties from the largest node
        primary = max(group, key=lambda n: n.get("area", 0))

        # Collect all labels
        all_labels = []
        for n in group:
            all_labels.extend(n.get("labels", []))
        # Deduplicate while preserving order
        seen = set()
        unique_labels = []
        for label in all_labels:
            if label.lower() not in seen:
                seen.add(label.lower())
                unique_labels.append(label)

        width = max_x - min_x
        height = max_y - min_y

        return {
            "id": primary.get("id", f"node_{indices[0]}"),
            "type": primary.get("type", "unknown"),
            "bbox": {"x": int(min_x), "y": int(min_y), "w": int(width), "h": int(height)},
            "center": {"x": int(min_x + width / 2), "y": int(min_y + height / 2)},
            "area": float(width * height),
            "circularity": primary.get("circularity", 0),
            "solidity": primary.get("solidity", 0),
            "aspect_ratio": float(width / height) if height > 0 else 0,
            "labels": unique_labels,
            "vertices": primary.get("vertices", 4),
            "perimeter": primary.get("perimeter", 0),
            "merged_count": len(group),
        }
