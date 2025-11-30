"""
Plugin Manager - Handles loading and executing modular plugins
Optimized for efficiency and better plugin separation
"""
import importlib
import importlib.util
import json
import ipaddress
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger('wolftrace.plugins')


class PluginDetector:
    """Helper class for efficient plugin detection with caching"""
    
    def __init__(self, plugins: Dict[str, Any]):
        self.plugins = plugins
        self._nested_key_cache: Dict[str, bool] = {}
        self._test_engine = None
    
    def _get_test_engine(self):
        """Lazy-load test engine (only create once)"""
        if self._test_engine is None:
            from graph_engine import GraphEngine
            self._test_engine = GraphEngine()
        return self._test_engine
    
    def _has_nested_key_cached(self, data: Any, key: str, max_depth: int = 3, cache_key: str = None) -> bool:
        """Recursively check if a key exists in nested dict structure (with caching)"""
        if cache_key and cache_key in self._nested_key_cache:
            return self._nested_key_cache[cache_key]
        
        result = self._has_nested_key(data, key, max_depth)
        
        if cache_key:
            self._nested_key_cache[cache_key] = result
        
        return result
    
    @staticmethod
    def _has_nested_key(data: Any, key: str, max_depth: int = 3) -> bool:
        """Recursively check if a key exists in nested dict structure"""
        if max_depth <= 0:
            return False
        if isinstance(data, dict):
            if key in data:
                return True
            for value in data.values():
                if PluginDetector._has_nested_key(value, key, max_depth - 1):
                    return True
        elif isinstance(data, list):
            for item in data:
                if PluginDetector._has_nested_key(item, key, max_depth - 1):
                    return True
        return False
    
    @staticmethod
    def _get_nested_value(data: Any, *keys, default=None):
        """Get nested value from dict using multiple keys"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def _count_ip_keys(self, data: Dict) -> int:
        """Count IP addresses in top-level keys (efficient check)"""
        if not isinstance(data, dict) or len(data) == 0:
            return 0
        
        ip_count = 0
        for key in list(data.keys())[:20]:  # Check first 20 keys
            if isinstance(key, str) and ('.' in key or ':' in key):
                try:
                    ip_part = key.split(':')[0].split('/')[0]
                    ipaddress.ip_address(ip_part)
                    ip_count += 1
                except (ValueError, AttributeError):
                    pass
        return ip_count
    
    
    def detect_web(self, data: Any) -> Optional[str]:
        """Detect web reconnaissance data from LangChain Recon Agent"""
        if 'web' not in self.plugins:
            return None
        
        if not isinstance(data, dict):
            return None
        
        # Check for metadata.json structure with tool field
        if 'tool' in data:
            tool_value = str(data.get('tool', '')).lower()
            if 'langchain' in tool_value or 'recon agent' in tool_value:
                return 'web'
        
        # Check for target field with domain (common in web recon data)
        if 'target' in data:
            target = str(data.get('target', '')).lower()
            # Check if target looks like a domain or URL
            if '.' in target and ('http' in target or any(c.isalpha() for c in target.split('.')[0])):
                # Check for web recon specific keys
                web_keys = ['scan_types', 'tools_used', 'scan_date', 'scan_results']
                if any(key in data for key in web_keys):
                    return 'web'
        
        # Check for web-specific data structures
        if 'data' in data:
            data_content = data.get('data', {})
            # Check for rustscan, httpx, gobuster, nuclei, nikto structures
            if isinstance(data_content, dict):
                web_indicators = [
                    'hosts' in data_content and 'ports' in str(data_content),  # RustScan
                    'results' in data_content and 'status_code' in str(data_content),  # HTTPX
                    'paths' in data_content,  # Gobuster
                    'findings' in data_content,  # Nuclei
                    'vulnerabilities' in data_content,  # Nikto
                    'certificates' in data_content,  # Certificate Transparency
                    'queries' in data_content,  # DNS Dig
                ]
                if any(web_indicators):
                    return 'web'
        
        return None
    
    
    
    def detect_iam(self, data: Any) -> Optional[str]:
        """Detect IAM (Identity and Access Management) data"""
        if 'iam' not in self.plugins:
            return None
        
        if not isinstance(data, dict):
            return None
        
        # IAM indicators (more specific than AD)
        has_users = 'users' in data
        has_roles = 'roles' in data
        has_access_grants = 'access_grants' in data
        
        # Check for AD indicators to exclude AD data
        has_ad_domains = 'domains' in data or 'domain' in data
        has_ad_computers = 'computers' in data or 'computer' in data
        
        if (has_users or has_roles or has_access_grants) and not has_ad_domains and not has_ad_computers:
            return 'iam'
        
        return None
    
    def detect_cloud(self, data: Any) -> Optional[str]:
        """Detect Cloud infrastructure data"""
        if 'cloud' not in self.plugins:
            return None
        
        if not isinstance(data, dict):
            return None
        
        # Cloud indicators
        if 'provider' in data:
            return 'cloud'
        
        if 'resources' in data and isinstance(data.get('resources'), list):
            return 'cloud'
        
        return None
    
    def detect_by_plugin_test(self, data: Any) -> Optional[str]:
        """Try each plugin to see if it can handle the data (fallback method)"""
        if not self.plugins:
            return None
        
        test_engine = self._get_test_engine()
        
        # Try plugins in order (prioritize specific ones first)
        priority_order = ['web', 'iam']
        
        # First try priority plugins
        for plugin_name in priority_order:
            if plugin_name in self.plugins:
                if self._test_plugin(plugin_name, data, test_engine):
                    return plugin_name
        
        # Then try remaining plugins
        for plugin_name, plugin in self.plugins.items():
            if plugin_name not in priority_order:
                if self._test_plugin(plugin_name, data, test_engine):
                    return plugin_name
        
        return None
    
    def _test_plugin(self, plugin_name: str, data: Any, test_engine) -> bool:
        """Test if a plugin can handle the data"""
        try:
            plugin = self.plugins[plugin_name]
            module = plugin['module']
            
            if not hasattr(module, 'process'):
                return False
            
            # Try to process with test engine
            result = module.process(data, test_engine)
            
            # If we get a result without error, this plugin can handle it
            return result is not None and not (isinstance(result, dict) and result.get('error'))
        except Exception:
            return False


class PluginManager:
    """Manages plugin loading, execution, and detection"""
    
    def __init__(self, plugins_dir: str = 'plugins'):
        """
        Initialize plugin manager
        
        Args:
            plugins_dir: Directory containing plugin modules
        """
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.detector: Optional[PluginDetector] = None
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all plugins from the plugins directory"""
        plugins_path = Path(self.plugins_dir)
        if not plugins_path.exists():
            logger.warning(f"Plugins directory {plugins_path} does not exist")
            return
        
        loaded_count = 0
        failed_count = 0
        
        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                try:
                    plugin = self._load_plugin(plugin_dir)
                    if plugin:
                        self.plugins[plugin['name']] = plugin
                        logger.info(
                            f"Loaded plugin: {plugin['name']} v{plugin['version']}",
                            extra={
                                'plugin': plugin['name'],
                                'version': plugin['version'],
                                'directory': str(plugin_dir)
                            }
                        )
                        loaded_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin {plugin_dir.name}: {str(e)}",
                        extra={'plugin_dir': str(plugin_dir), 'error': str(e)},
                        exc_info=True
                    )
                    failed_count += 1
        
        logger.info(
            f"Plugin loading complete: {loaded_count} loaded, {failed_count} failed",
            extra={'loaded': loaded_count, 'failed': failed_count, 'total': len(self.plugins)}
        )
        
        # Initialize detector after plugins are loaded
        self.detector = PluginDetector(self.plugins)
    
    def _load_plugin(self, plugin_dir: Path) -> Optional[Dict[str, Any]]:
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
            'detection_hints': metadata.get('detection_hints', []),  # New: detection hints
            'priority': metadata.get('priority', 5),  # New: detection priority (lower = higher priority)
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
        
        # If result is a dict, merge it with metadata, otherwise wrap it
        if isinstance(result, dict):
            return {
                'plugin': collector_name,
                'status': 'success',
                **result  # Merge plugin result fields (nodes_added, edges_added, etc.)
            }
        else:
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
    
    def detect_plugin(self, data: Any) -> Optional[str]:
        """
        Automatically detect which plugin can handle the given data
        Uses priority-based detection with efficient caching
        
        Args:
            data: Data to analyze (can be dict, list, string, etc.)
        
        Returns:
            Name of the plugin that can handle the data, or None if none found
        """
        if not self.detector:
            return None
        
        # Detection order (most specific first):
        # 1. Web (metadata.json based detection)
        # 2. IAM (specific structure)
        # 3. Plugin test fallback
        
        # Dict data detection
        if isinstance(data, dict):
            # Check metadata.json first (highest priority for real data)
            result = self.detector.detect_web(data)
            if result:
                return result
            
            # Try IAM detection
            result = self.detector.detect_iam(data)
            if result:
                return result
        
        # Fallback: try plugins directly
        result = self.detector.detect_by_plugin_test(data)
        if result:
            return result
        
        return None
