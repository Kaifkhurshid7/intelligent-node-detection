"""
Graph construction and analysis service.

    - Sanity rule validation (flowchart logic correctness)
    - Workflow narrative generation (BFS-based, using display names)
    - Accuracy metrics computation
"""

from typing import List, Dict, Any
from collections import deque

import networkx as nx

from app.core.logging import logger


class GraphBuilder:
    """
    Constructs and analyzes directed graphs from diagram elements.

    Uses semantic node IDs and display names for all output, ensuring
    the graph is human-readable in API responses, exports, and narratives.
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
            elements: Named, classified logical nodes (with 'id', 'display_name', 'sequence').
            edges: Detected logical edges (source/target use OLD IDs from edge detector).
            raw_nodes_count: Total raw contours before filtering.
            raw_edges_count: Total raw line segments before filtering.

        Returns:
            Complete graph data with semantic nodes, edges, metadata, and narrative.
        """
        self._graph = nx.DiGraph()
        self._nodes_data = {}

        # Build an ID mapping: old logical_node_X → new semantic ID
        # The edge detector uses the old IDs, so we need to remap
        old_to_new = {}
        for element in elements:
            old_id = element.get("_original_id") or element.get("id")
            new_id = element.get("id", old_id)
            old_to_new[old_id] = new_id
            # Also map new to new (in case edges already use new IDs)
            old_to_new[new_id] = new_id

        # Populate graph nodes with semantic IDs
        nodes_output = []
        for element in elements:
            node_id = element.get("id")
            if not node_id:
                continue

            self._nodes_data[node_id] = element
            self._graph.add_node(
                node_id,
                type=element.get("semantic_class", "unknown"),
                display_name=element.get("display_name", node_id),
                labels=element.get("labels", []),
                bbox=element.get("bbox"),
                shape_type=element.get("type"),
                confidence=element.get("confidence", 0.0),
                sequence=element.get("sequence", 0),
            )

            nodes_output.append({
                "id": node_id,
                "display_name": element.get("display_name", node_id),
                "label": " ".join(element.get("labels", [])),
                "type": element.get("semantic_class", "unknown"),
                "shape": element.get("type"),
                "bbox": element.get("bbox"),
                "center": element.get("center"),
                "confidence": element.get("confidence", 0.0),
                "sequence": element.get("sequence", 0),
                "labels": element.get("labels", []),
            })

        # Populate graph edges, remapping old IDs to semantic IDs
        edges_output = []
        for edge in edges:
            raw_source = edge.get("source", "")
            raw_target = edge.get("target", "")

            source = old_to_new.get(raw_source, raw_source)
            target = old_to_new.get(raw_target, raw_target)

            if source and target and source in self._graph and target in self._graph:
                label = edge.get("label", "")
                self._graph.add_edge(
                    source, target,
                    label=label,
                    condition=label.upper() if label else "",
                    direction=edge.get("direction", "->"),
                )
                edges_output.append({
                    "source": source,
                    "target": target,
                    "label": label,
                    "condition": label.upper() if label else "",
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
            "graph": logical_graph,
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
            display = node_data.get("display_name", node_id)
            in_degree = self._graph.in_degree(node_id)
            out_degree = self._graph.out_degree(node_id)

            if node_type == "start" and in_degree > 0:
                violations.append(f"Start node '{display}' has incoming edges")
            if node_type == "end" and out_degree > 0:
                violations.append(f"End node '{display}' has outgoing edges")
            if node_type == "decision" and out_degree < 2:
                violations.append(
                    f"Decision node '{display}' has only {out_degree} outgoing edge(s)"
                )

        return violations

    def _generate_narrative(self) -> List[str]:
        """
        Generate a human-readable workflow narrative via BFS traversal.

        Uses display_name for readable output and semantic class for
        contextual step descriptions. Produces natural-language steps
        that describe the workflow logic.
        """
        if not self._graph or self._graph.number_of_nodes() == 0:
            return []

        start_nodes = self._find_start_nodes()
        if not start_nodes:
            start_nodes = [list(self._graph.nodes())[0]]

        visited = set()
        queue = deque()
        for node_id in start_nodes:
            queue.append(node_id)
            visited.add(node_id)

        narrative = []
        step_idx = 1

        while queue:
            node_id = queue.popleft()
            node_data = self._nodes_data.get(node_id)
            if not node_data:
                continue

            display_name = node_data.get("display_name", node_id)
            sem_class = node_data.get("semantic_class", "process").lower()

            # Generate contextual step description using display names
            step = self._format_narrative_step(step_idx, sem_class, display_name)
            narrative.append(step)
            step_idx += 1

            # Add branching annotations for decision nodes
            for _, target, data in self._graph.out_edges(node_id, data=True):
                edge_label = data.get("label", "")
                if sem_class == "decision" and edge_label:
                    target_data = self._nodes_data.get(target, {})
                    target_display = target_data.get("display_name", target)
                    narrative.append(
                        f"   ↳ If {edge_label.upper()}, proceed to: {target_display}"
                    )

                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        return narrative

    def _format_narrative_step(
        self, step_num: int, sem_class: str, display_name: str
    ) -> str:
        """
        Format a single narrative step with contextual language.

        Uses the semantic class to choose appropriate action verbs
        that make the narrative read naturally.
        """
        templates = {
            "start": f"Step {step_num}: Begin the workflow — {display_name}",
            "end": f"Step {step_num}: End of workflow — {display_name}",
            "decision": f"Step {step_num}: Check condition — {display_name}",
            "input": f"Step {step_num}: Read input — {display_name}",
            "output": f"Step {step_num}: Produce output — {display_name}",
            "data": f"Step {step_num}: Access data — {display_name}",
            "database": f"Step {step_num}: Database operation — {display_name}",
            "process": f"Step {step_num}: Execute — {display_name}",
        }
        return templates.get(sem_class, f"Step {step_num}: {display_name}")

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
