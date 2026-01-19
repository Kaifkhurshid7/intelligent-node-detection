"""Graph building module using NetworkX"""
import json
from typing import List, Dict, Any
import networkx as nx


class GraphBuilder:
    """Builds NetworkX graphs from diagram elements"""
    
    def __init__(self):
        """Initialize graph builder"""
        self.graph = None
        self.raw_graph = None # Added for raw graph
        self.nodes_data = {} # Added for node data storage
    
    def build_from_elements(self, elements: List[Dict], edges: List[Dict], raw_nodes_count: int, raw_edges_count: int) -> Dict[str, Any]:
        """
        Build a graph from classified diagram elements and enforce logical sanity rules.
        """
        # Reset current state
        self.graph = nx.DiGraph() # This will be the logical graph
        self.raw_graph = nx.DiGraph() # This will store all raw elements
        self.nodes_data = {} # Store all node data for easy lookup

        nodes = []
        edge_list = []
        
        # Add nodes to raw_graph and nodes_data
        for element in elements:
            node_id = element.get('id')
            if node_id:
                self.nodes_data[node_id] = element
                self.raw_graph.add_node(node_id, **element) # Add all attributes to raw_graph node

                # Add nodes to the logical graph (self.graph)
                self.graph.add_node(
                    node_id,
                    type=element.get('semantic_class', 'unknown'),
                    labels=element.get('labels', []),
                    bbox=element.get('bbox'),
                    shape_type=element.get('type'),
                    confidence=element.get('confidence', 0.0),
                )
                
                label_text = ' '.join(element.get('labels', []))
                nodes.append({
                    'id': node_id,
                    'label': label_text,
                    'type': element.get('semantic_class', 'unknown'),
                    'shape': element.get('type'),
                    'bbox': element.get('bbox'),
                    'confidence': element.get('confidence', 0.0),
                })
        
        # Add edges to raw_graph and logical graph
        if edges:
            for edge in edges:
                source = edge.get('source')
                target = edge.get('target')
                
                if source and target:
                    self.raw_graph.add_edge(source, target, **edge) # Add all attributes to raw_graph edge

                    if source in self.graph and target in self.graph: # Only add to logical graph if nodes exist
                        self.graph.add_edge(
                            source,
                            target,
                            label=edge.get('label', ''),
                            direction=edge.get('direction', '->'),
                            confidence=edge.get('confidence', 0.5),
                        )
                        
                        edge_list.append({
                            'source': source,
                            'target': target,
                            'label': edge.get('label', ''),
                            'direction': edge.get('direction', '->'),
                        })

        # --- TASK 8: Enforce Graph Sanity Rules ---
        sanity_violations = self.check_sanity_rules()

        # --- TASK 11: Logic Narrative Generation ---
        narrative = self._generate_narrative(elements, edges)

        # --- TASK 10: Add Confidence Metrics ---
        node_reduction = ((raw_nodes_count - len(nodes)) / raw_nodes_count * 100) if raw_nodes_count > 0 else 0

        logical_graph = {
            'nodes': nodes,
            'edges': edge_list,
            'metadata': {
                'node_count': len(nodes),
                'edge_count': len(edge_list),
                'node_reduction_pct': round(node_reduction, 1),
                'sanity_violations': sanity_violations,
                'start_nodes': self.find_start_nodes(),
                'end_nodes': self.find_end_nodes(),
            },
            'narrative': narrative
        }

        # --- TASK 9: Maintain Raw vs Logical Graphs ---
        return {
            'raw_graph': {
                'nodes': raw_nodes_count,
                'edges': raw_edges_count
            },
            'logical_graph': logical_graph,
            'graph': logical_graph # For backward compatibility
        }

    def check_sanity_rules(self) -> List[str]:
        """Check flowchart logic rules and return list of violations"""
        violations = []
        if self.graph is None:
            return violations

        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_type = node_data.get('type')
            in_degree = self.graph.in_degree(node_id)
            out_degree = self.graph.out_degree(node_id)

            # Rule: Start node has no incoming edges
            if node_type == 'start' and in_degree > 0:
                violations.append(f"Start node {node_id} has incoming edges")

            # Rule: End node has no outgoing edges
            if node_type == 'end' and out_degree > 0:
                violations.append(f"End node {node_id} has outgoing edges")

            # Rule: Decision nodes have >=2 outgoing edges
            if node_type == 'decision' and out_degree < 2:
                violations.append(f"Decision node {node_id} has only {out_degree} outgoing edge(s)")

        return violations
    
    def add_edge(self, source_id: str, target_id: str, label: str = "", arrow_type: str = "->"):
        """
        Add an edge between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            label: Edge label/text
            arrow_type: Type of arrow (->. <-, <->, etc.)
        """
        if self.graph and source_id in self.graph and target_id in self.graph:
            self.graph.add_edge(
                source_id,
                target_id,
                label=label,
                arrow_type=arrow_type,
            )
    
    def to_json(self, filepath: str):
        """
        Save graph to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        if self.graph is None:
            raise ValueError("No graph to export")
        
        data = {
            'nodes': [
                {
                    'id': node,
                    'label': self.graph.nodes[node].get('type', 'unknown'),
                    'data': dict(self.graph.nodes[node])
                }
                for node in self.graph.nodes()
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    'data': dict(data)
                }
                for source, target, data in self.graph.edges(data=True)
            ],
            'metadata': {
                'node_count': self.graph.number_of_nodes(),
                'edge_count': self.graph.number_of_edges(),
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def to_graphml(self, filepath: str):
        """
        Save graph to GraphML format.
        
        Args:
            filepath: Path to save GraphML file
        """
        if self.graph is None:
            raise ValueError("No graph to export")
        
        nx.write_graphml(self.graph, filepath)
    
    def get_adjacency_list(self) -> Dict[str, List[str]]:
        """
        Get adjacency list representation.
        
        Returns:
            Dictionary mapping node IDs to lists of connected node IDs
        """
        if self.graph is None:
            return {}
        
        return {node: list(self.graph.successors(node)) for node in self.graph.nodes()}
    
    def find_start_nodes(self) -> List[str]:
        """
        Find nodes with no incoming edges (start nodes).
        
        Returns:
            List of start node IDs
        """
        if self.graph is None:
            return []
        
        return [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]
    
    def find_end_nodes(self) -> List[str]:
        """
        Find nodes with no outgoing edges (end nodes).
        
        Returns:
            List of end node IDs
        """
        if self.graph is None:
            return []
        
        return [node for node in self.graph.nodes() if self.graph.out_degree(node) == 0]
    
    def get_graph_paths(self) -> List[List[str]]:
        """
        Get all paths in the graph.
        
        Returns:
            List of paths (each path is a list of node IDs)
        """
        if self.graph is None:
            return []
        
        paths = []
        start_nodes = self.find_start_nodes()
        
        for start in start_nodes:
            for end in self.find_end_nodes():
                try:
                    for path in nx.all_simple_paths(self.graph, start, end):
                        paths.append(path)
                except nx.NetworkXNoPath:
                    pass
        
        return paths

    def _generate_narrative(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Translates the directed graph into a human-readable chronological narrative.
        """
        narrative = []
        start_nodes = self.find_start_nodes()
        
        if not start_nodes:
            # If no node has in-degree 0 in the logical graph, use raw graph or fallback
            start_nodes = [node_id for node_id, d in self.graph.in_degree() if d == 0]
            
        if not start_nodes and nodes:
            start_nodes = [nodes[0]['id']] # Final fallback

        # BFS for narrative flow
        visited = set()
        queue = []
        for sn in start_nodes:
            queue.append(sn)
            visited.add(sn)

        step_idx = 1
        
        while queue:
            node_id = queue.pop(0)
            node_data = self.nodes_data.get(node_id)
            if not node_data: continue
            
            label = " ".join(node_data.get('labels', [])) or f"Step {node_id}"
            sem_class = node_data.get('semantic_class', 'process').lower()
            
            sentence = f"Step {step_idx}: "
            if sem_class == 'start':
                sentence += f"Start the process: {label}"
            elif sem_class == 'end':
                sentence += f"End of process: {label}"
            elif sem_class == 'decision':
                sentence += f"Decision point: {label}"
            else:
                sentence += f"Perform action: {label}"
            
            narrative.append(sentence)
            step_idx += 1
            
            # Handle outgoing edges
            out_edges = self.raw_graph.out_edges(node_id, data=True)
            for _, target, data in out_edges:
                edge_label = data.get('label', '')
                if sem_class == 'decision' and edge_label:
                    narrative.append(f"   ↳ If {edge_label}, proceed to {target}")
                
                if target not in visited:
                    visited.add(target)
                    queue.append(target)
                    
        return narrative
