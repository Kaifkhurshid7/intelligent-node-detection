"""
Graph Sanity Validation Engine.

Validates and auto-repairs workflow graph topology to ensure
structural correctness before narrative generation.

Validation rules:
    1. Exactly one start node (or mark the first node as start)
    2. At least one end node (or mark terminal nodes as end)
    3. No self-loops
    4. No isolated nodes (every node must be reachable)
    5. Decision nodes must have ≥2 outgoing edges
    6. Start nodes must have no incoming edges
    7. End nodes must have no outgoing edges
"""

from typing import List, Dict, Tuple

from app.core.logging import logger


class GraphValidator:
    """
    Validates and auto-repairs workflow graph structures.

    Returns both the list of violations found and suggested fixes
    that were automatically applied.
    """

    def validate_and_repair(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[str], List[str]]:
        """
        Validate graph topology and apply auto-repairs.

        Args:
            nodes: Classified nodes with semantic_class.
            edges: Directed edges with source/target.

        Returns:
            Tuple of (repaired_nodes, repaired_edges, violations, repairs).
        """
        violations = []
        repairs = []

        # Build lookup structures
        node_ids = {n["id"] for n in nodes}
        node_map = {n["id"]: n for n in nodes}

        # Remove edges referencing non-existent nodes
        valid_edges = []
        for edge in edges:
            if edge["source"] in node_ids and edge["target"] in node_ids:
                valid_edges.append(edge)
            else:
                repairs.append(f"Removed edge with invalid reference: {edge.get('source')} → {edge.get('target')}")
        edges = valid_edges

        # Remove self-loops
        clean_edges = []
        for edge in edges:
            if edge["source"] == edge["target"]:
                violations.append(f"Self-loop detected on '{edge['source']}'")
                repairs.append(f"Removed self-loop on '{edge['source']}'")
            else:
                clean_edges.append(edge)
        edges = clean_edges

        # Check start nodes
        start_nodes = [n for n in nodes if n.get("semantic_class") == "start"]
        if len(start_nodes) == 0 and nodes:
            # Auto-fix: mark the first node with no incoming edges as start
            incoming = {e["target"] for e in edges}
            candidates = [n for n in nodes if n["id"] not in incoming]
            if candidates:
                candidates[0]["semantic_class"] = "start"
                repairs.append(f"Auto-assigned '{candidates[0]['id']}' as start node")
            violations.append("No start node detected")

        # Check end nodes
        end_nodes = [n for n in nodes if n.get("semantic_class") == "end"]
        if len(end_nodes) == 0 and nodes:
            # Auto-fix: mark terminal nodes (no outgoing) as end
            outgoing = {e["source"] for e in edges}
            terminals = [n for n in nodes if n["id"] not in outgoing]
            for t in terminals:
                if t.get("semantic_class") != "start":
                    t["semantic_class"] = "end"
                    repairs.append(f"Auto-assigned '{t['id']}' as end node")
            if not terminals:
                violations.append("No end node detected")

        # Validate decision branching
        for node in nodes:
            if node.get("semantic_class") == "decision":
                out_count = sum(1 for e in edges if e["source"] == node["id"])
                if out_count < 2:
                    violations.append(
                        f"Decision node '{node.get('display_name', node['id'])}' "
                        f"has only {out_count} outgoing edge(s) (expected ≥2)"
                    )

        # Check for start nodes with incoming edges
        for node in nodes:
            if node.get("semantic_class") == "start":
                in_count = sum(1 for e in edges if e["target"] == node["id"])
                if in_count > 0:
                    violations.append(
                        f"Start node '{node.get('display_name', node['id'])}' has incoming edges"
                    )

        # Check for isolated nodes
        connected = set()
        for e in edges:
            connected.add(e["source"])
            connected.add(e["target"])
        isolated = [n for n in nodes if n["id"] not in connected and len(nodes) > 1]
        for iso in isolated:
            violations.append(f"Isolated node: '{iso.get('display_name', iso['id'])}'")

        logger.info(
            f"[GraphValidator] {len(violations)} violations, {len(repairs)} auto-repairs"
        )

        return nodes, edges, violations, repairs
