import requests
import json
import sys
import os
from pathlib import Path

def evaluate_accuracy(image_path):
    url = "http://127.0.0.1:8000/analyze"
    
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found.")
        return

    print(f"--- Evaluating Accuracy for: {os.path.basename(image_path)} ---")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/png")}
            response = requests.post(url, files=files)
            
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(response.text)
            return

        result = response.json()
        if not result.get("success"):
            print(f"Error: {result.get('message')}")
            return

        data = result.get("data", {})
        logical_graph = data.get("logical_graph", {})
        metadata = logical_graph.get("metadata", {})
        raw_graph = data.get("raw_graph", {})

        print("\n[SUMMARY METRICS]")
        print(f"Noise Reduction: {metadata.get('node_reduction_pct')}%")
        print(f"Logical Nodes: {metadata.get('node_count')} (Reduced from {raw_graph.get('nodes')} raw contours)")
        print(f"Logical Edges: {metadata.get('edge_count')}")

        print("\n[LOGIC SANITY CHECK]")
        violations = metadata.get("sanity_violations", [])
        if not violations:
            print(" Perfect Logic! No sanity violations found.")
        else:
            print(f"Found {len(violations)} potential logic errors:")
            for v in violations:
                print(f"   - {v}")

        print("\n[NODE CLASSIFICATION]")
        for node in logical_graph.get("nodes", []):
            label = node.get("label") or "[No Text]"
            print(f"{node.get('id')} | Type: {node.get('type'):<10} | Shape: {node.get('shape'):<10} | Text: {label}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the backend server. Make sure uvicorn is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python evaluate.py <path_to_image>")
        # Try to find a sample if none provided
        sample = "backend/data/samples/flowchart.png"
        if os.path.exists(sample):
            print(f"No image provided, testing with default: {sample}\n")
            evaluate_accuracy(sample)
    else:
        evaluate_accuracy(sys.argv[1])
