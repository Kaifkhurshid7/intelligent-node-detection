import requests
import json

try:
    with open('backend/data/samples/flowchart.png', 'rb') as f:
        resp = requests.post('http://localhost:8000/analyze', files={'file': f})
        
    if resp.status_code == 200:
        res_json = resp.json()
        if res_json['success']:
            data = res_json['data']
            print(f"Raw: {data['raw_graph']}")
            print(f"Logical: {data['logical_graph']}")
            print(f"Total Text Found: {len(data['text'])}")
            print(f"Edges: {len(data['edges'])}")
            for node in data['nodes'][:10]:
                print(f"Node {node['id']} ({node['semantic_class']}): Area={node['area']}")
        else:
            print(f"Error: {res_json['message']}")
    else:
        print(f"HTTP Error: {resp.status_code}")
except Exception as e:
    print(f"Exception: {e}")
