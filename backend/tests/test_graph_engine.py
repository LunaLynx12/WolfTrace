"""
Test suite for GraphEngine
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph_engine import GraphEngine


@pytest.fixture
def graph_engine():
    """Create a fresh GraphEngine instance for each test"""
    return GraphEngine()


class TestGraphEngine:
    """Test GraphEngine core functionality"""
    
    def test_add_node(self, graph_engine):
        """Test adding a node"""
        graph_engine.add_node('node1', {'type': 'host', 'name': 'Test Node'})
        nodes = graph_engine.get_nodes()
        assert len(nodes) == 1
        assert nodes[0]['id'] == 'node1'
        # Node properties are stored in the node dict
        node_data = nodes[0]
        assert node_data.get('type') == 'host' or 'type' in node_data
    
    def test_add_edge(self, graph_engine):
        """Test adding an edge"""
        graph_engine.add_node('node1', {'type': 'host'})
        graph_engine.add_node('node2', {'type': 'host'})
        graph_engine.add_edge('node1', 'node2', 'connection')
        
        edges = graph_engine.get_edges()
        assert len(edges) == 1
        assert edges[0]['source'] == 'node1'
        assert edges[0]['target'] == 'node2'
    
    def test_get_nodes(self, graph_engine):
        """Test getting all nodes"""
        graph_engine.add_node('node1', {'type': 'host'})
        graph_engine.add_node('node2', {'type': 'service'})
        
        nodes = graph_engine.get_nodes()
        assert len(nodes) == 2
    
    def test_get_edges(self, graph_engine):
        """Test getting all edges"""
        graph_engine.add_node('node1', {})
        graph_engine.add_node('node2', {})
        graph_engine.add_edge('node1', 'node2', 'RELATED_TO')
        
        edges = graph_engine.get_edges()
        assert len(edges) == 1
    
    def test_clear(self, graph_engine):
        """Test clearing the graph"""
        graph_engine.add_node('node1', {})
        graph_engine.add_node('node2', {})
        graph_engine.add_edge('node1', 'node2', 'RELATED_TO')
        
        graph_engine.clear()
        
        nodes = graph_engine.get_nodes()
        edges = graph_engine.get_edges()
        assert len(nodes) == 0
        assert len(edges) == 0
    
    def test_find_paths(self, graph_engine):
        """Test finding paths between nodes"""
        # Create a simple path: node1 -> node2 -> node3
        graph_engine.add_node('node1', {})
        graph_engine.add_node('node2', {})
        graph_engine.add_node('node3', {})
        graph_engine.add_edge('node1', 'node2', 'RELATED_TO')
        graph_engine.add_edge('node2', 'node3', 'RELATED_TO')
        
        paths = graph_engine.find_paths('node1', 'node3', max_depth=10)
        assert len(paths) > 0
        assert any('node1' in path and 'node3' in path for path in paths)
    
    def test_search_nodes(self, graph_engine):
        """Test searching for nodes via get_nodes with filtering"""
        graph_engine.add_node('node1', {'name': 'Test Node', 'type': 'host'})
        graph_engine.add_node('node2', {'name': 'Another Node', 'type': 'service'})
        
        # GraphEngine doesn't have search_nodes, but we can filter by type
        results = graph_engine.get_nodes(node_type='host')
        # Should find at least one node of type 'host'
        assert len(results) >= 1
        # Verify node1 is in the results
        node_ids = [node.get('id') for node in results]
        assert 'node1' in node_ids


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

