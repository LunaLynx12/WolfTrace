"""
Bulk Operations - Perform operations on multiple nodes/edges
Supports batch creation, deletion, updates, and transaction rollback
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BulkOperations:
    def __init__(self, graph_engine, db_backend: Optional[object] = None):
        self.graph_engine = graph_engine
        self.db_backend = db_backend
        self._transaction_stack: List[Dict[str, Any]] = []  # For rollback support
    
    def bulk_delete_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple nodes and their associated edges"""
        deleted_count = 0
        edges_removed = 0
        
        for node_id in node_ids:
            if node_id in self.graph_engine.graph:
                result = self.graph_engine.remove_node(node_id)
                if result['deleted']:
                    deleted_count += 1
                    edges_removed += result['edges_removed']
        
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
                removed = self.graph_engine.remove_edge(source, target, edge_type)
                if removed:
                    deleted_count += 1
        
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
                    for key, value in properties.items():
                        self.graph_engine.graph.nodes[node_id][key] = value
                    # Persist updates if backend supports it
                    if getattr(self.graph_engine, "_should_persist", lambda: False)():
                        try:
                            node_props = dict(self.graph_engine.graph.nodes[node_id])
                            self.graph_engine.db_backend.add_node(node_id, node_props.get('type'), node_props)
                        except Exception:
                            pass
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
    
    def bulk_create_nodes(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Create multiple nodes in bulk
        
        Args:
            nodes: List of dicts with 'id', 'type', and optional 'properties'
            
        Returns:
            Operation result with success count and error details
        """
        created_count = 0
        errors = []
        self._transaction_stack = []
        
        for node_data in nodes:
            try:
                node_id = node_data.get('id')
                node_type = node_data.get('type', 'Entity')
                properties = node_data.get('properties', {})
                
                if not node_id:
                    errors.append({"node": node_data, "error": "Missing node ID"})
                    continue
                
                # Record for potential rollback
                self._transaction_stack.append({
                    "operation": "create_node",
                    "node_id": node_id,
                    "node_type": node_type
                })
                
                self.graph_engine.add_node(node_id, node_type, properties)
                created_count += 1
            except Exception as e:
                errors.append({"node": node_data, "error": str(e)})
                logger.error(f"Error creating node: {str(e)}")
        
        return {
            "nodes_created": created_count,
            "total_requested": len(nodes),
            "errors": errors,
            "status": "success" if not errors else "partial",
            "transaction_id": id(self._transaction_stack) if self._transaction_stack else None
        }
    
    def bulk_create_edges(self, edges: List[Dict]) -> Dict[str, Any]:
        """Create multiple edges in bulk
        
        Args:
            edges: List of dicts with 'source', 'target', and optional 'type', 'properties'
            
        Returns:
            Operation result with success count and error details
        """
        created_count = 0
        errors = []
        self._transaction_stack = []
        
        for edge_data in edges:
            try:
                source = edge_data.get('source')
                target = edge_data.get('target')
                edge_type = edge_data.get('type', 'RELATED_TO')
                properties = edge_data.get('properties', {})
                
                if not source or not target:
                    errors.append({"edge": edge_data, "error": "Missing source or target"})
                    continue
                
                # Record for potential rollback
                self._transaction_stack.append({
                    "operation": "create_edge",
                    "source": source,
                    "target": target,
                    "type": edge_type
                })
                
                self.graph_engine.add_edge(source, target, edge_type, properties)
                created_count += 1
            except Exception as e:
                errors.append({"edge": edge_data, "error": str(e)})
                logger.error(f"Error creating edge: {str(e)}")
        
        return {
            "edges_created": created_count,
            "total_requested": len(edges),
            "errors": errors,
            "status": "success" if not errors else "partial",
            "transaction_id": id(self._transaction_stack) if self._transaction_stack else None
        }
    
    def rollback_transaction(self, transaction_id: int = None) -> Dict[str, Any]:
        """Rollback the last bulk operation
        
        Args:
            transaction_id: Optional transaction ID to rollback
            
        Returns:
            Rollback status and count of operations reversed
        """
        if not self._transaction_stack:
            return {"status": "no_transaction", "rolled_back": 0}
        
        rolled_back = 0
        errors = []
        
        # Reverse the transaction stack (LIFO)
        for operation in reversed(self._transaction_stack):
            try:
                if operation["operation"] == "create_node":
                    self.graph_engine.remove_node(operation["node_id"])
                    rolled_back += 1
                elif operation["operation"] == "create_edge":
                    self.graph_engine.remove_edge(
                        operation["source"],
                        operation["target"],
                        operation["type"]
                    )
                    rolled_back += 1
            except Exception as e:
                errors.append({
                    "operation": operation,
                    "error": str(e)
                })
                logger.error(f"Rollback error: {str(e)}")
        
        self._transaction_stack = []
        
        return {
            "status": "success",
            "rolled_back": rolled_back,
            "errors": errors
        }

