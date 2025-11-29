"""
Example Plugin - Demonstrates plugin structure
"""
from typing import Dict, Any

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process data and add nodes/edges to graph
    
    Args:
        data: Input data (can be dict, list, string, etc.)
        graph_engine: GraphEngine instance
    
    Returns:
        Dictionary with processing statistics
    """
    nodes_added = 0
    edges_added = 0
    
    # Example: Process a simple relationship list
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                source = item.get('source')
                target = item.get('target')
                relationship = item.get('relationship', 'RELATED_TO')
                
                if source and target:
                    # Add nodes
                    graph_engine.add_node(source, 'Entity', {'name': source})
                    graph_engine.add_node(target, 'Entity', {'name': target})
                    nodes_added += 2
                    
                    # Add edge
                    graph_engine.add_edge(source, target, relationship, item.get('properties', {}))
                    edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': 'Data processed successfully'
    }

