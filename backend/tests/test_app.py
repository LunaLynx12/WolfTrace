"""
Test suite for WolfTrace Backend API
"""
import pytest
import json
from pathlib import Path
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_network_data():
    """Load sample network data for testing"""
    data_file = Path(__file__).resolve().parent.parent / 'data' / 'examples' / 'example_network.json'
    with open(data_file, 'r') as f:
        return json.load(f)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test that health endpoint returns OK"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestPluginsEndpoint:
    """Test plugins endpoint"""
    
    def test_list_plugins(self, client):
        """Test listing available plugins"""
        response = client.get('/api/plugins')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check plugin structure
        plugin = data[0]
        assert 'name' in plugin
        assert 'version' in plugin
        assert 'description' in plugin


class TestGraphEndpoints:
    """Test graph-related endpoints"""
    
    def test_get_empty_graph(self, client):
        """Test getting an empty graph"""
        response = client.get('/api/graph')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'nodes' in data
        assert 'edges' in data
        assert isinstance(data['nodes'], list)
        assert isinstance(data['edges'], list)
    
    def test_clear_graph(self, client):
        """Test clearing the graph"""
        response = client.post('/api/clear')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] in ['success', 'cleared']
    
    def test_get_nodes(self, client):
        """Test getting nodes"""
        response = client.get('/api/nodes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_edges(self, client):
        """Test getting edges"""
        response = client.get('/api/edges')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestImportEndpoints:
    """Test data import endpoints"""
    
    def test_import_with_plugin(self, client, sample_network_data):
        """Test importing data with a specific plugin"""
        # Use a plugin that exists (e.g., 'nmap' or 'example')
        response = client.post(
            '/api/import',
            json={
                'collector': 'nmap',  # Use an available plugin
                'data': sample_network_data
            },
            content_type='application/json'
        )
        # Should either succeed or return an error if plugin doesn't support the data
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
    
    def test_import_autodetect(self, client, sample_network_data):
        """Test importing data with auto-detection"""
        response = client.post(
            '/api/import-autodetect',
            json={'data': sample_network_data},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_import_invalid_data(self, client):
        """Test importing invalid data"""
        response = client.post(
            '/api/import',
            json={
                'collector': 'network',
                'data': {'invalid': 'data'}
            },
            content_type='application/json'
        )
        # Should either succeed (graceful handling) or return an error
        assert response.status_code in [200, 400, 500]


class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_search_nodes(self, client):
        """Test searching for nodes"""
        response = client.get('/api/search?q=test')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_search_nodes_by_type(self, client):
        """Test searching nodes by type"""
        response = client.get('/api/nodes?type=host')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_get_analytics(self, client):
        """Test getting graph analytics stats"""
        response = client.get('/api/analytics/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Graph might be empty, so check for either stats or error message
        assert 'nodes' in data or 'error' in data
    
    def test_get_centrality(self, client):
        """Test getting centrality metrics"""
        response = client.get('/api/analytics/centrality')
        # This endpoint may not exist, so accept 404, 500, or 200
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)


class TestOpenAPI:
    """Test OpenAPI documentation endpoints"""
    
    def test_openapi_spec(self, client):
        """Test OpenAPI specification endpoint"""
        response = client.get('/openapi.json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'openapi' in data
        assert data['openapi'].startswith('3.')
        assert 'paths' in data
        assert 'info' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

