"""
Bulk Operations - Perform operations on multiple nodes/edges
"""
from typing import Dict, List, Any

class BulkOperations:
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
    
    def bulk_delete_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple nodes and their associated edges"""
        deleted_count = 0
        edges_removed = 0
        
        for node_id in node_ids:
            if node_id in self.graph_engine.graph:
                # Count edges to be removed
                edges_removed += (
                    self.graph_engine.graph.out_degree(node_id) +
                    self.graph_engine.graph.in_degree(node_id)
                )
                self.graph_engine.graph.remove_node(node_id)
                deleted_count += 1
        
        return {
            'nodes_deleted': deleted_count,
            'edges_removed': edges_removed,
            'status': 'success'
        }
    
    def bulk_delete_edges(self, edge_specs: List[Dict]) -> Dict[str, Any]:
        """Delete multiple edges
        
        Args:
            edge_specs: List of dicts with 'source', 'target', and optionally 'type'
        """
        deleted_count = 0
        
        for edge_spec in edge_specs:
            source = edge_spec.get('source')
            target = edge_spec.get('target')
            edge_type = edge_spec.get('type')
            
            if source and target:
                if edge_type:
                    # Remove specific edge type
                    if self.graph_engine.graph.has_edge(source, target, edge_type):
                        self.graph_engine.graph.remove_edge(source, target, edge_type)
                        deleted_count += 1
                else:
                    # Remove all edges between source and target
                    if self.graph_engine.graph.has_edge(source, target):
                        edges_to_remove = list(self.graph_engine.graph.edges(source, target, keys=True))
                        for edge in edges_to_remove:
                            self.graph_engine.graph.remove_edge(*edge)
                        deleted_count += len(edges_to_remove)
        
        return {
            'edges_deleted': deleted_count,
            'status': 'success'
        }
    
    def bulk_update_nodes(self, updates: List[Dict]) -> Dict[str, Any]:
        """Update properties of multiple nodes
        
        Args:
            updates: List of dicts with 'id' and 'properties' to update
        """
        updated_count = 0
        
        for update in updates:
            node_id = update.get('id')
            properties = update.get('properties', {})
            
            if node_id and properties:
                if node_id in self.graph_engine.graph:
                    # Update node properties
                    for key, value in properties.items():
                        self.graph_engine.graph.nodes[node_id][key] = value
                    updated_count += 1
        
        return {
            'nodes_updated': updated_count,
            'status': 'success'
        }
    
    def bulk_tag_nodes(self, node_ids: List[str], tags: List[str], operation: str = 'add') -> Dict[str, Any]:
        """Add or remove tags from multiple nodes
        
        Args:
            node_ids: List of node IDs
            tags: List of tags to add/remove
            operation: 'add' or 'remove'
        """
        tagged_count = 0
        
        for node_id in node_ids:
            if node_id in self.graph_engine.graph:
                node = self.graph_engine.graph.nodes[node_id]
                current_tags = node.get('tags', [])
                
                if operation == 'add':
                    # Add tags (avoid duplicates)
                    new_tags = list(set(current_tags + tags))
                    node['tags'] = new_tags
                elif operation == 'remove':
                    # Remove tags
                    node['tags'] = [t for t in current_tags if t not in tags]
                
                tagged_count += 1
        
        return {
            'nodes_tagged': tagged_count,
            'status': 'success'
        }
    
    def bulk_export_nodes(self, node_ids: List[str]) -> List[Dict]:
        """Export data for multiple nodes"""
        nodes = []
        for node_id in node_ids:
            node_data = self.graph_engine.get_nodes()
            node = next((n for n in node_data if n['id'] == node_id), None)
            if node:
                nodes.append(node)
        return nodes

