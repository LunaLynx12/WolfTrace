"""
Plugin Manager - Handles loading and executing modular plugins
Optimized for efficiency and better plugin separation
"""
import os
import importlib
import importlib.util
import json
import ipaddress
import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from functools import lru_cache

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
    
    def detect_nmap(self, data: Any) -> Optional[str]:
        """Detect Nmap XML data"""
        if 'nmap' not in self.plugins:
            return None
        
        # Check string data first (fastest)
        if isinstance(data, str):
            if (data.strip().startswith('<?xml') or data.strip().startswith('<')) and 'nmap' in data.lower()[:200]:
                return 'nmap'
        
        # Check dict data
        if isinstance(data, dict):
            # Check metadata tool
            metadata_tool = self._get_nested_value(data, 'metadata', 'tool', default='')
            if metadata_tool and 'nmap' in metadata_tool.lower():
                return 'nmap'
            
            # Check for nmap key
            if 'nmap' in data:
                return 'nmap'
            
            # Check for XML in raw_output
            if self._has_nested_key_cached(data, 'raw_output', cache_key='raw_output'):
                raw_output = self._get_nested_value(data, 'raw_output', default='')
                if isinstance(raw_output, str) and ('nmap' in raw_output.lower() or '<?xml' in raw_output[:100]):
                    return 'nmap'
        
        return None
    
    def detect_csv(self, data: Any) -> Optional[str]:
        """Detect CSV data"""
        if 'csv' not in self.plugins:
            return None
        
        if isinstance(data, str):
            if ',' in data and '\n' in data:
                lines = data.strip().split('\n')
                if len(lines) > 1 and ',' in lines[0]:
                    return 'csv'
        
        return None
    
    def detect_network(self, data: Any) -> Optional[str]:
        """Detect network scanning/topology data"""
        if 'network' not in self.plugins:
            return None
        
        if not isinstance(data, dict):
            return None
        
        # Tool indicators mapping
        tool_indicators = {
            'rustscan', 'gobuster', 'dig', 'masscan', 'zmap', 'webapprecon',
            'httpx', 'whatweb', 'wafw00f', 'geoip', 'certificate_transparency',
            'whois_domain', 'whois_ips', 'network_topology', 'ip_domain_mapping',
            'nikto', 'nuclei'
        }
        
        # Fast check: metadata tool
        metadata_tool = self._get_nested_value(data, 'metadata', 'tool', default='')
        if metadata_tool and metadata_tool.lower() in tool_indicators:
            return 'network'
        
        # Fast check: tool keys at top level
        if any(tool in data for tool in tool_indicators):
            return 'network'
        
        # Priority 1: IP addresses as keys (strongest indicator)
        ip_key_count = self._count_ip_keys(data)
        if ip_key_count >= 3:
            return 'network'
        
        # Priority 2: Network topology structure
        if ('nodes' in data and 'edges' in data) or 'network_topology' in data:
            return 'network'
        
        # Check for network scanning indicators
        network_indicators = {
            'ports', 'port', 'hosts', 'host', 'connections', 'connection',
            'queries', 'records', 'services', 'ips'
        }
        
        has_network_indicators = any(
            key in data or self._has_nested_key_cached(data, key, cache_key=f'network_{key}')
            for key in network_indicators
        )
        
        if has_network_indicators and ip_key_count > 0:
            return 'network'
        
        # Additional check: ports + hosts combination
        has_ports = 'ports' in data or self._has_nested_key_cached(data, 'ports', cache_key='ports')
        has_hosts = 'hosts' in data or self._has_nested_key_cached(data, 'hosts', cache_key='hosts')
        
        if has_ports and has_hosts:
            return 'network'
        
        return None
    
    def detect_ad(self, data: Any) -> Optional[str]:
        """Detect Active Directory data"""
        if 'ad' not in self.plugins:
            return None
        
        if not isinstance(data, dict):
            return None
        
        # AD-specific indicators
        ad_indicators = {
            'users', 'user', 'groups', 'group', 'computers', 'computer',
            'domain_controllers', 'organizational_units', 'ous', 'domains', 'domain'
        }
        
        # Count AD indicators
        ad_indicator_count = sum(
            1 for key in ad_indicators
            if key in data or self._has_nested_key_cached(data, key, cache_key=f'ad_{key}')
        )
        
        # Need at least 2 AD indicators
        if ad_indicator_count < 2:
            return None
        
        # Check for AD-specific domain structure
        if self._has_nested_key_cached(data, 'domains', cache_key='domains'):
            domains_value = self._get_nested_value(data, 'domains', default=None)
            if isinstance(domains_value, dict):
                return 'ad'
            elif isinstance(domains_value, list) and len(domains_value) > 0:
                first_domain = domains_value[0]
                if isinstance(first_domain, dict) and ('domain_controllers' in first_domain or 'users' in first_domain):
                    return 'ad'
        
        # Check for domains/computers without network scanning indicators
        has_domains = 'domains' in data or 'domain' in data
        has_computers = 'computers' in data or 'computer' in data
        
        if (has_domains or has_computers):
            # Make sure it's not network scanning data
            has_ports = 'ports' in data or self._has_nested_key_cached(data, 'ports', cache_key='ports')
            has_hosts = 'hosts' in data or self._has_nested_key_cached(data, 'hosts', cache_key='hosts')
            has_connections = 'connections' in data or self._has_nested_key_cached(data, 'connections', cache_key='connections')
            
            if not (has_ports or has_hosts or has_connections):
                return 'ad'
        
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
        priority_order = ['nmap', 'ad', 'iam', 'cloud', 'network', 'csv']
        
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
        # 1. String-based detection (fastest)
        # 2. Nmap (specific XML format)
        # 3. CSV (specific text format)
        # 4. AD (specific structure)
        # 5. IAM (specific structure)
        # 6. Cloud (specific structure)
        # 7. Network (generic, but common)
        # 8. Plugin test fallback
        
        # String data detection
        if isinstance(data, str):
            result = self.detector.detect_nmap(data)
            if result:
                return result
            
            result = self.detector.detect_csv(data)
            if result:
                return result
        
        # Dict data detection
        if isinstance(data, dict):
            # Try specific detectors first (most specific to least specific)
            detectors = [
                self.detector.detect_nmap,
                self.detector.detect_ad,
                self.detector.detect_iam,
                self.detector.detect_cloud,
                self.detector.detect_network,
            ]
            
            for detector in detectors:
                result = detector(data)
                if result:
                    return result
        
        # Fallback: try plugins directly
        result = self.detector.detect_by_plugin_test(data)
        if result:
            return result
        
        # Final fallback: default to network if dict data
        if isinstance(data, dict) and 'network' in self.plugins:
            return 'network'
        
        return None
