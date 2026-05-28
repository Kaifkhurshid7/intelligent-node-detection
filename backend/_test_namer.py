import sys
sys.path.insert(0, ".")
from app.services.pipeline import AnalysisPipeline

p = AnalysisPipeline()
result = p.analyze("data/samples/flowchart.png")
lg = result["logical_graph"]

print("\n--- Nodes (Semantic IDs) ---\n")
for node in lg["nodes"]:
    print(f"  {node['sequence']:2d}. {node['id']:<45} | {node['display_name']:<25} | {node['type']}")

print(f"\n--- Edges ---\n")
for edge in lg["edges"]:
    cond = f" [{edge['condition']}]" if edge.get("condition") else ""
    print(f"  {edge['source']} → {edge['target']}{cond}")

print(f"\n--- Narrative ---\n")
for step in lg["narrative"]:
    print(f"  {step}")

print(f"\n--- Timings ---")
for k, v in result["timings"].items():
    print(f"  {k}: {v}ms")

print("\nPASS")
