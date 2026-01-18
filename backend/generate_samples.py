"""Script to generate sample diagrams for testing"""
import cv2
import numpy as np
from pathlib import Path

def create_flowchart_sample():
    """Create a simple flowchart with shapes and connections"""
    # Create blank image
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Define colors
    BLACK = (0, 0, 0)
    BLUE = (255, 0, 0)
    GREEN = (0, 255, 0)
    
    # Draw Start (circle)
    cv2.circle(img, (400, 50), 30, BLUE, 2)
    cv2.putText(img, "Start", (370, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1)
    
    # Draw arrow from start to process
    cv2.arrowedLine(img, (400, 80), (400, 120), BLACK, 2)
    
    # Draw Process (rectangle)
    cv2.rectangle(img, (300, 130), (500, 200), BLUE, 2)
    cv2.putText(img, "Process", (350, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1)
    
    # Draw arrow from process to decision
    cv2.arrowedLine(img, (400, 200), (400, 240), BLACK, 2)
    
    # Draw Decision (diamond)
    diamond_pts = np.array([
        [400, 240],
        [500, 300],
        [400, 360],
        [300, 300]
    ], dtype=np.int32)
    cv2.polylines(img, [diamond_pts], True, GREEN, 2)
    cv2.putText(img, "Decision?", (350, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    # Draw arrows from decision (yes/no)
    cv2.arrowedLine(img, (300, 300), (150, 300), BLACK, 2)
    cv2.putText(img, "Yes", (200, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    cv2.arrowedLine(img, (500, 300), (650, 300), BLACK, 2)
    cv2.putText(img, "No", (570, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    # Draw End nodes
    cv2.circle(img, (150, 300), 25, BLUE, 2)
    cv2.putText(img, "End", (130, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    cv2.circle(img, (650, 300), 25, BLUE, 2)
    cv2.putText(img, "End", (630, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    return img


def create_simple_boxes_sample():
    """Create a simple diagram with boxes and connections"""
    img = np.ones((500, 800, 3), dtype=np.uint8) * 255
    
    BLACK = (0, 0, 0)
    RED = (0, 0, 255)
    
    # Draw boxes
    boxes = [
        ((100, 100), (200, 150), "Input"),
        ((350, 100), (450, 150), "Process"),
        ((600, 100), (700, 150), "Output"),
    ]
    
    for (x1, y1), (x2, y2), label in boxes:
        cv2.rectangle(img, (x1, y1), (x2, y2), RED, 2)
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = (x1 + x2 - text_size[0]) // 2
        text_y = (y1 + y2 + text_size[1]) // 2
        cv2.putText(img, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    # Draw connections
    cv2.arrowedLine(img, (200, 125), (350, 125), BLACK, 2)
    cv2.arrowedLine(img, (450, 125), (600, 125), BLACK, 2)
    
    return img


def create_diagram_with_data():
    """Create a diagram with database symbols"""
    img = np.ones((600, 900, 3), dtype=np.uint8) * 255
    
    BLACK = (0, 0, 0)
    PURPLE = (128, 0, 128)
    
    # Title
    cv2.putText(img, "System Architecture", (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, BLACK, 2)
    
    # Draw components
    # API
    cv2.rectangle(img, (100, 80), (250, 150), PURPLE, 2)
    cv2.putText(img, "API Server", (130, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1)
    
    # Database
    cv2.rectangle(img, (400, 80), (500, 150), PURPLE, 2)
    cv2.putText(img, "Database", (420, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1)
    
    # Queue
    cv2.rectangle(img, (700, 80), (800, 150), PURPLE, 2)
    cv2.putText(img, "Queue", (720, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1)
    
    # Workers
    worker_y = 250
    for i, label in enumerate(["Worker 1", "Worker 2", "Worker 3"]):
        x = 150 + i * 300
        cv2.rectangle(img, (x, worker_y), (x + 150, worker_y + 70), PURPLE, 2)
        cv2.putText(img, label, (x + 20, worker_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1)
    
    # Draw connections
    cv2.arrowedLine(img, (250, 115), (400, 115), BLACK, 2)
    cv2.arrowedLine(img, (500, 115), (700, 115), BLACK, 2)
    cv2.arrowedLine(img, (750, 150), (200, 250), BLACK, 2)
    cv2.arrowedLine(img, (750, 150), (450, 250), BLACK, 2)
    cv2.arrowedLine(img, (750, 150), (700, 250), BLACK, 2)
    
    return img


def main():
    """Generate all sample diagrams"""
    samples_dir = Path("D:\\intelligent-node-detection\\backend\\data\\samples")
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save samples
    samples = [
        ("flowchart.png", create_flowchart_sample()),
        ("simple_boxes.png", create_simple_boxes_sample()),
        ("system_diagram.png", create_diagram_with_data()),
    ]
    
    for filename, img in samples:
        filepath = samples_dir / filename
        cv2.imwrite(str(filepath), img)
        print(f"✓ Created {filename}")
    
    print(f"\nSample diagrams saved to: {samples_dir}")


if __name__ == "__main__":
    main()
