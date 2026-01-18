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
            
        # Simplistic merging logic (can be optimized with Union-Find)
        merged_groups = []
        used_indices = set()
        
        for i in range(len(nodes)):
            if i in used_indices:
                continue
            
            current_group = [nodes[i]]
            used_indices.add(i)
            
            for j in range(i + 1, len(nodes)):
                if j in used_indices:
                    continue
                    
                if self.calculate_iou(nodes[i]['bbox'], nodes[j]['bbox']) > self.iou_threshold:
                    current_group.append(nodes[j])
                    used_indices.add(j)
            
            merged_groups.append(current_group)
            
        # Create consolidated nodes
        logical_nodes = []
        for i, group in enumerate(merged_groups):
            # Union of bounding boxes
            min_x = min(n['bbox']['x'] for n in group)
            min_y = min(n['bbox']['y'] for n in group)
            max_x = max(n['bbox']['x'] + n['bbox']['w'] for n in group)
            max_y = max(n['bbox']['y'] + n['bbox']['h'] for n in group)
            
            # Use properties from the largest contour in the group
            primary_node = max(group, key=lambda x: x['area'])
            
            logical_nodes.append({
                'id': f"logical_node_{i+1}",
                'raw_ids': [n['id'] for n in group],
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
                'circularity': primary_node['circularity'],
                'labels': []
            })
            
        return logical_nodes

    def group_text_into_nodes(self, nodes: List[Dict], text_elements: List[Dict]) -> List[Dict]:
        """Assign OCR text elements to their containing shapes"""
        for node in nodes:
            bbox = node['bbox']
            node_labels = []
            
            for text_info in text_elements:
                t_bbox = text_info['bbox']
                # Check center of text box is inside shape bbox
                tx_c = t_bbox['x'] + t_bbox['w'] / 2
                ty_c = t_bbox['y'] + t_bbox['h'] / 2
                
                if (bbox['x'] <= tx_c <= bbox['x'] + bbox['w'] and
                    bbox['y'] <= ty_c <= bbox['y'] + bbox['h']):
                    node_labels.append(text_info['text'])
            
            # Join fragments in likely reading order (top-to-bottom)
            # (In a real system, we'd sort by y then x)
            node['labels'] = node_labels
            
        return nodes
