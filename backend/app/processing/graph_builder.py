"""
Graph construction and analysis service.

Builds a NetworkX directed graph from classified nodes and edges,
then performs structural analysis including:
    - Sanity rule validation (flowchart logic correctness)
    - Workflow narrative generation (BFS-based step descriptions)
    - Accuracy metrics computation
"""

from typing import List, Dict, Any

import networkx as nx

from app.core.logging import logger


class GraphBuilder:
    """
    Constructs and analyzes directed graphs from diagram elements.

    Maintains both a raw detection graph (all elements) and a logical
    graph (validated, classified elements) for comparison metrics.
    """

    def __init__(self):
        self._graph: nx.DiGraph | None = None
        self._nodes_data: Dict[str, Dict] = {}

    def build(
        self,
        elements: List[Dict],
        edges: List[Dict],
        raw_nodes_count: int,
        raw_edges_count: int,
    ) -> Dict[str, Any]:
        """
        Build the complete graph structure from pipeline outputs.

        Args:
            elements: Classified logical nodes.
            edges: Detected logical edges.
            raw_nodes_count: Total raw contours before filtering.
            raw_edges_count: Total raw line segments before filtering.

        Returns:
            Complete graph data with nodes, edges, metadata, and narrative.
        """
        self._graph = nx.DiGraph()
        self._nodes_data = {}

        # Populate graph nodes
        nodes_output = []
        for element in elements:
            node_id = element.get("id")
            if not node_id:
                continue

            self._nodes_data[node_id] = element
            self._graph.add_node(
                node_id,
                type=element.get("semantic_class", "unknown"),
                labels=element.get("labels", []),
                bbox=element.get("bbox"),
                shape_type=element.get("type"),
                confidence=element.get("confidence", 0.0),
            )

            nodes_output.append({
                "id": node_id,
                "label": " ".join(element.get("labels", [])),
                "type": element.get("semantic_class", "unknown"),
                "shape": element.get("type"),
                "bbox": element.get("bbox"),
                "confidence": element.get("confidence", 0.0),
            })

        # Populate graph edges
        edges_output = []
        for edge in edges:
            source, target = edge.get("source"), edge.get("target")
            if source and target and source in self._graph and target in self._graph:
                self._graph.add_edge(
                    source, target,
                    label=edge.get("label", ""),
                    direction=edge.get("direction", "->"),
                )
                edges_output.append({
                    "source": source,
                    "target": target,
                    "label": edge.get("label", ""),
                    "direction": edge.get("direction", "->"),
                })

        # Analysis
        violations = self._check_sanity_rules()
        narrative = self._generate_narrative()
        node_reduction = (
            ((raw_nodes_count - len(nodes_output)) / raw_nodes_count * 100)
            if raw_nodes_count > 0
            else 0
        )

        logical_graph = {
            "nodes": nodes_output,
            "edges": edges_output,
            "metadata": {
                "node_count": len(nodes_output),
                "edge_count": len(edges_output),
                "node_reduction_pct": round(node_reduction, 1),
                "sanity_violations": violations,
                "start_nodes": self._find_start_nodes(),
                "end_nodes": self._find_end_nodes(),
            },
            "narrative": narrative,
        }

        logger.info(
            f"Graph built: {len(nodes_output)} nodes, {len(edges_output)} edges, "
            f"{len(violations)} violations"
        )

        return {
            "raw_graph": {"nodes": raw_nodes_count, "edges": raw_edges_count},
            "logical_graph": logical_graph,
            "graph": logical_graph,  # Backward compatibility
        }

    def _check_sanity_rules(self) -> List[str]:
        """
        Validate flowchart structural rules.

        Rules enforced:
            - Start nodes must have no incoming edges
            - End nodes must have no outgoing edges
            - Decision nodes must have ≥2 outgoing edges (branching)
        """
        violations = []
        if not self._graph:
            return violations

        for node_id in self._graph.nodes():
            node_data = self._graph.nodes[node_id]
            node_type = node_data.get("type")
            in_degree = self._graph.in_degree(node_id)
            out_degree = self._graph.out_degree(node_id)

            if node_type == "start" and in_degree > 0:
                violations.append(f"Start node '{node_id}' has incoming edges")
            if node_type == "end" and out_degree > 0:
                violations.append(f"End node '{node_id}' has outgoing edges")
            if node_type == "decision" and out_degree < 2:
                violations.append(
                    f"Decision node '{node_id}' has only {out_degree} outgoing edge(s)"
                )

        return violations

    def _generate_narrative(self) -> List[str]:
        """
        Generate a human-readable workflow narrative via BFS traversal.

        Starts from nodes with in-degree 0 (entry points) and traverses
        the graph in breadth-first order, producing step-by-step
        descriptions of the flowchart logic.
        """
        if not self._graph or self._graph.number_of_nodes() == 0:
            return []

        start_nodes = self._find_start_nodes()
        if not start_nodes:
            # Fallback: use first node if no clear entry point
            start_nodes = [list(self._graph.nodes())[0]]

        visited = set()
        queue = []
        for node_id in start_nodes:
            queue.append(node_id)
            visited.add(node_id)

        narrative = []
        step_idx = 1

        while queue:
            node_id = queue.pop(0)
            node_data = self._nodes_data.get(node_id)
            if not node_data:
                continue

            label = " ".join(node_data.get("labels", [])) or f"Step {node_id}"
            sem_class = node_data.get("semantic_class", "process").lower()

            # Generate contextual step description
            prefix = f"Step {step_idx}: "
            if sem_class == "start":
                narrative.append(f"{prefix}Start the process: {label}")
            elif sem_class == "end":
                narrative.append(f"{prefix}End of process: {label}")
            elif sem_class == "decision":
                narrative.append(f"{prefix}Decision point: {label}")
            else:
                narrative.append(f"{prefix}Perform action: {label}")

            step_idx += 1

            # Add branching annotations for decision nodes
            for _, target, data in self._graph.out_edges(node_id, data=True):
                edge_label = data.get("label", "")
                if sem_class == "decision" and edge_label:
                    narrative.append(f"   ↳ If {edge_label}, proceed to {target}")

                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        return narrative

    def _find_start_nodes(self) -> List[str]:
        """Find nodes with no incoming edges (graph entry points)."""
        if not self._graph:
            return []
        return [n for n in self._graph.nodes() if self._graph.in_degree(n) == 0]

    def _find_end_nodes(self) -> List[str]:
        """Find nodes with no outgoing edges (graph exit points)."""
        if not self._graph:
            return []
        return [n for n in self._graph.nodes() if self._graph.out_degree(n) == 0]
