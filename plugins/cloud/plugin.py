"""
Cloud Infrastructure Plugin - Processes cloud resource data
Supports AWS, Azure, GCP, etc.
"""
from typing import Dict, Any

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process cloud infrastructure data
    
    Expected format:
    {
        "provider": "aws",
        "resources": [
            {
                "id": "i-123456",
                "type": "ec2",
                "name": "web-server",
                "relationships": [
                    {"target": "sg-abc123", "type": "HAS_SECURITY_GROUP"},
                    {"target": "vpc-xyz789", "type": "IN_VPC"}
                ]
            }
        ]
    }
    """
    nodes_added = 0
    edges_added = 0
    
    if isinstance(data, dict):
        provider = data.get('provider', 'cloud')
        resources = data.get('resources', [])
        
        for resource in resources:
            resource_id = resource.get('id')
            resource_type = resource.get('type', 'Resource')
            
            if resource_id:
                graph_engine.add_node(
                    resource_id,
                    resource_type,
                    {
                        'name': resource.get('name'),
                        'provider': provider,
                        **resource.get('properties', {})
                    }
                )
                nodes_added += 1
                
                # Process relationships
                relationships = resource.get('relationships', [])
                for rel in relationships:
                    target = rel.get('target')
                    rel_type = rel.get('type', 'RELATED_TO')
                    
                    if target:
                        graph_engine.add_edge(
                            resource_id,
                            target,
                            rel_type,
                            rel.get('properties', {})
                        )
                        edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed {nodes_added} cloud resources'
    }

