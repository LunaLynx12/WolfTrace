"""
Query Builder - Advanced filtering and querying for graph data
"""
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime

class QueryBuilder:
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
    
    def build_query(self, filters: Dict[str, Any]) -> List[Dict]:
        """
        Build and execute a query with filters
        
        Filters format:
        {
            "node_type": ["Host", "User"],
            "properties": {
                "os": "Linux",
                "enabled": True
            },
            "edge_type": ["CONNECTS_TO", "MEMBER_OF"],
            "date_range": {
                "field": "created_at",
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "text_search": "search term",
            "min_degree": 2,
            "max_degree": 10
        }
        """
        nodes = self.graph_engine.get_nodes()
        edges = self.graph_engine.get_edges()
        
        # Filter nodes
        filtered_nodes = self._filter_nodes(nodes, filters)
        
        # Filter edges
        filtered_edges = self._filter_edges(edges, filters, filtered_nodes)
        
        # Get node IDs from filtered nodes
        node_ids = {node['id'] for node in filtered_nodes}
        
        # Filter edges to only include those connecting filtered nodes
        final_edges = [
            edge for edge in filtered_edges
            if edge.get('source') in node_ids and edge.get('target') in node_ids
        ]
        
        return {
            'nodes': filtered_nodes,
            'edges': final_edges,
            'count': len(filtered_nodes)
        }
    
    def _filter_nodes(self, nodes: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to nodes"""
        result = nodes
        
        # Filter by node type
        if 'node_type' in filters:
            types = filters['node_type']
            if isinstance(types, str):
                types = [types]
            result = [n for n in result if n.get('type') in types]
        
        # Filter by properties
        if 'properties' in filters:
            props = filters['properties']
            for prop_key, prop_value in props.items():
                result = [
                    n for n in result
                    if n.get(prop_key) == prop_value or 
                       (isinstance(n.get(prop_key), list) and prop_value in n.get(prop_key, []))
                ]
        
        # Text search
        if 'text_search' in filters:
            search_term = filters['text_search'].lower()
            result = [
                n for n in result
                if search_term in str(n.get('id', '')).lower() or
                  any(search_term in str(v).lower() for v in n.values() if isinstance(v, str))
            ]
        
        # Date range filter
        if 'date_range' in filters:
            date_filter = filters['date_range']
            field = date_filter.get('field', 'created_at')
            start = date_filter.get('start')
            end = date_filter.get('end')
            
            if start or end:
                result = [
                    n for n in result
                    if self._in_date_range(n.get(field), start, end)
                ]
        
        # Degree filtering
        if 'min_degree' in filters or 'max_degree' in filters:
            graph = self.graph_engine.graph
            min_deg = filters.get('min_degree', 0)
            max_deg = filters.get('max_degree', float('inf'))
            
            result = [
                n for n in result
                if min_deg <= graph.degree(n['id']) <= max_deg
            ]
        
        return result
    
    def _filter_edges(self, edges: List[Dict], filters: Dict, filtered_nodes: List[Dict]) -> List[Dict]:
        """Apply filters to edges"""
        result = edges
        
        # Filter by edge type
        if 'edge_type' in filters:
            types = filters['edge_type']
            if isinstance(types, str):
                types = [types]
            result = [e for e in result if e.get('type') in types]
        
        # Filter by edge properties
        if 'edge_properties' in filters:
            props = filters['edge_properties']
            for prop_key, prop_value in props.items():
                result = [
                    e for e in result
                    if e.get(prop_key) == prop_value
                ]
        
        return result
    
    def _in_date_range(self, date_str: Optional[str], start: Optional[str], end: Optional[str]) -> bool:
        """Check if a date string is within range"""
        if not date_str:
            return False
        
        try:
            date_val = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if start:
                start_date = datetime.fromisoformat(start)
                if date_val < start_date:
                    return False
            if end:
                end_date = datetime.fromisoformat(end)
                if date_val > end_date:
                    return False
            return True
        except:
            return False
    
    def get_statistics_for_query(self, filters: Dict) -> Dict:
        """Get statistics for a filtered query"""
        query_result = self.build_query(filters)
        
        nodes = query_result['nodes']
        edges = query_result['edges']
        
        # Calculate stats
        node_types = {}
        edge_types = {}
        
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for edge in edges:
            edge_type = edge.get('type', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        return {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'node_types': node_types,
            'edge_types': edge_types
        }

