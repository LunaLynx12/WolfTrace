"""
Graph Analytics - Provides graph metrics and analysis
"""
import networkx as nx
from typing import Dict, List, Any
from collections import Counter

class GraphAnalytics:
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        if self.graph_engine.use_neo4j:
            return self._get_neo4j_stats()
        
        graph = self.graph_engine.graph
        if len(graph.nodes) == 0:
            return {"error": "Graph is empty"}
        
        # Basic stats
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        
        # Node type distribution
        node_types = [data.get('type', 'Unknown') for _, data in graph.nodes(data=True)]
        type_distribution = dict(Counter(node_types))
        
        # Edge type distribution
        edge_types = [data.get('type', 'Unknown') for _, _, _, data in graph.edges(keys=True, data=True)]
        edge_type_distribution = dict(Counter(edge_types))
        
        # Graph metrics
        try:
            # Convert to undirected for some metrics
            undirected = graph.to_undirected()
            
            # Centrality measures (sample top nodes for performance)
            if num_nodes > 0:
                degree_centrality = nx.degree_centrality(graph)
                top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Betweenness centrality (only for smaller graphs)
                if num_nodes < 1000:
                    betweenness = nx.betweenness_centrality(graph)
                    top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
                else:
                    top_betweenness = []
                
                # Connected components
                if num_nodes > 0:
                    components = list(nx.connected_components(undirected))
                    largest_component_size = max(len(c) for c in components) if components else 0
                else:
                    components = []
                    largest_component_size = 0
            else:
                top_degree = []
                top_betweenness = []
                components = []
                largest_component_size = 0
            
            # Average degree
            avg_degree = (2 * num_edges / num_nodes) if num_nodes > 0 else 0
            
            return {
                "basic": {
                    "nodes": num_nodes,
                    "edges": num_edges,
                    "average_degree": round(avg_degree, 2),
                    "connected_components": len(components),
                    "largest_component_size": largest_component_size
                },
                "node_types": type_distribution,
                "edge_types": edge_type_distribution,
                "top_nodes_by_degree": [{"id": node, "centrality": round(cent, 4)} 
                                        for node, cent in top_degree],
                "top_nodes_by_betweenness": [{"id": node, "centrality": round(cent, 4)} 
                                             for node, cent in top_betweenness] if top_betweenness else [],
                "is_connected": len(components) == 1,
                "is_dag": nx.is_directed_acyclic_graph(graph)
            }
        except Exception as e:
            return {
                "basic": {
                    "nodes": num_nodes,
                    "edges": num_edges
                },
                "node_types": type_distribution,
                "edge_types": edge_type_distribution,
                "error": str(e)
            }
    
    def find_communities(self, max_communities: int = 10) -> List[Dict[str, Any]]:
        """Find communities in the graph using Louvain algorithm"""
        if self.graph_engine.use_neo4j:
            return []
        
        try:
            import networkx.algorithms.community as nx_comm
            
            graph = self.graph_engine.graph
            if len(graph.nodes) == 0:
                return []
            
            # Convert to undirected
            undirected = graph.to_undirected()
            
            # Use greedy modularity communities
            communities = nx_comm.greedy_modularity_communities(undirected)
            
            result = []
            for i, community in enumerate(list(communities)[:max_communities]):
                community_nodes = list(community)
                result.append({
                    "id": i,
                    "size": len(community_nodes),
                    "nodes": community_nodes[:20]  # Limit to first 20 nodes
                })
            
            return result
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_node_neighbors(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get neighbors of a node up to specified depth"""
        if self.graph_engine.use_neo4j:
            return {}
        
        graph = self.graph_engine.graph
        if node_id not in graph:
            return {"error": "Node not found"}
        
        neighbors = {
            "node": node_id,
            "depth_1": list(graph.successors(node_id)) + list(graph.predecessors(node_id)),
            "total_neighbors": 0
        }
        
        if depth > 1:
            # Get 2-hop neighbors
            depth_2 = set()
            for neighbor in neighbors["depth_1"]:
                depth_2.update(graph.successors(neighbor))
                depth_2.update(graph.predecessors(neighbor))
            depth_2.discard(node_id)
            neighbors["depth_2"] = list(depth_2)
        
        neighbors["total_neighbors"] = len(set(neighbors["depth_1"]))
        return neighbors
    
    def _get_neo4j_stats(self) -> Dict[str, Any]:
        """Get statistics from Neo4j"""
        # Placeholder for Neo4j implementation
        return {"error": "Neo4j analytics not yet implemented"}

