"""
Node merging and grouping service.

Transforms raw contour detections into logical diagram nodes by:
1. Merging spatially proximal fragments into unified shapes
2. Assigning OCR text elements to their containing nodes
"""

import numpy as np
from typing import List, Dict, Any

from app.core.config import PROXIMAL_MERGE_THRESHOLD
from app.core.logging import logger


class NodeProcessor:
    """
    Consolidates fragmented raw detections into meaningful logical nodes.

    Diagrams often produce multiple overlapping contours for a single
    visual element (e.g., a rectangle with inner text creates nested
    contours). This processor merges them using spatial proximity.
    """

    def merge_proximal_nodes(
        self, nodes: List[Dict], threshold: int = PROXIMAL_MERGE_THRESHOLD
    ) -> List[Dict]:
        """
        Merge nodes whose centers are within a pixel distance threshold.

        Uses connected-component analysis: if node A is close to B, and
        B is close to C, all three merge into one logical node.

        Args:
            nodes: Raw detected nodes from NodeDetector.
            threshold: Maximum center-to-center distance for merging (px).

        Returns:
            List of merged logical nodes with unified bounding boxes.
        """
        if not nodes:
            return []

        # Build adjacency graph based on center proximity
        adjacency = {i: [] for i in range(len(nodes))}
        for i in range(len(nodes)):
            center_i = nodes[i]["center"]
            for j in range(i + 1, len(nodes)):
                center_j = nodes[j]["center"]
                distance = np.sqrt(
                    (center_i["x"] - center_j["x"]) ** 2
                    + (center_i["y"] - center_j["y"]) ** 2
                )
                if distance < threshold:
                    adjacency[i].append(j)
                    adjacency[j].append(i)

        # Extract connected components via DFS
        visited = set()
        groups = []
        for i in range(len(nodes)):
            if i in visited:
                continue
            component = []
            stack = [i]
            visited.add(i)
            while stack:
                current = stack.pop()
                component.append(nodes[current])
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            groups.append(component)

        # Consolidate each group into a single logical node
        logical_nodes = []
        for idx, group in enumerate(groups):
            logical_nodes.append(self._merge_group(group, idx + 1))

        logger.info(
            f"Merged {len(nodes)} raw nodes → {len(logical_nodes)} logical nodes"
        )
        return logical_nodes

    def assign_text_to_nodes(
        self, nodes: List[Dict], text_elements: List[Dict]
    ) -> List[Dict]:
        """
        Spatially assign OCR text elements to their containing nodes.

        For each text element, checks if its center falls within a node's
        bounding box (with small margin). Text is sorted by reading order
        (top-to-bottom, left-to-right) before assignment.

        Args:
            nodes: Logical nodes with bounding boxes.
            text_elements: OCR results with text and bbox.

        Returns:
            Nodes with populated 'labels' field.
        """
        for node in nodes:
            bbox = node["bbox"]
            existing_labels = set(node.get("labels", []))
            new_text = []

            for text_info in text_elements:
                if text_info["text"] in existing_labels:
                    continue

                t_bbox = text_info["bbox"]
                text_center_x = t_bbox["x"] + t_bbox["w"] / 2
                text_center_y = t_bbox["y"] + t_bbox["h"] / 2

                # Check if text center falls within node bbox (5px margin)
                margin = 5
                if (
                    bbox["x"] - margin <= text_center_x <= bbox["x"] + bbox["w"] + margin
                    and bbox["y"] - margin <= text_center_y <= bbox["y"] + bbox["h"] + margin
                ):
                    new_text.append(text_info)

            # Sort by reading order and append
            new_text.sort(key=lambda t: (t["bbox"]["y"], t["bbox"]["x"]))
            for t in new_text:
                existing_labels.add(t["text"])

            node["labels"] = list(existing_labels)

        return nodes

    def _merge_group(self, group: List[Dict], group_id: int) -> Dict[str, Any]:
        """
        Merge a group of overlapping nodes into a single logical node.

        Uses the union of all bounding boxes and inherits shape type
        from the largest contour in the group (most representative).
        """
        min_x = min(n["bbox"]["x"] for n in group)
        min_y = min(n["bbox"]["y"] for n in group)
        max_x = max(n["bbox"]["x"] + n["bbox"]["w"] for n in group)
        max_y = max(n["bbox"]["y"] + n["bbox"]["h"] for n in group)

        # The largest contour best represents the intended shape
        primary = max(group, key=lambda n: n["area"])

        # Collect any pre-existing labels from all group members
        all_labels = []
        for n in group:
            all_labels.extend(n.get("labels", []))

        width = max_x - min_x
        height = max_y - min_y

        return {
            "id": f"logical_node_{group_id}",
            "raw_ids": [n["id"] for n in group],
            "type": primary["type"],
            "bbox": {"x": int(min_x), "y": int(min_y), "w": int(width), "h": int(height)},
            "center": {"x": int(min_x + width / 2), "y": int(min_y + height / 2)},
            "area": float(width * height),
            "circularity": primary.get("circularity", 0),
            "solidity": primary.get("solidity", 0),
            "aspect_ratio": float(width / height) if height > 0 else 0,
            "labels": all_labels,
        }
