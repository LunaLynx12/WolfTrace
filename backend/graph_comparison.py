"""
Graph Comparison - Compare two graphs and find differences
"""
from typing import Dict, List, Set, Any
from collections import defaultdict

class GraphComparison:
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
    
    def compare_graphs(self, graph1: Dict, graph2: Dict) -> Dict[str, Any]:
        """
        Compare two graphs and return differences
        
        Args:
            graph1: First graph (nodes and edges)
            graph2: Second graph (nodes and edges)
        
        Returns:
            Comparison result with added/removed/changed items
        """
        nodes1 = {node['id']: node for node in graph1.get('nodes', [])}
        nodes2 = {node['id']: node for node in graph2.get('nodes', [])}
        
        edges1 = self._normalize_edges(graph1.get('edges', []))
        edges2 = self._normalize_edges(graph2.get('edges', []))
        
        # Find node differences
        node_ids1 = set(nodes1.keys())
        node_ids2 = set(nodes2.keys())
        
        added_nodes = [nodes2[nid] for nid in node_ids2 - node_ids1]
        removed_nodes = [nodes1[nid] for nid in node_ids1 - node_ids2]
        common_nodes = node_ids1 & node_ids2
        
        # Find changed nodes
        changed_nodes = []
        for nid in common_nodes:
            node1 = nodes1[nid]
            node2 = nodes2[nid]
            if node1 != node2:
                changed_nodes.append({
                    'id': nid,
                    'old': node1,
                    'new': node2,
                    'changes': self._get_property_changes(node1, node2)
                })
        
        # Find edge differences
        edge_ids1 = set(edges1.keys())
        edge_ids2 = set(edges2.keys())
        
        added_edges = [edges2[eid] for eid in edge_ids2 - edge_ids1]
        removed_edges = [edges1[eid] for eid in edge_ids1 - edge_ids2]
        common_edges = edge_ids1 & edge_ids2
        
        # Find changed edges
        changed_edges = []
        for eid in common_edges:
            edge1 = edges1[eid]
            edge2 = edges2[eid]
            if edge1 != edge2:
                changed_edges.append({
                    'id': eid,
                    'old': edge1,
                    'new': edge2,
                    'changes': self._get_property_changes(edge1, edge2)
                })
        
        # Statistics
        stats = {
            'nodes': {
                'total_1': len(nodes1),
                'total_2': len(nodes2),
                'added': len(added_nodes),
                'removed': len(removed_nodes),
                'changed': len(changed_nodes),
                'unchanged': len(common_nodes) - len(changed_nodes)
            },
            'edges': {
                'total_1': len(edges1),
                'total_2': len(edges2),
                'added': len(added_edges),
                'removed': len(removed_edges),
                'changed': len(changed_edges),
                'unchanged': len(common_edges) - len(changed_edges)
            }
        }
        
        return {
            'stats': stats,
            'nodes': {
                'added': added_nodes,
                'removed': removed_nodes,
                'changed': changed_nodes
            },
            'edges': {
                'added': added_edges,
                'removed': removed_edges,
                'changed': changed_edges
            }
        }
    
    def _normalize_edges(self, edges: List[Dict]) -> Dict[str, Dict]:
        """Normalize edges to a dictionary keyed by (source, target, type)"""
        normalized = {}
        for edge in edges:
            source = edge.get('source') or edge.get('source_id', '')
            target = edge.get('target') or edge.get('target_id', '')
            edge_type = edge.get('type', 'RELATED_TO')
            key = f"{source}::{target}::{edge_type}"
            normalized[key] = edge
        return normalized
    
    def _get_property_changes(self, old: Dict, new: Dict) -> Dict[str, Any]:
        """Get property changes between two objects"""
        changes = {}
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes
    
    def create_diff_graph(self, comparison_result: Dict) -> Dict:
        """Create a visualization graph showing differences"""
        nodes = []
        links = []
        
        # Add nodes with change indicators
        for node in comparison_result['nodes']['added']:
            nodes.append({
                **node,
                'change_type': 'added',
                'id': f"added_{node['id']}"
            })
        
        for node in comparison_result['nodes']['removed']:
            nodes.append({
                **node,
                'change_type': 'removed',
                'id': f"removed_{node['id']}"
            })
        
        for change in comparison_result['nodes']['changed']:
            nodes.append({
                **change['new'],
                'change_type': 'changed',
                'id': change['id']
            })
        
        # Add edges with change indicators
        for edge in comparison_result['edges']['added']:
            source = edge.get('source') or edge.get('source_id', '')
            target = edge.get('target') or edge.get('target_id', '')
            links.append({
                **edge,
                'source': f"added_{source}" if any(n['id'] == source and n.get('change_type') == 'added' for n in nodes) else source,
                'target': f"added_{target}" if any(n['id'] == target and n.get('change_type') == 'added' for n in nodes) else target,
                'change_type': 'added'
            })
        
        for edge in comparison_result['edges']['removed']:
            source = edge.get('source') or edge.get('source_id', '')
            target = edge.get('target') or edge.get('target_id', '')
            links.append({
                **edge,
                'source': f"removed_{source}" if any(n['id'] == source and n.get('change_type') == 'removed' for n in nodes) else source,
                'target': f"removed_{target}" if any(n['id'] == target and n.get('change_type') == 'removed' for n in nodes) else target,
                'change_type': 'removed'
            })
        
        return {
            'nodes': nodes,
            'edges': links
        }

