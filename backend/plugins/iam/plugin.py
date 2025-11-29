"""
IAM Permission Analyzer Plugin - Analyze identity and access relationships
"""
from typing import Dict, Any

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process IAM/permission data
    
    Expected format:
    {
        "users": [
            {
                "id": "user1",
                "name": "John Doe",
                "permissions": ["read:data", "write:data"],
                "roles": ["admin", "developer"],
                "groups": ["engineering"]
            }
        ],
        "roles": [
            {
                "id": "admin",
                "permissions": ["read:*", "write:*", "delete:*"]
            }
        ],
        "resources": [
            {
                "id": "resource1",
                "type": "database",
                "permissions_required": ["read:data"]
            }
        ],
        "access_grants": [
            {
                "user": "user1",
                "resource": "resource1",
                "permission": "read:data",
                "granted_via": "role"
            }
        ]
    }
    """
    nodes_added = 0
    edges_added = 0
    
    if not isinstance(data, dict):
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'IAM data must be a dictionary'
        }
    
    # Process users
    users = data.get('users', [])
    for user in users:
        user_id = user.get('id')
        if user_id:
            graph_engine.add_node(
                user_id,
                'User',
                {
                    'name': user.get('name'),
                    'permissions': user.get('permissions', []),
                    'roles': user.get('roles', []),
                    'groups': user.get('groups', []),
                    **user.get('properties', {})
                }
            )
            nodes_added += 1
            
            # Connect to roles
            for role in user.get('roles', []):
                graph_engine.add_edge(user_id, role, 'HAS_ROLE', {})
                edges_added += 1
            
            # Connect to groups
            for group in user.get('groups', []):
                graph_engine.add_edge(user_id, group, 'MEMBER_OF', {})
                edges_added += 1
    
    # Process roles
    roles = data.get('roles', [])
    for role in roles:
        role_id = role.get('id')
        if role_id:
            graph_engine.add_node(
                role_id,
                'Role',
                {
                    'permissions': role.get('permissions', []),
                    'description': role.get('description'),
                    **role.get('properties', {})
                }
            )
            nodes_added += 1
    
    # Process resources
    resources = data.get('resources', [])
    for resource in resources:
        resource_id = resource.get('id')
        if resource_id:
            graph_engine.add_node(
                resource_id,
                resource.get('type', 'Resource'),
                {
                    'name': resource.get('name'),
                    'permissions_required': resource.get('permissions_required', []),
                    **resource.get('properties', {})
                }
            )
            nodes_added += 1
    
    # Process access grants
    access_grants = data.get('access_grants', [])
    for grant in access_grants:
        user = grant.get('user')
        resource = grant.get('resource')
        permission = grant.get('permission')
        granted_via = grant.get('granted_via', 'direct')
        
        if user and resource:
            graph_engine.add_edge(
                user,
                resource,
                'CAN_ACCESS',
                {
                    'permission': permission,
                    'granted_via': granted_via
                }
            )
            edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed IAM data: {len(users)} users, {len(roles)} roles, {len(resources)} resources'
    }

