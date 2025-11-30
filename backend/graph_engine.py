"""
Graph Engine - Handles graph operations and storage
Uses in-memory NetworkX graph storage
"""
import networkx as nx
from typing import List, Dict, Any, Optional
import json

class GraphEngine:
    def __init__(self):
        """
        Initialize graph engine with in-memory NetworkX graph
        """
        self.graph = nx.MultiDiGraph()  # Directed multigraph for relationships
    
    def add_node(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None):
        """Add a node to the graph, merging properties if node already exists
        
        Args:
            node_id: Node identifier
            node_type: Node type (optional, can be in properties)
            properties: Node properties dict (optional)
        """
        # Handle case where node_type is passed as a dict (backward compatibility)
        if isinstance(node_type, dict):
            properties = node_type
            node_type = properties.get('type', None)
        elif properties is None:
            properties = {}
        
        properties['id'] = node_id
        if node_type:
            properties['type'] = node_type
        
        # Check if node already exists and merge properties
        if self.graph.has_node(node_id):
            existing_data = self.graph.nodes[node_id]
            # Merge properties - lists are concatenated, dicts are merged, scalars are updated
            merged_properties = dict(existing_data)
            for key, value in properties.items():
                if key in merged_properties:
                    # Merge lists
                    if isinstance(merged_properties[key], list) and isinstance(value, list):
                        merged_properties[key] = merged_properties[key] + value
                    # Merge dicts
                    elif isinstance(merged_properties[key], dict) and isinstance(value, dict):
                        merged_properties[key] = {**merged_properties[key], **value}
                    # Update scalar
                    else:
                        merged_properties[key] = value
                else:
                    merged_properties[key] = value
            self.graph.add_node(node_id, **merged_properties)
        else:
            self.graph.add_node(node_id, **properties)
    
    def add_edge(self, source: str, target: str, edge_type: str = None, properties: Dict[str, Any] = None):
        """Add an edge to the graph
        
        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Edge type (optional, can be in properties)
            properties: Edge properties dict (optional)
        """
        if properties is None:
            properties = {}
        
        # Handle case where edge_type is passed as a dict (backward compatibility)
        if isinstance(edge_type, dict):
            properties = edge_type
            edge_type = properties.get('type', 'RELATED_TO')
        elif edge_type is None:
            edge_type = properties.get('type', 'RELATED_TO')
        
        properties['type'] = edge_type
        
        # For NetworkX MultiDiGraph, use edge_type as key for multi-edges
        self.graph.add_edge(source, target, key=edge_type, **properties)
    
    def get_nodes(self, node_type: Optional[str] = None) -> List[Dict]:
        """Get all nodes, optionally filtered by type"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            if node_type is None or data.get('type') == node_type:
                nodes.append({
                    'id': node_id,
                    **data
                })
        return nodes
    
    def get_edges(self, edge_type: Optional[str] = None) -> List[Dict]:
        """Get all edges, optionally filtered by type"""
        edges = []
        for source, target, key, data in self.graph.edges(keys=True, data=True):
            if edge_type is None or data.get('type') == edge_type:
                edges.append({
                    'source': source,
                    'target': target,
                    'type': key,
                    **data
                })
        return edges
    
    def get_full_graph(self) -> Dict:
        """Get complete graph data"""
        return {
            'nodes': self.get_nodes(),
            'edges': self.get_edges()
        }
    
    def find_paths(self, source: str, target: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths between source and target"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_depth))
            return [list(path) for path in paths]
        except nx.NetworkXNoPath:
            return []
    
    def clear(self):
        """Clear all graph data"""
        self.graph.clear()

