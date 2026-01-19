"""Module for merging and processing detected nodes"""
from typing import List, Dict, Any
import numpy as np

class NodeProcessor:
    """Handles logical grouping of raw visual primitives into meaningful nodes"""
    
    def __init__(self, iou_threshold: float = 0.4):
        self.iou_threshold = iou_threshold

    def calculate_iou(self, bbox1: Dict, bbox2: Dict) -> float:
        """Calculate Intersection over Union of two bounding boxes"""
        x1 = max(bbox1['x'], bbox2['x'])
        y1 = max(bbox1['y'], bbox2['y'])
        x2 = min(bbox1['x'] + bbox1['w'], bbox2['x'] + bbox2['w'])
        y2 = min(bbox1['y'] + bbox1['h'], bbox2['y'] + bbox2['h'])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = bbox1['w'] * bbox1['h']
        area2 = bbox2['w'] * bbox2['h']
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def merge_overlapping_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """Merge nodes that have high IoU into single logical entities"""
        if not nodes:
            return []
            
        # Grouping logic: find all connected components of overlapping nodes
        adj = {i: [] for i in range(len(nodes))}
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if self.calculate_iou(nodes[i]['bbox'], nodes[j]['bbox']) > self.iou_threshold:
                    adj[i].append(j)
                    adj[j].append(i)
        
        visited = set()
        merged_groups = []
        
        for i in range(len(nodes)):
            if i not in visited:
                component = []
                stack = [i]
                visited.add(i)
                while stack:
                    curr = stack.pop()
                    component.append(nodes[curr])
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
                merged_groups.append(component)
            
        # Create consolidated nodes
        logical_nodes = []
        for i, group in enumerate(merged_groups):
            # Union of bounding boxes
            min_x = min(n['bbox']['x'] for n in group)
            min_y = min(n['bbox']['y'] for n in group)
            max_x = max(n['bbox']['x'] + n['bbox']['w'] for n in group)
            max_y = max(n['bbox']['y'] + n['bbox']['h'] for n in group)
            
            # Use properties from the largest contour in the group to determine shape type
            primary_node = max(group, key=lambda x: x['area'])
            
            logical_nodes.append({
                'id': f"logical_node_{i+1}",
                'raw_ids': [n['id'] for n in group],
                'type': primary_node['type'], # Predominant shape type
                'bbox': {
                    'x': int(min_x),
                    'y': int(min_y),
                    'w': int(max_x - min_x),
                    'h': int(max_y - min_y)
                },
                'center': {
                    'x': int(min_x + (max_x - min_x) / 2),
                    'y': int(min_y + (max_y - min_y) / 2)
                },
                'area': float((max_x - min_x) * (max_y - min_y)),
                'circularity': primary_node.get('circularity', 0),
                'solidity': primary_node.get('solidity', 0),
                'aspect_ratio': float((max_x - min_x) / (max_y - min_y)) if (max_y - min_y) > 0 else 0,
                'labels': []
            })
            
        return logical_nodes

    def merge_proximal_nodes(self, nodes: List[Dict], threshold: int = 50) -> List[Dict]:
        """
        Merge nodes whose centers are within the pixel threshold using clustering.
        Reduces fragmentation in logical flow.
        """
        if not nodes:
            return []

        # Connectivity logic: nodes are connected if their centers are close
        adj = {i: [] for i in range(len(nodes))}
        for i in range(len(nodes)):
            c1 = nodes[i]['center']
            for j in range(i + 1, len(nodes)):
                c2 = nodes[j]['center']
                dist = np.sqrt((c1['x'] - c2['x'])**2 + (c1['y'] - c2['y'])**2)
                if dist < threshold:
                    adj[i].append(j)
                    adj[j].append(i)

        visited = set()
        merged_groups = []

        # Connected components extraction
        for i in range(len(nodes)):
            if i not in visited:
                component = []
                stack = [i]
                visited.add(i)
                while stack:
                    curr = stack.pop()
                    component.append(nodes[curr])
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
                merged_groups.append(component)

        logical_nodes = []
        for i, group in enumerate(merged_groups):
            # Union of bboxes
            min_x = min(n['bbox']['x'] for n in group)
            min_y = min(n['bbox']['y'] for n in group)
            max_x = max(n['bbox']['x'] + n['bbox']['w'] for n in group)
            max_y = max(n['bbox']['y'] + n['bbox']['h'] for n in group)

            primary_node = max(group, key=lambda x: x['area'])
            
            # Merge labels and raw IDs
            all_labels = []
            for n in group:
                if n.get('labels'):
                    all_labels.extend(n['labels'])
            
            logical_nodes.append({
                'id': f"logical_node_{i+1}",
                'raw_ids': list(set([n['id'] for n in group] + sum([n.get('raw_ids', []) for n in group], []))),
                'type': primary_node['type'],
                'bbox': {
                    'x': int(min_x),
                    'y': int(min_y),
                    'w': int(max_x - min_x),
                    'h': int(max_y - min_y)
                },
                'center': {
                    'x': int(min_x + (max_x - min_x) / 2),
                    'y': int(min_y + (max_y - min_y) / 2)
                },
                'area': float((max_x - min_x) * (max_y - min_y)),
                'circularity': primary_node.get('circularity', 0),
                'solidity': primary_node.get('solidity', 0),
                'aspect_ratio': float((max_x - min_x) / (max_y - min_y)) if (max_y - min_y) > 0 else 0,
                'labels': all_labels
            })
            
        return logical_nodes

    def group_text_into_nodes(self, nodes: List[Dict], text_elements: List[Dict]) -> List[Dict]:
        """Assign OCR text elements to their containing shapes and sort in reading order"""
        for node in nodes:
            bbox = node['bbox']
            contained_text = []
            
            # Use already merged labels if any
            node_labels = set(node.get('labels', []))
            
            for text_info in text_elements:
                if text_info['text'] in node_labels:
                    continue # Already included
                    
                t_bbox = text_info['bbox']
                margin = 5
                tx_c = t_bbox['x'] + t_bbox['w'] / 2
                ty_c = t_bbox['y'] + t_bbox['h'] / 2
                
                if (bbox['x'] - margin <= tx_c <= bbox['x'] + bbox['w'] + margin and
                    bbox['y'] - margin <= ty_c <= bbox['y'] + bbox['h'] + margin):
                    contained_text.append(text_info)
            
            # Sort and append new labels
            sorted_text = sorted(contained_text, key=lambda t: (t['bbox']['y'], t['bbox']['x']))
            for t in sorted_text:
                if t['text'] not in node_labels:
                    node_labels.add(t['text'])
                    
            node['labels'] = list(node_labels)
            
        return nodes
