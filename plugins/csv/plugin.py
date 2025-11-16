"""
CSV Parser Plugin - Processes CSV files with relationship data
"""
import csv
import io
from typing import Dict, Any

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process CSV data
    
    Expected CSV format (one of):
    1. source,target,relationship
    2. id,type,property1,property2,...
    3. Custom format with headers
    
    Or pass as string with CSV content
    """
    nodes_added = 0
    edges_added = 0
    
    # Handle string input
    if isinstance(data, str):
        csv_data = data
    elif isinstance(data, dict) and 'csv' in data:
        csv_data = data['csv']
    else:
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'CSV data must be a string or dict with "csv" key'
        }
    
    try:
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        if not rows:
            return {
                'nodes_added': 0,
                'edges_added': 0,
                'error': 'CSV file is empty'
            }
        
        # Detect format based on headers
        headers = list(rows[0].keys())
        
        # Format 1: source,target,relationship
        if 'source' in headers and 'target' in headers:
            for row in rows:
                source = row.get('source', '').strip()
                target = row.get('target', '').strip()
                relationship = row.get('relationship', 'RELATED_TO').strip()
                
                if source and target:
                    # Add nodes
                    graph_engine.add_node(source, 'Entity', {'name': source})
                    graph_engine.add_node(target, 'Entity', {'name': target})
                    nodes_added += 2
                    
                    # Add edge
                    properties = {k: v for k, v in row.items() 
                                if k not in ['source', 'target', 'relationship']}
                    graph_engine.add_edge(source, target, relationship, properties)
                    edges_added += 1
        
        # Format 2: id,type,properties...
        elif 'id' in headers:
            for row in rows:
                node_id = row.get('id', '').strip()
                node_type = row.get('type', 'Entity').strip()
                
                if node_id:
                    properties = {k: v for k, v in row.items() 
                               if k not in ['id', 'type']}
                    graph_engine.add_node(node_id, node_type, properties)
                    nodes_added += 1
        
        # Format 3: Custom - try to infer relationships
        else:
            # Assume first column is source, second is target
            first_col = headers[0]
            second_col = headers[1] if len(headers) > 1 else None
            
            for row in rows:
                source = row.get(first_col, '').strip()
                if second_col:
                    target = row.get(second_col, '').strip()
                    if source and target:
                        graph_engine.add_node(source, 'Entity', {'name': source})
                        graph_engine.add_node(target, 'Entity', {'name': target})
                        nodes_added += 2
                        
                        relationship = row.get('relationship', 'RELATED_TO') if 'relationship' in row else 'RELATED_TO'
                        graph_engine.add_edge(source, target, relationship, {})
                        edges_added += 1
                else:
                    # Single column - just add nodes
                    if source:
                        graph_engine.add_node(source, 'Entity', {'name': source})
                        nodes_added += 1
        
        return {
            'nodes_added': nodes_added,
            'edges_added': edges_added,
            'message': f'Processed {len(rows)} CSV rows'
        }
    
    except Exception as e:
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': f'CSV parsing failed: {str(e)}'
        }

