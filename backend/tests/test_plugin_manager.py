"""
Test suite for PluginManager
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plugin_manager import PluginManager
from graph_engine import GraphEngine


@pytest.fixture
def plugin_manager():
    """Create a PluginManager instance"""
    backend_dir = Path(__file__).resolve().parent.parent
    plugins_path = str(backend_dir / 'plugins')
    return PluginManager(plugins_dir=plugins_path)


@pytest.fixture
def graph_engine():
    """Create a GraphEngine instance"""
    return GraphEngine()


class TestPluginManager:
    """Test PluginManager functionality"""
    
    def test_load_plugins(self, plugin_manager):
        """Test that plugins are loaded"""
        assert len(plugin_manager.plugins) > 0
    
    def test_list_plugins(self, plugin_manager):
        """Test listing plugins"""
        plugins = plugin_manager.list_plugins()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Check plugin structure
        plugin = plugins[0]
        assert 'name' in plugin
        assert 'version' in plugin
        assert 'description' in plugin
    
    def test_process_network_data(self, plugin_manager, graph_engine):
        """Test processing network data"""
        # Use a plugin that exists (e.g., 'nmap' or 'example')
        sample_data = {
            'hosts': [
                {'id': 'host1', 'ip': '192.168.1.1', 'name': 'Test Host'}
            ]
        }
        
        # Try with an available plugin
        available_plugins = list(plugin_manager.plugins.keys())
        if available_plugins:
            plugin_name = available_plugins[0]
            result = plugin_manager.process_data(plugin_name, sample_data, graph_engine)
            assert 'status' in result
            assert result['status'] == 'success'
        else:
            pytest.skip("No plugins available for testing")
    
    def test_detect_plugin(self, plugin_manager):
        """Test plugin auto-detection"""
        # Network data
        network_data = {
            'hosts': [{'id': 'host1', 'ip': '192.168.1.1'}],
            'connections': []
        }
        detected = plugin_manager.detect_plugin(network_data)
        assert detected is not None
        
        # AD data
        ad_data = {
            'users': [{'id': 'user1', 'name': 'Test User'}],
            'groups': []
        }
        detected = plugin_manager.detect_plugin(ad_data)
        assert detected is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

