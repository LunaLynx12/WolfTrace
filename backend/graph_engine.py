"""
Graph Engine - Handles graph operations and storage
Supports both Neo4j and in-memory graph storage
"""
import os
import networkx as nx
from typing import List, Dict, Any, Optional
import json

class GraphEngine:
    def __init__(self, use_neo4j: bool = False):
        """
        Initialize graph engine
        
        Args:
            use_neo4j: If True, use Neo4j database. Otherwise use in-memory NetworkX
        """
        self.use_neo4j = use_neo4j
        if use_neo4j:
            self._init_neo4j()
        else:
            self.graph = nx.MultiDiGraph()  # Directed multigraph for relationships
    
    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        try:
            from neo4j import GraphDatabase
            uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            user = os.getenv('NEO4J_USER', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', 'password')
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            print(f"Neo4j not available, using in-memory: {e}")
            self.use_neo4j = False
            self.graph = nx.MultiDiGraph()
    
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
        
        if self.use_neo4j:
            self._add_node_neo4j(node_id, node_type, properties)
        else:
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
        
        if self.use_neo4j:
            self._add_edge_neo4j(source, target, edge_type, properties)
        else:
            # For NetworkX MultiDiGraph, use edge_type as key for multi-edges
            self.graph.add_edge(source, target, key=edge_type, **properties)
    
    def get_nodes(self, node_type: Optional[str] = None) -> List[Dict]:
        """Get all nodes, optionally filtered by type"""
        if self.use_neo4j:
            return self._get_nodes_neo4j(node_type)
        else:
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
        if self.use_neo4j:
            return self._get_edges_neo4j(edge_type)
        else:
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
        if self.use_neo4j:
            return self._find_paths_neo4j(source, target, max_depth)
        else:
            try:
                paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_depth))
                return [list(path) for path in paths]
            except nx.NetworkXNoPath:
                return []
    
    def clear(self):
        """Clear all graph data"""
        if self.use_neo4j:
            self._clear_neo4j()
        else:
            self.graph.clear()
    
    # Neo4j methods
    def _add_node_neo4j(self, node_id: str, node_type: str, properties: Dict):
        with self.driver.session() as session:
            session.run(
                f"MERGE (n:{node_type} {{id: $id}}) SET n += $props",
                id=node_id,
                props=properties
            )
    
    def _add_edge_neo4j(self, source: str, target: str, edge_type: str, properties: Dict):
        with self.driver.session() as session:
            session.run(
                f"MATCH (a), (b) WHERE a.id = $source AND b.id = $target "
                f"CREATE (a)-[r:{edge_type}]->(b) SET r += $props",
                source=source,
                target=target,
                props=properties
            )
    
    def _get_nodes_neo4j(self, node_type: Optional[str]) -> List[Dict]:
        with self.driver.session() as session:
            if node_type:
                result = session.run(f"MATCH (n:{node_type}) RETURN n")
            else:
                result = session.run("MATCH (n) RETURN n")
            return [dict(record['n']) for record in result]
    
    def _get_edges_neo4j(self, edge_type: Optional[str]) -> List[Dict]:
        with self.driver.session() as session:
            if edge_type:
                result = session.run(
                    f"MATCH (a)-[r:{edge_type}]->(b) RETURN a.id as source, b.id as target, r"
                )
            else:
                result = session.run("MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, r")
            return [
                {
                    'source': record['source'],
                    'target': record['target'],
                    **dict(record['r'])
                }
                for record in result
            ]
    
    def _find_paths_neo4j(self, source: str, target: str, max_depth: int) -> List[List[str]]:
        with self.driver.session() as session:
            result = session.run(
                f"MATCH path = shortestPath((a)-[*1..{max_depth}]->(b)) "
                "WHERE a.id = $source AND b.id = $target "
                "RETURN [node in nodes(path) | node.id] as path",
                source=source,
                target=target
            )
            return [record['path'] for record in result]
    
    def _clear_neo4j(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

