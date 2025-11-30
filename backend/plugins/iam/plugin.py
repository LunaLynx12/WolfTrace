"""
IAM Plugin - Processes Identity and Access Management data
Supports: users, roles, policies, access grants, permissions
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process IAM (Identity and Access Management) data
    
    Supports:
    - Users and their roles
    - Roles and their permissions
    - Policies and access grants
    - Resource access mappings
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
    if isinstance(users, list):
        for user in users:
            user_id = user.get('id') or user.get('username') or user.get('name')
            if user_id:
                graph_engine.add_node(user_id, 'User', {
                    'username': user.get('username', ''),
                    'email': user.get('email', ''),
                    'active': user.get('active', True),
                    **{k: v for k, v in user.items() if k not in ['id', 'username', 'name']}
                })
                nodes_added += 1
    
    # Process roles
    roles = data.get('roles', [])
    if isinstance(roles, list):
        for role in roles:
            role_id = role.get('id') or role.get('name')
            if role_id:
                graph_engine.add_node(role_id, 'Role', {
                    'name': role.get('name', ''),
                    'description': role.get('description', ''),
                    **{k: v for k, v in role.items() if k not in ['id', 'name']}
                })
                nodes_added += 1
                
                # Link users to roles
                if 'users' in role:
                    for user_id in role.get('users', []):
                        graph_engine.add_edge(user_id, role_id, 'HAS_ROLE', {})
                        edges_added += 1
    
    # Process user-role mappings
    user_roles = data.get('user_roles', [])
    if isinstance(user_roles, list):
        for mapping in user_roles:
            user_id = mapping.get('user_id') or mapping.get('user')
            role_id = mapping.get('role_id') or mapping.get('role')
            if user_id and role_id:
                graph_engine.add_edge(user_id, role_id, 'HAS_ROLE', {})
                edges_added += 1
    
    # Process policies
    policies = data.get('policies', [])
    if isinstance(policies, list):
        for policy in policies:
            policy_id = policy.get('id') or policy.get('name')
            if policy_id:
                graph_engine.add_node(policy_id, 'Policy', {
                    'name': policy.get('name', ''),
                    'description': policy.get('description', ''),
                    'permissions': policy.get('permissions', []),
                    **{k: v for k, v in policy.items() if k not in ['id', 'name']}
                })
                nodes_added += 1
                
                # Link roles to policies
                if 'roles' in policy:
                    for role_id in policy.get('roles', []):
                        graph_engine.add_edge(role_id, policy_id, 'HAS_POLICY', {})
                        edges_added += 1
    
    # Process access grants
    access_grants = data.get('access_grants', [])
    if isinstance(access_grants, list):
        for grant in access_grants:
            principal_id = grant.get('principal_id') or grant.get('user_id') or grant.get('role_id')
            resource_id = grant.get('resource_id') or grant.get('resource')
            permission = grant.get('permission') or grant.get('action', 'ACCESS')
            
            if principal_id and resource_id:
                # Add resource node if it doesn't exist
                graph_engine.add_node(resource_id, 'Resource', {
                    'type': grant.get('resource_type', 'unknown'),
                    **{k: v for k, v in grant.items() if k not in ['principal_id', 'user_id', 'role_id', 'resource_id', 'resource']}
                })
                nodes_added += 1
                
                # Link principal to resource
                graph_engine.add_edge(principal_id, resource_id, 'HAS_ACCESS', {
                    'permission': permission
                })
                edges_added += 1
    
    # Process permissions
    permissions = data.get('permissions', [])
    if isinstance(permissions, list):
        for perm in permissions:
            perm_id = perm.get('id') or perm.get('name')
            if perm_id:
                graph_engine.add_node(perm_id, 'Permission', {
                    'name': perm.get('name', ''),
                    'action': perm.get('action', ''),
                    'resource': perm.get('resource', ''),
                    **{k: v for k, v in perm.items() if k not in ['id', 'name']}
                })
                nodes_added += 1
                
                # Link roles to permissions
                if 'roles' in perm:
                    for role_id in perm.get('roles', []):
                        graph_engine.add_edge(role_id, perm_id, 'HAS_PERMISSION', {})
                        edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed {nodes_added} nodes and {edges_added} edges'
    }

