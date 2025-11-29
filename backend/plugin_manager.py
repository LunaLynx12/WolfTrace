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

    def _has_nested_key(self, data: Any, key: str, max_depth: int = 3) -> bool:
        """Recursively check if a key exists in nested dict structure"""
        if max_depth <= 0:
            return False
        if isinstance(data, dict):
            if key in data:
                return True
            for value in data.values():
                if self._has_nested_key(value, key, max_depth - 1):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._has_nested_key(item, key, max_depth - 1):
                    return True
        return False
    
    def _get_nested_value(self, data: Any, *keys, default=None):
        """Get nested value from dict using multiple keys"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def detect_plugin(self, data: Any) -> str:
        """
        Automatically detect which plugin can handle the given data
        
        Args:
            data: Data to analyze (can be dict, list, string, etc.)
        
        Returns:
            Name of the plugin that can handle the data, or None if none found
        """
        # Heuristic-based detection based on data structure
        # Order matters - more specific checks first
        if isinstance(data, dict):
            # Check for network scanning tools first (rustscan, gobuster, dig, nmap, etc.)
            tool_indicators = {
                'rustscan': 'network',
                'gobuster': 'network',
                'dig': 'network',
                'nmap': 'nmap',
                'masscan': 'network',
                'zmap': 'network',
                'webapprecon': 'network',  # WebAppRecon tool
                'httpx': 'network',
                'whatweb': 'network',
                'wafw00f': 'network',
                'geoip': 'network',
                'certificate_transparency': 'network',
                'whois_domain': 'network',
                'whois_ips': 'network',
                'network_topology': 'network',
                'ip_domain_mapping': 'network',
            }
            
            # Check metadata for tool name
            metadata_tool = self._get_nested_value(data, 'metadata', 'tool', default='')
            if metadata_tool and metadata_tool.lower() in tool_indicators:
                plugin_name = tool_indicators[metadata_tool.lower()]
                if plugin_name in self.plugins:
                    return plugin_name
            
            # Check for tool-specific keys at top level
            for tool_key, plugin_name in tool_indicators.items():
                if tool_key in data and plugin_name in self.plugins:
                    return plugin_name
            
            # PRIORITY 1: Check for IP addresses as top-level keys FIRST (geoip, whois_ips format)
            # This is the STRONGEST and most unambiguous network indicator
            ip_key_count = 0
            if isinstance(data, dict) and len(data) > 0:
                for key in list(data.keys())[:20]:  # Check first 20 keys
                    if isinstance(key, str) and ('.' in key or ':' in key):
                        # Check if it looks like IP addresses as keys
                        try:
                            import ipaddress
                            # Try to parse as IP (handle port notation like "1.2.3.4:80")
                            ip_part = key.split(':')[0].split('/')[0]
                            ipaddress.ip_address(ip_part)
                            ip_key_count += 1
                        except:
                            pass
                # If we have multiple IP keys (3+), it's definitely network data - return immediately
                if ip_key_count >= 3:
                    if 'network' in self.plugins:
                        return 'network'
            
            # PRIORITY 2: Check for network topology structure (nodes + edges) - strong network indicator
            has_nodes = 'nodes' in data
            has_edges = 'edges' in data
            has_network_topology = 'network_topology' in data
            if (has_nodes and has_edges) or has_network_topology:
                if 'network' in self.plugins:
                    return 'network'
            
            # Set has_ip_keys flag for later use
            has_ip_keys = ip_key_count > 0
            
            # Check for network scanning data structures (ports, hosts, etc.)
            has_ports = self._has_nested_key(data, 'ports') or self._has_nested_key(data, 'port')
            has_hosts = self._has_nested_key(data, 'hosts') or self._has_nested_key(data, 'host')
            has_connections = self._has_nested_key(data, 'connections') or self._has_nested_key(data, 'connection')
            has_dns_records = self._has_nested_key(data, 'queries') or self._has_nested_key(data, 'records')
            has_services = 'services' in data or self._has_nested_key(data, 'services')
            has_ips = 'ips' in data or self._has_nested_key(data, 'ips')
            
            # Network scanning indicators (rustscan has data.hosts, data.ports)
            if (has_ports or has_hosts or has_connections or has_dns_records or has_services or has_ips or has_ip_keys) and 'network' in self.plugins:
                # Make sure it's not AD data (AD has more specific structure)
                # AD requires MULTIPLE specific indicators, not just 'domains'
                has_ad_users = self._has_nested_key(data, 'users')
                has_ad_groups = self._has_nested_key(data, 'groups')
                has_ad_computers = self._has_nested_key(data, 'computers')
                has_ad_domain_controllers = self._has_nested_key(data, 'domain_controllers')
                has_ad_ous = self._has_nested_key(data, 'organizational_units') or self._has_nested_key(data, 'ous')
                
                # AD domains are different from DNS domains - check for AD-specific domain structure
                has_ad_domains = False
                if self._has_nested_key(data, 'domains'):
                    # Check if domains have AD-specific structure (like domain controllers, users, etc.)
                    domains_value = self._get_nested_value(data, 'domains', default=None)
                    if isinstance(domains_value, dict):
                        # AD domains are usually objects with properties
                        has_ad_domains = True
                    elif isinstance(domains_value, list) and len(domains_value) > 0:
                        # Check if it's a list of domain objects (AD) vs simple strings (DNS)
                        first_domain = domains_value[0]
                        if isinstance(first_domain, dict) and ('domain_controllers' in first_domain or 'users' in first_domain):
                            has_ad_domains = True
                
                # Require at least 2 AD-specific indicators to classify as AD
                ad_indicator_count = sum([
                    has_ad_users,
                    has_ad_groups,
                    has_ad_computers,
                    has_ad_domain_controllers,
                    has_ad_ous,
                    has_ad_domains
                ])
                
                # If we have strong network indicators and weak AD indicators, it's network
                if ad_indicator_count < 2:
                    return 'network'
            
            # Check for XML (Nmap) in nested structures
            if self._has_nested_key(data, 'raw_output'):
                raw_output = self._get_nested_value(data, 'raw_output', default='')
                if isinstance(raw_output, str) and ('nmap' in raw_output.lower() or '<?xml' in raw_output[:100]):
                    if 'nmap' in self.plugins:
                        return 'nmap'
            
            # Check for AD structure (Active Directory) - require specific indicators
            # AD should have domains/computers AND NOT have network scanning indicators
            has_ad_domains = self._has_nested_key(data, 'domains') or self._has_nested_key(data, 'domain')
            has_ad_computers = self._has_nested_key(data, 'computers') or self._has_nested_key(data, 'computer')
            has_ad_users = self._has_nested_key(data, 'users') or self._has_nested_key(data, 'user')
            has_ad_groups = self._has_nested_key(data, 'groups') or self._has_nested_key(data, 'group')
            
            # AD detection: need domains/computers AND not network scanning data
            if (has_ad_domains or has_ad_computers) and 'ad' in self.plugins:
                # Make sure it's not network scanning data
                if not (has_ports or has_hosts or has_connections):
                    return 'ad'
            
            # Check for IAM structure (more specific than AD)
            if (('users' in data or 'roles' in data or 'access_grants' in data) and 
                not has_ad_domains and not has_ad_computers and 'iam' in self.plugins):
                return 'iam'
            
            # Check for Cloud structure
            if ('provider' in data or ('resources' in data and isinstance(data.get('resources'), list))) and 'cloud' in self.plugins:
                return 'cloud'
        
        elif isinstance(data, str):
            # Check for XML (Nmap) - check before CSV since XML is more specific
            if (data.strip().startswith('<?xml') or data.strip().startswith('<')) and 'nmap' in self.plugins:
                return 'nmap'
            
            # Check for CSV
            if ',' in data and '\n' in data:
                lines = data.strip().split('\n')
                if len(lines) > 1 and ',' in lines[0] and 'csv' in self.plugins:
                    return 'csv'
        
        # Try each plugin with a test to see if it can handle the data
        # Use a lightweight check: see if plugin processes without error
        from graph_engine import GraphEngine
        test_engine = GraphEngine()
        
        for plugin_name, plugin in self.plugins.items():
            try:
                module = plugin['module']
                if hasattr(module, 'process'):
                    # Try to process with test engine
                    result = module.process(data, test_engine)
                    # If we get a result without error, this plugin can handle it
                    if result and not result.get('error'):
                        return plugin_name
            except Exception:
                # This plugin can't handle it, try next
                continue
        
        # Default fallback - try network first (most generic for scanning data)
        if isinstance(data, dict):
            if 'network' in self.plugins:
                return 'network'
            if 'cloud' in self.plugins:
                return 'cloud'
        
        return None