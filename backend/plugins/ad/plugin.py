"""
Active Directory Plugin - Processes AD relationship data
Inspired by BloodHound but modular for WolfTrace
"""
from typing import Dict, Any, List

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process Active Directory data
    
    Expected format:
    {
        "users": [
            {"name": "user1", "domain": "corp.local", "groups": ["group1", "group2"]},
            ...
        ],
        "groups": [
            {"name": "group1", "domain": "corp.local", "members": ["user1"], "nested": ["group2"]},
            ...
        ],
        "computers": [
            {"name": "PC1", "domain": "corp.local", "sessions": ["user1"]},
            ...
        ],
        "relationships": [
            {"source": "user1", "target": "group1", "type": "MEMBER_OF"},
            ...
        ]
    }
    """
    nodes_added = 0
    edges_added = 0
    
    if not isinstance(data, dict):
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'AD data must be a dictionary'
        }
    
    # Process users
    users = data.get('users', [])
    for user in users:
        user_id = f"{user.get('domain', '')}\\{user.get('name', '')}"
        if user.get('name'):
            graph_engine.add_node(
                user_id,
                'User',
                {
                    'name': user.get('name'),
                    'domain': user.get('domain'),
                    'enabled': user.get('enabled', True),
                    **user.get('properties', {})
                }
            )
            nodes_added += 1
            
            # Add group memberships
            for group_name in user.get('groups', []):
                group_id = f"{user.get('domain', '')}\\{group_name}"
                graph_engine.add_edge(user_id, group_id, 'MEMBER_OF', {})
                edges_added += 1
    
    # Process groups
    groups = data.get('groups', [])
    for group in groups:
        group_id = f"{group.get('domain', '')}\\{group.get('name', '')}"
        if group.get('name'):
            graph_engine.add_node(
                group_id,
                'Group',
                {
                    'name': group.get('name'),
                    'domain': group.get('domain'),
                    'type': group.get('type', 'Security'),
                    **group.get('properties', {})
                }
            )
            nodes_added += 1
            
            # Add nested groups
            for nested_group in group.get('nested', []):
                nested_id = f"{group.get('domain', '')}\\{nested_group}"
                graph_engine.add_edge(group_id, nested_id, 'NESTED_IN', {})
                edges_added += 1
    
    # Process computers
    computers = data.get('computers', [])
    for computer in computers:
        computer_id = f"{computer.get('domain', '')}\\{computer.get('name', '')}"
        if computer.get('name'):
            graph_engine.add_node(
                computer_id,
                'Computer',
                {
                    'name': computer.get('name'),
                    'domain': computer.get('domain'),
                    'os': computer.get('os'),
                    **computer.get('properties', {})
                }
            )
            nodes_added += 1
            
            # Add sessions
            for user_name in computer.get('sessions', []):
                user_id = f"{computer.get('domain', '')}\\{user_name}"
                graph_engine.add_edge(user_id, computer_id, 'HAS_SESSION', {})
                edges_added += 1
    
    # Process explicit relationships
    relationships = data.get('relationships', [])
    for rel in relationships:
        source = rel.get('source')
        target = rel.get('target')
        rel_type = rel.get('type', 'RELATED_TO')
        
        if source and target:
            graph_engine.add_edge(source, target, rel_type, rel.get('properties', {}))
            edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed AD data: {len(users)} users, {len(groups)} groups, {len(computers)} computers'
    }

