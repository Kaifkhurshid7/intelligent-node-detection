"""Node and shape detection module"""
import cv2
import numpy as np
from typing import List, Dict, Any


class NodeDetector:
    """Detects nodes and shapes in diagram images"""
    
    def __init__(self):
        """Initialize node detector"""
        self.node_counter = 0
        self.MIN_CONTOUR_AREA = 100 # Ignore dots/punctuation
        self.MIN_BBOX_SIZE = 400   # 20x20 minimum logical shape size
    
    def detect(self, image) -> List[Dict[str, Any]]:
        """
        Detect all nodes/shapes in the image.
        Uses CCOMP hierarchy to only process external contours (avoiding holes).
        """
        nodes = []
        self.node_counter = 0
        
        # Check if image is valid
        if image is None or len(image.shape) != 2:
            return nodes

        # Find all contours (Baseline stage: maximizing robustness by over-detecting)
        res = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Handle OpenCV version difference in return values
        contours = res[0] if len(res) == 2 else res[1]
            
        for i, contour in enumerate(contours):
            # Pre-filter by area before full analysis
            if cv2.contourArea(contour) < self.MIN_CONTOUR_AREA:
                continue
                
            node = self._analyze_contour(contour)
            if node and self._is_valid_node(node):
                nodes.append(node)
        
        return nodes
    
    def _analyze_contour(self, contour) -> Dict[str, Any]:
        """
        Analyze a contour and extract node properties.
        """
        area = cv2.contourArea(contour)
        if area < self.MIN_CONTOUR_AREA:
            return None
        
        x, y, w, h = cv2.boundingRect(contour)
        if w < 5 or h < 5:
            return None
        
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return None
        
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # Approximate shape
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Classify shape
        shape_type = self._classify_shape(approx, circularity, w, h)
        
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        self.node_counter += 1
        
        return {
            'id': f"node_{self.node_counter}",
            'type': shape_type,
            'bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
            'center': {'x': int(x + w/2), 'y': int(y + h/2)},
            'area': float(area),
            'perimeter': float(perimeter),
            'circularity': float(circularity),
            'solidity': float(solidity),
            'vertices': len(approx),
            'aspect_ratio': float(w / h) if h > 0 else 0,
        }
    
    def _classify_shape(self, approx, circularity, w, h) -> str:
        vertices = len(approx)
        aspect_ratio = w / h if h > 0 else 0
        
        # High-circularity -> Circle
        if circularity > 0.85:
            return 'circle'
        
        # Medium-circularity + Aspect Ratio -> Oval
        if circularity > 0.6:
            return 'oval'
        
        # Quadrilaterals
        if vertices == 4:
            # Diamond usually has aspect ratio close to 1.0 in flowcharts
            if 0.8 < aspect_ratio < 1.2:
                return 'diamond'
            else:
                return 'rectangle'
        
        if vertices == 3: return 'triangle'
        if vertices >= 5: return 'polygon'
        
        return 'unknown'
    
    def _is_valid_node(self, node) -> bool:
        bbox = node['bbox']
        size = bbox['w'] * bbox['h']
        
        if size < self.MIN_BBOX_SIZE:
            return False
            
        aspect = node['aspect_ratio']
        if aspect < 0.1 or aspect > 10: # Refined aspect ratio limits
            return False
            
        return True
