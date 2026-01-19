"""Edge and arrow detection module"""
import cv2
import numpy as np
from typing import List, Dict, Any
import math


class EdgeDetector:
    """Detects edges and arrows connecting nodes"""
    
    def __init__(self):
        """Initialize edge detector"""
        self.min_line_length = 50
        self.max_line_gap = 20
    
    def detect_edges_from_contours(self, image, nodes: List[Dict], label_elements: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Refined Edge detection with label assignment.
        """
        if len(nodes) < 2:
            return []
            
        # 1. Detect raw segments
        raw_lines = self.detect_lines(image, threshold=50)
        if raw_lines is None or len(raw_lines) == 0:
            return []
            
        segments = [line[0] for line in raw_lines]
        
        # 2. Cluster segments
        clusters = self._cluster_segments(segments)
        
        # 3. Connect logical nodes via clustered edges
        logical_edges = []
        for cluster in clusters:
            x1, y1, x2, y2 = cluster['endpoints']
            
            source_id = self._find_nearest_node(nodes, (x1, y1))
            target_id = self._find_nearest_node(nodes, (x2, y2))
            
            if source_id and target_id and source_id != target_id:
                logical_edges.append({
                    'source': source_id,
                    'target': target_id,
                    'direction': '->',
                    'label': '',
                    'center': ((x1+x2)/2, (y1+y2)/2)
                })
        
        # 4. Assign labels from label_elements (Step C)
        if label_elements:
            for label_node in label_elements:
                label_text = ' '.join(label_node.get('labels', []))
                lc = label_node['center']
                
                # Find nearest edge
                min_dist = float('inf')
                best_edge = None
                for edge in logical_edges:
                    ec = edge['center']
                    dist = math.hypot(ec[0] - lc['x'], ec[1] - lc['y'])
                    if dist < min_dist and dist < 150: # max dist 150px
                        min_dist = dist
                        best_edge = edge
                
                if best_edge:
                    best_edge['label'] = label_text

        # Deduplicate edges between same source-target-label triple
        unique_edges = {}
        for edge in logical_edges:
            key = (edge['source'], edge['target'], edge['label'])
            if key not in unique_edges:
                unique_edges[key] = edge
                
        return list(unique_edges.values())

    def detect_lines(self, image, threshold=100) -> List[List[List[int]]]:
        """Detect lines using Hough transform"""
        try:
            lines = cv2.HoughLinesP(
                image,
                rho=1,
                theta=np.pi/180,
                threshold=threshold,
                minLineLength=self.min_line_length,
                maxLineGap=self.max_line_gap
            )
            return lines if lines is not None else []
        except Exception as e:
            print(f"Line detection error: {str(e)}")
            return []

    def _cluster_segments(self, segments: List[List[int]]) -> List[Dict]:
        """Cluster raw segments that belong to the same logical line/arrow using proximity and angle"""
        if not segments:
            return []
            
        clusters = []
        used = set()
        
        # Calculate angles for all segments
        segment_data = []
        for s in segments:
            angle = math.degrees(math.atan2(s[3] - s[1], s[2] - s[0])) % 180
            segment_data.append({'coords': s, 'angle': angle})

        for i, s1 in enumerate(segment_data):
            if i in used:
                continue
                
            current_cluster = [s1['coords']]
            used.add(i)
            
            for j, s2 in enumerate(segment_data):
                if j in used:
                    continue
                
                # Check proximity of endpoints
                dist = self._get_min_endpoint_dist(s1['coords'], s2['coords'])
                
                # Check angular similarity (within 15 degrees)
                angle_diff = abs(s1['angle'] - s2['angle'])
                angle_diff = min(angle_diff, 180 - angle_diff)
                
                if dist < 40 and angle_diff < 15:
                    current_cluster.append(s2['coords'])
                    used.add(j)
                    
            # Compute aggregate endpoints (farthest points in cluster)
            pts = []
            for s in current_cluster:
                pts.append((s[0], s[1]))
                pts.append((s[2], s[3]))
            
            # Find extreme points
            best_pair = (pts[0], pts[1])
            max_d = 0
            for p1 in pts:
                for p2 in pts:
                    d = (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
                    if d > max_d:
                        max_d = d
                        best_pair = (p1, p2)
            
            clusters.append({
                'segments': current_cluster,
                'endpoints': (best_pair[0][0], best_pair[0][1], best_pair[1][0], best_pair[1][1])
            })
            
        return clusters

    def _get_min_endpoint_dist(self, s1, s2):
        p1a, p1b = (s1[0], s1[1]), (s1[2], s1[3])
        p2a, p2b = (s2[0], s2[1]), (s2[2], s2[3])
        
        dists = [
            math.hypot(p1a[0]-p2a[0], p1a[1]-p2a[1]),
            math.hypot(p1a[0]-p2b[0], p1a[1]-p2b[1]),
            math.hypot(p1b[0]-p2a[0], p1b[1]-p2a[1]),
            math.hypot(p1b[0]-p2b[0], p1b[1]-p2b[1])
        ]
        return min(dists)

    def _find_nearest_node(self, nodes: List[Dict], point: tuple, max_dist: int = 200) -> str:
        """Find node whose boundary is closest to point"""
        min_dist = float('inf')
        best_id = None
        
        px, py = point
        for node in nodes:
            bbox = node['bbox']
            # Distance to rectangle
            dx = max(bbox['x'] - px, 0, px - (bbox['x'] + bbox['w']))
            dy = max(bbox['y'] - py, 0, py - (bbox['y'] + bbox['h']))
            dist = math.hypot(dx, dy)
            
            if dist < min_dist and dist < max_dist:
                min_dist = dist
                best_id = node['id']
        return best_id
