import cv2
import numpy as np
from pathlib import Path
import sys
import os

# Add the backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.cv.preprocess import PreprocessEngine
from app.cv.node_detector import NodeDetector

def debug_pipeline():
    engine = PreprocessEngine()
    detector = NodeDetector()
    
    img_path = Path("backend/data/samples/flowchart.png")
    if not img_path.exists():
        print(f"Error: {img_path} not found")
        return
    
    img = cv2.imread(str(img_path))
    print(f"Original image shape: {img.shape}")
    
    # Resize like main.py
    img_resized = cv2.resize(img, (1280, 960))
    print(f"Resized image shape: {img_resized.shape}")
    
    binary, gray, _ = engine.preprocess_for_detection(img_resized)
    
    white_pixels = np.count_nonzero(binary)
    print(f"Binary image white pixels: {white_pixels}/{binary.size}")
    
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Number of contours found: {len(contours)}")
    
    large_contours = [c for c in contours if cv2.contourArea(c) > 50]
    print(f"Number of contours with area > 50: {len(large_contours)}")
    if large_contours:
        areas = [cv2.contourArea(c) for c in large_contours]
        print(f"Top 5 areas: {sorted(areas, reverse=True)[:5]}")
    
    nodes = detector.detect(binary)
    print(f"Number of nodes detected: {len(nodes)}")
    
    # Save binary for inspection
    cv2.imwrite("debug_binary.png", binary)
    print("Saved debug_binary.png")

if __name__ == "__main__":
    debug_pipeline()
