"""Tests for bulk operations and advanced search endpoints"""
import pytest
from graph_engine import GraphEngine


def test_bulk_create_nodes(app_client):
    """Test bulk node creation endpoint"""
    client, ge = app_client
    result = client.post('/api/bulk/nodes/create', json={
        'nodes': [
            {'id': 'n1', 'type': 'Host', 'properties': {'ip': '192.168.1.1'}},
            {'id': 'n2', 'type': 'Host', 'properties': {'ip': '192.168.1.2'}},
            {'id': 'n3', 'type': 'Service'}
        ]
    })
    assert result.status_code == 201
    data = result.get_json()
    assert data['status'] == 'success'
    assert data['nodes_created'] == 3
    assert ge.graph.has_node('n1')
    assert ge.graph.has_node('n3')


def test_bulk_create_edges(app_client):
    """Test bulk edge creation endpoint"""
    client, ge = app_client
    # First create nodes
    for i in range(3):
        ge.add_node(f"n{i}")
    
    result = client.post('/api/bulk/edges/create', json={
        'edges': [
            {'source': 'n0', 'target': 'n1', 'type': 'CONNECTS'},
            {'source': 'n1', 'target': 'n2', 'type': 'CONNECTS'}
        ]
    })
    assert result.status_code == 201
    data = result.get_json()
    assert data['status'] == 'success'
    assert data['edges_created'] == 2
    assert ge.graph.has_edge('n0', 'n1')


def test_bulk_create_with_errors(app_client):
    """Test bulk creation with some invalid nodes"""
    client, ge = app_client
    result = client.post('/api/bulk/nodes/create', json={
        'nodes': [
            {'id': 'valid', 'type': 'Host'},
            {'type': 'Host'},  # Missing ID
            {'id': 'also_valid', 'type': 'Service'}
        ]
    })
    assert result.status_code == 207  # Multi-Status
    data = result.get_json()
    assert data['nodes_created'] == 2
    assert len(data['errors']) == 1


def test_bulk_rollback(app_client):
    """Test transaction rollback"""
    client, ge = app_client
    # Create nodes
    create_result = client.post('/api/bulk/nodes/create', json={
        'nodes': [
            {'id': 'rollback1', 'type': 'Host'},
            {'id': 'rollback2', 'type': 'Host'}
        ]
    })
    assert create_result.status_code == 201
    assert ge.graph.has_node('rollback1')
    
    # Rollback
    rollback_result = client.post('/api/bulk/rollback')
    assert rollback_result.status_code == 200
    data = rollback_result.get_json()
    assert data['rolled_back'] == 2
    assert not ge.graph.has_node('rollback1')


def test_search_regex(app_client):
    """Test regex search endpoint"""
    client, ge = app_client
    ge.add_node('server-001', 'Host', {'name': 'Production Server'})
    ge.add_node('server-002', 'Host', {'name': 'Test Server'})
    ge.add_node('client-001', 'Client', {'name': 'Test Client'})
    
    result = client.get('/api/search/regex?pattern=server.*')
    assert result.status_code == 200
    data = result.get_json()
    assert len(data) == 2
    ids = {n['id'] for n in data}
    assert 'server-001' in ids
    assert 'server-002' in ids


def test_search_fuzzy(app_client):
    """Test fuzzy search endpoint"""
    client, ge = app_client
    ge.add_node('database-prod', 'Service', {'name': 'Production Database'})
    ge.add_node('database-test', 'Service', {'name': 'Test Database'})
    ge.add_node('cache-prod', 'Service', {'name': 'Production Cache'})
    
    result = client.get('/api/search/fuzzy?query=database&threshold=0.5')
    assert result.status_code == 200
    data = result.get_json()
    assert len(data) >= 2
    # Should find database nodes with higher scores
    top = data[0]
    assert 'database' in top['id'].lower() or 'database' in top.get('name', '').lower()


def test_search_full_text(app_client):
    """Test full-text search endpoint"""
    client, ge = app_client
    ge.add_node('host1', 'Host', {'name': 'Production Server', 'env': 'prod'})
    ge.add_node('host2', 'Host', {'name': 'Test Server', 'env': 'test'})
    
    result = client.get('/api/search/full-text?query=Production')
    assert result.status_code == 200
    data = result.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Production Server'


def test_search_advanced_filter(app_client):
    """Test advanced search with complex filters"""
    client, ge = app_client
    ge.add_node('host1', 'Host', {'name': 'Server A', 'env': 'prod', 'critical': True})
    ge.add_node('host2', 'Host', {'name': 'Server B', 'env': 'test', 'critical': False})
    ge.add_node('host3', 'Service', {'name': 'API Service', 'env': 'prod'})
    
    # Search for critical prod nodes
    result = client.post('/api/search/advanced', json={
        'and': [
            {'env': 'prod'},
            {'type': 'Host'}
        ]
    })
    assert result.status_code == 200
    data = result.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 'host1'
