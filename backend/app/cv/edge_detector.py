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
    
    def detect_edges_from_contours(self, image, nodes: List[Dict]) -> List[Dict[str, Any]]:
        """
        Refined Edge detection:
        1. Multi-scale line detection
        2. Orientation-based clustering
        3. Endpoint matching to nearest logical shapes
        """
        if len(nodes) < 2:
            return []
            
        # 1. Detect raw segments
        raw_lines = self.detect_lines(image, threshold=50) # Use lower threshold for more segments
        if raw_lines is None or len(raw_lines) == 0:
            return []
            
        # flatten segments [x1, y1, x2, y2]
        segments = [line[0] for line in raw_lines]
        
        # 2. Cluster segments (Simplified: group by proximity and angle)
        clusters = self._cluster_segments(segments)
        
        # 3. Connect logical nodes via clustered edges
        logical_edges = []
        for cluster in clusters:
            # Represent cluster by its endpoints
            x1, y1, x2, y2 = cluster['endpoints']
            
            source_id = self._find_nearest_node(nodes, (x1, y1))
            target_id = self._find_nearest_node(nodes, (x2, y2))
            
            if source_id and target_id and source_id != target_id:
                # Basic direction heuristic for now (source to target)
                logical_edges.append({
                    'source': source_id,
                    'target': target_id,
                    'direction': '->',
                    'label': ''
                })
        
        # Deduplicate edges between same source-target pair
        unique_edges = {}
        for edge in logical_edges:
            key = (edge['source'], edge['target'])
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
        """Cluster raw segments that belong to the same logical line/arrow"""
        if not segments:
            return []
            
        clusters = []
        used = set()
        
        for i, s1 in enumerate(segments):
            if i in used:
                continue
                
            current_cluster = [s1]
            used.add(i)
            
            # Simple greedy clustering (proximity of endpoints)
            for j, s2 in enumerate(segments):
                if j in used:
                    continue
                    
                # Check if any endpoints are close (threshold 30px)
                if self._get_min_endpoint_dist(s1, s2) < 30:
                    current_cluster.append(s2)
                    used.add(j)
                    
            # Compute aggregate endpoints for the cluster
            xs = [s[0] for s in current_cluster] + [s[2] for s in current_cluster]
            ys = [s[1] for s in current_cluster] + [s[3] for s in current_cluster]
            
            clusters.append({
                'segments': current_cluster,
                'endpoints': (min(xs), min(ys), max(xs), max(ys))
            })
            
        return clusters

    def _get_min_endpoint_dist(self, s1, s2):
        p1a, p1b = (s1[0], s1[1]), (s1[2], s1[3])
        p2a, p2b = (s2[0], s2[1]), (s2[2], s2[3])
        
        dists = [
            math.sqrt((p1a[0]-p2a[0])**2 + (p1a[1]-p2a[1])**2),
            math.sqrt((p1a[0]-p2b[0])**2 + (p1a[1]-p2b[1])**2),
            math.sqrt((p1b[0]-p2a[0])**2 + (p1b[1]-p2a[1])**2),
            math.sqrt((p1b[0]-p2b[0])**2 + (p1b[1]-p2b[1])**2)
        ]
        return min(dists)

    def _find_nearest_node(self, nodes: List[Dict], point: tuple, max_dist: int = 150) -> str:
        """Find node whose center is closest to point"""
        min_dist = float('inf')
        best_id = None
        
        for node in nodes:
            center = node['center']
            dist = math.sqrt((center['x'] - point[0])**2 + (center['y'] - point[1])**2)
            if dist < min_dist and dist < max_dist:
                min_dist = dist
                best_id = node['id']
        return best_id
