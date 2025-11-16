"""
Plugin Manager - Handles loading and executing modular plugins
"""
import os
import importlib
import importlib.util
import json
from typing import Dict, Any, List
from pathlib import Path

class PluginManager:
    def __init__(self, plugins_dir: str = 'plugins'):
        """
        Initialize plugin manager
        
        Args:
            plugins_dir: Directory containing plugin modules
        """
        self.plugins_dir = plugins_dir
        self.plugins = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all plugins from the plugins directory"""
        plugins_path = Path(self.plugins_dir)
        if not plugins_path.exists():
            print(f"Plugins directory {plugins_path} does not exist")
            return
        
        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                try:
                    plugin = self._load_plugin(plugin_dir)
                    if plugin:
                        self.plugins[plugin['name']] = plugin
                        print(f"Loaded plugin: {plugin['name']}")
                except Exception as e:
                    print(f"Failed to load plugin {plugin_dir.name}: {e}")
    
    def _load_plugin(self, plugin_dir: Path) -> Dict[str, Any]:
        """Load a single plugin"""
        plugin_file = plugin_dir / 'plugin.py'
        if not plugin_file.exists():
            return None
        
        # Read plugin metadata
        metadata_file = plugin_dir / 'metadata.json'
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Import plugin module
        spec = importlib.util.spec_from_file_location(
            plugin_dir.name,
            plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return {
            'name': metadata.get('name', plugin_dir.name),
            'version': metadata.get('version', '1.0.0'),
            'description': metadata.get('description', ''),
            'supported_formats': metadata.get('supported_formats', []),
            'module': module,
            'directory': plugin_dir
        }
    
    def process_data(self, collector_name: str, data: Any, graph_engine) -> Dict[str, Any]:
        """
        Process data using a specific collector plugin
        
        Args:
            collector_name: Name of the collector plugin
            data: Data to process (can be dict, list, string, etc.)
            graph_engine: GraphEngine instance to add nodes/edges to
        
        Returns:
            Processing result with stats
        """
        if collector_name not in self.plugins:
            raise ValueError(f"Plugin '{collector_name}' not found")
        
        plugin = self.plugins[collector_name]
        module = plugin['module']
        
        if not hasattr(module, 'process'):
            raise ValueError(f"Plugin '{collector_name}' missing 'process' function")
        
        # Call plugin's process function
        result = module.process(data, graph_engine)
        
        return {
            'plugin': collector_name,
            'result': result,
            'status': 'success'
        }
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins"""
        return [
            {
                'name': plugin['name'],
                'version': plugin['version'],
                'description': plugin['description'],
                'supported_formats': plugin['supported_formats']
            }
            for plugin in self.plugins.values()
        ]
