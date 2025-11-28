"""
Network Topology Plugin - Processes network scan data
Supports: standard format, RustScan, Gobuster, Dig, and merged formats
"""
from typing import Dict, Any, List
import logging

# Set up logging
logger = logging.getLogger(__name__)

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process network topology data
    
    Supported formats:
    1. Standard format:
       {
           "hosts": [{"ip": "192.168.1.1", "hostname": "router", "ports": [80, 443]}],
           "connections": [{"source": "192.168.1.1", "target": "192.168.1.2", "protocol": "tcp", "port": 22}]
       }
    
    2. RustScan format:
       {
           "data": {
               "hosts": [{
                   "addresses": [{"addr": "142.250.180.238", "addrtype": "ipv4"}],
                   "ports": [{"port": "80", "protocol": "tcp", "state": "open", "service": "http"}]
               }]
           }
       }
    
    3. Gobuster format:
       {
           "data": {
               "found_paths": ["/admin", "/api"],
               "status_codes": {"200": 5, "404": 10},
               "total_found": 15
           },
           "target": "http://example.com"
       }
    
    4. Dig format:
       {
           "queries": {
               "A": {"data": {"records": [{"type": "A", "value": "142.251.39.14"}]}},
               "MX": {"data": {"records": [{"type": "MX", "value": "smtp.example.com", "priority": 10}]}}
           },
           "target": "example.com"
       }
    
    5. Merged format (from ZIP):
       {
           "rustscan": {...},
           "gobuster": {...},
           "dig": {...}
    }
    """
    nodes_added = 0
    edges_added = 0
    
    if not isinstance(data, dict):
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'Network data must be a dictionary'
        }
    
    # Handle merged format (from ZIP files with multiple tools) - summary.json style
    # Check if we have tool-specific keys at top level (like summary.json)
    logger.info(f"Processing network data. Top-level keys: {list(data.keys())[:10]}")
    
    tool_processors = {
        'rustscan': process_rustscan,
        'gobuster': process_gobuster,
        'dig': process_dig,
        'httpx': process_httpx,
        'whatweb': process_whatweb,
        'wafw00f': process_wafw00f,
        'geoip': process_geoip,
        'certificate_transparency': process_certificate_transparency,
        'whois_domain': process_whois_domain,
        'whois_ips': process_whois_ips,
        'network_topology': process_network_topology,
        'ip_domain_mapping': process_ip_domain_mapping,
    }
    
    for tool_name, processor_func in tool_processors.items():
        if tool_name in data:
            try:
                logger.info(f"Processing {tool_name} data")
                result = processor_func(data[tool_name], graph_engine)
                tool_nodes = result.get('nodes_added', 0)
                tool_edges = result.get('edges_added', 0)
                nodes_added += tool_nodes
                edges_added += tool_edges
                logger.info(f"{tool_name}: Added {tool_nodes} nodes, {tool_edges} edges")
                if result.get('error'):
                    logger.warning(f"{tool_name} processing had error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error processing {tool_name}: {str(e)}", exc_info=True)
                # Continue processing other tools even if one fails
    
    # If we already processed tool-specific keys, we're done
    if nodes_added > 0 or edges_added > 0:
        return {
            'nodes_added': nodes_added,
            'edges_added': edges_added,
            'message': f'Processed {nodes_added} nodes and {edges_added} edges'
        }
    
    # Handle individual tool formats (from individual JSON files or merged without tool keys)
    # When ZIP files are merged using _merge_json_objects, they combine recursively
    # So we need to check for data structures that indicate each tool type
    # Note: We process ALL matching formats, not just the first one
    
    logger.info("Checking for individual file formats in merged data")
    
    # PRIORITY: Check for IP addresses as top-level keys FIRST (geoip, whois_ips format)
    # This happens when individual files are merged - IPs become top-level keys
    ip_keys_found = []
    if isinstance(data, dict) and len(data) > 0:
        for key in data.keys():
            if isinstance(key, str) and ('.' in key or ':' in key):
                # Check if it looks like an IP address
                try:
                    import ipaddress
                    ip_part = key.split(':')[0].split('/')[0]
                    ipaddress.ip_address(ip_part)
                    ip_keys_found.append(key)
                except:
                    pass
        
        # If we found IP keys, process them
        if len(ip_keys_found) >= 3:  # At least 3 IPs to be confident
            # Check what type of data they contain
            first_ip_key = ip_keys_found[0]
            first_ip_value = data[first_ip_key]
            
            if isinstance(first_ip_value, dict):
                # Check if it's GeoIP or IP WHOIS
                if 'data' in first_ip_value:
                    ip_info = first_ip_value.get('data', {})
                else:
                    ip_info = first_ip_value
                
                if 'country' in ip_info or 'city' in ip_info or 'latitude' in ip_info:
                    try:
                        logger.info(f"Detected GeoIP format in merged data ({len(ip_keys_found)} IPs)")
                        # Extract only IP keys for processing
                        geoip_data = {ip_key: data[ip_key] for ip_key in ip_keys_found if ip_key in data}
                        result = process_geoip(geoip_data, graph_engine)
                        nodes_added += result.get('nodes_added', 0)
                        edges_added += result.get('edges_added', 0)
                        logger.info(f"GeoIP: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                    except Exception as e:
                        logger.error(f"Error processing GeoIP: {str(e)}", exc_info=True)
                elif 'org' in ip_info or 'asn' in ip_info or 'netrange' in ip_info:
                    try:
                        logger.info(f"Detected IP WHOIS format in merged data ({len(ip_keys_found)} IPs)")
                        # Extract only IP keys for processing
                        whois_data = {ip_key: data[ip_key] for ip_key in ip_keys_found if ip_key in data}
                        result = process_whois_ips(whois_data, graph_engine)
                        nodes_added += result.get('nodes_added', 0)
                        edges_added += result.get('edges_added', 0)
                        logger.info(f"IP WHOIS: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                    except Exception as e:
                        logger.error(f"Error processing IP WHOIS: {str(e)}", exc_info=True)
            elif isinstance(first_ip_value, str):
                # Could be IP-Domain mapping
                try:
                    logger.info(f"Detected IP-Domain Mapping format in merged data ({len(ip_keys_found)} IPs)")
                    # Extract only IP keys for processing
                    mapping_data = {ip_key: data[ip_key] for ip_key in ip_keys_found if ip_key in data}
                    result = process_ip_domain_mapping(mapping_data, graph_engine)
                    nodes_added += result.get('nodes_added', 0)
                    edges_added += result.get('edges_added', 0)
                    logger.info(f"IP-Domain Mapping: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                except Exception as e:
                    logger.error(f"Error processing IP-Domain Mapping: {str(e)}", exc_info=True)
    
    # Check for RustScan format - has data.hosts with addresses array
    if 'data' in data:
        scan_data = data.get('data', {})
        
        # RustScan: has hosts with addresses array (check structure)
        if 'hosts' in scan_data:
            hosts = scan_data.get('hosts', [])
            # Check if this is RustScan format (hosts have addresses array)
            if hosts and isinstance(hosts, list) and len(hosts) > 0:
                first_host = hosts[0] if isinstance(hosts[0], dict) else {}
                # RustScan format has addresses array in hosts
                if 'addresses' in first_host:
                    try:
                        logger.info("Detected RustScan format (individual file)")
                        result = process_rustscan(data, graph_engine)
                        nodes_added += result.get('nodes_added', 0)
                        edges_added += result.get('edges_added', 0)
                        logger.info(f"RustScan: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                    except Exception as e:
                        logger.error(f"Error processing RustScan: {str(e)}", exc_info=True)
        
        # Gobuster: has found_paths or total_found in data
        if 'found_paths' in scan_data or 'total_found' in scan_data:
            try:
                logger.info("Detected Gobuster format (individual file)")
                result = process_gobuster(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"Gobuster: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing Gobuster: {str(e)}", exc_info=True)
    
    # Check for Dig format - has queries at top level (even if mixed with other keys)
    if 'queries' in data:
        try:
            logger.info("Detected Dig format in merged data")
            # Extract just the dig data structure
            dig_data = {
                'target': data.get('target', 'unknown'),
                'queries': data.get('queries', {})
            }
            result = process_dig(dig_data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
            logger.info(f"Dig: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        except Exception as e:
            logger.error(f"Error processing Dig: {str(e)}", exc_info=True)
    
    # Check for HTTPX format - has data.enhanced.endpoints or data.results
    if 'data' in data:
        scan_data = data.get('data', {})
        if 'enhanced' in scan_data and ('endpoints' in scan_data.get('enhanced', {}) or 'technologies' in scan_data.get('enhanced', {})):
            try:
                logger.info("Detected HTTPX format (individual file)")
                result = process_httpx(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"HTTPX: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing HTTPX: {str(e)}", exc_info=True)
        elif 'technologies' in scan_data and 'enhanced' in scan_data and 'waf_detected' not in scan_data:
            try:
                logger.info("Detected WhatWeb format (individual file)")
                result = process_whatweb(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"WhatWeb: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing WhatWeb: {str(e)}", exc_info=True)
        elif 'waf_detected' in scan_data:
            try:
                logger.info("Detected WAFW00F format (individual file)")
                result = process_wafw00f(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"WAFW00F: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing WAFW00F: {str(e)}", exc_info=True)
    
    # Check for Certificate Transparency - has data.certificates
    if 'data' in data and 'certificates' in data.get('data', {}):
        try:
            logger.info("Detected Certificate Transparency format (individual file)")
            result = process_certificate_transparency(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
            logger.info(f"Certificate Transparency: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        except Exception as e:
            logger.error(f"Error processing Certificate Transparency: {str(e)}", exc_info=True)
    
    # Check for Domain WHOIS - has data.name_servers or data.registrar
    if 'data' in data:
        whois_data = data.get('data', {})
        if ('name_servers' in whois_data or 'registrar' in whois_data) and 'type' not in data:
            try:
                logger.info("Detected Domain WHOIS format (individual file)")
                result = process_whois_domain(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"Domain WHOIS: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing Domain WHOIS: {str(e)}", exc_info=True)
    
    # Check for Network Topology - has nodes and edges arrays (even if mixed with other keys)
    if 'nodes' in data and 'edges' in data:
        try:
            logger.info("Detected Network Topology format in merged data")
            # Extract just the topology data to avoid conflicts
            topology_data = {
                'nodes': data.get('nodes', []),
                'edges': data.get('edges', [])
            }
            result = process_network_topology(topology_data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
            logger.info(f"Network Topology: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        except Exception as e:
            logger.error(f"Error processing Network Topology: {str(e)}", exc_info=True)
    
    # Check for IP-Domain Mapping - simple dict with IP:domain pairs
    # Only check if we haven't processed anything yet and it looks like a simple mapping
    if isinstance(data, dict) and len(data) > 0:
        # Check if it looks like IP:domain mapping (all values are strings, keys look like IPs)
        first_key = list(data.keys())[0]
        first_value = data[first_key]
        if (isinstance(first_key, str) and 
            isinstance(first_value, str) and 
            ('.' in first_key or ':' in first_key) and
            '.' in first_value and not first_value.startswith('{')):
            try:
                logger.info("Detected IP-Domain Mapping format (individual file)")
                result = process_ip_domain_mapping(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
                logger.info(f"IP-Domain Mapping: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
            except Exception as e:
                logger.error(f"Error processing IP-Domain Mapping: {str(e)}", exc_info=True)
    
    # Check for GeoIP or IP WHOIS - dict with IPs as keys and dict values
    if isinstance(data, dict) and len(data) > 0:
        first_key = list(data.keys())[0]
        first_value = data[first_key]
        if (isinstance(first_key, str) and 
            isinstance(first_value, dict) and
            ('.' in first_key or ':' in first_key)):
            # Check if it's GeoIP (has country, city, latitude) or IP WHOIS (has org, asn, netrange)
            if 'data' in first_value:
                ip_info = first_value.get('data', {})
            else:
                ip_info = first_value
            
            if 'country' in ip_info or 'city' in ip_info or 'latitude' in ip_info:
                try:
                    logger.info("Detected GeoIP format (individual file)")
                    result = process_geoip(data, graph_engine)
                    nodes_added += result.get('nodes_added', 0)
                    edges_added += result.get('edges_added', 0)
                    logger.info(f"GeoIP: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                except Exception as e:
                    logger.error(f"Error processing GeoIP: {str(e)}", exc_info=True)
            elif 'org' in ip_info or 'asn' in ip_info or 'netrange' in ip_info:
                try:
                    logger.info("Detected IP WHOIS format (individual file)")
                    result = process_whois_ips(data, graph_engine)
                    nodes_added += result.get('nodes_added', 0)
                    edges_added += result.get('edges_added', 0)
                    logger.info(f"IP WHOIS: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                except Exception as e:
                    logger.error(f"Error processing IP WHOIS: {str(e)}", exc_info=True)
    
    # Fallback to standard format if nothing processed yet
    if nodes_added == 0 and edges_added == 0:
        try:
            logger.info("No specific format detected, trying standard format")
            result = process_standard(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
            logger.info(f"Standard format: Added {result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        except Exception as e:
            logger.error(f"Error processing standard format: {str(e)}", exc_info=True)
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed {nodes_added} nodes and {edges_added} edges'
    }

def process_standard(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process standard network format"""
    nodes_added = 0
    edges_added = 0
    
    # Process hosts
    hosts = data.get('hosts', [])
    for host in hosts:
        host_id = host.get('ip') or host.get('hostname')
        if host_id:
            graph_engine.add_node(
                host_id,
                'Host',
                {
                    'ip': host.get('ip'),
                    'hostname': host.get('hostname'),
                    'ports': host.get('ports', []),
                    **host.get('properties', {})
                }
            )
            nodes_added += 1
    
    # Process connections
    connections = data.get('connections', [])
    for conn in connections:
        source = conn.get('source')
        target = conn.get('target')
        if source and target:
            graph_engine.add_edge(
                source,
                target,
                'CONNECTS_TO',
                {
                    'protocol': conn.get('protocol', 'tcp'),
                    'port': conn.get('port'),
                    **conn.get('properties', {})
                }
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_rustscan(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process RustScan format"""
    nodes_added = 0
    edges_added = 0
    
    # Get data section (could be nested or direct)
    scan_data = data.get('data', data) if 'data' in data else data
    target = data.get('target', 'unknown')
    
    # Handle case where data might be the scan_data itself
    if not isinstance(scan_data, dict):
        return {'nodes_added': 0, 'edges_added': 0, 'error': 'Invalid RustScan data structure'}
    
    hosts = scan_data.get('hosts', [])
    
    # If hosts is empty, return early
    if not hosts or not isinstance(hosts, list):
        return {'nodes_added': 0, 'edges_added': 0, 'error': 'No hosts found in RustScan data'}
    for host in hosts:
        # Extract IP address from addresses array
        addresses = host.get('addresses', [])
        ip_address = None
        for addr in addresses:
            if addr.get('addrtype') == 'ipv4' or addr.get('addrtype') == 'ipv6':
                ip_address = addr.get('addr')
                break
        
        if not ip_address and addresses:
            ip_address = addresses[0].get('addr')
        
        if ip_address:
            # Extract ports
            ports = host.get('ports', [])
            port_list = []
            for port_info in ports:
                port_num = port_info.get('port')
                if port_num:
                    port_list.append({
                        'port': port_num,
                        'protocol': port_info.get('protocol', 'tcp'),
                        'state': port_info.get('state', 'unknown'),
                        'service': port_info.get('service', '')
                    })
            
            # Add host node
            graph_engine.add_node(
                ip_address,
                'Host',
                {
                    'ip': ip_address,
                    'target': target,
                    'ports': port_list,
                    'status': host.get('status', {}).get('state', 'unknown'),
                    'tool': 'rustscan'
                }
            )
            nodes_added += 1
            
            # Add edges for each port
            for port_info in ports:
                port_num = port_info.get('port')
                service = port_info.get('service', '')
                if port_num:
                    # Create port node
                    port_id = f"{ip_address}:{port_num}"
                    graph_engine.add_node(
                        port_id,
                        'Port',
                        {
                            'port': port_num,
                            'protocol': port_info.get('protocol', 'tcp'),
                            'state': port_info.get('state', 'open'),
                            'service': service,
                            'host': ip_address
                        }
                    )
                    nodes_added += 1
                    
                    # Connect host to port
                    graph_engine.add_edge(
                        ip_address,
                        port_id,
                        'HAS_PORT',
                        {
                            'protocol': port_info.get('protocol', 'tcp'),
                            'service': service
                        }
                    )
                    edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_gobuster(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Gobuster format"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    # Extract domain/IP from target URL
    if '://' in target:
        target = target.split('://')[1].split('/')[0]
    
    scan_data = data.get('data', {})
    found_paths = scan_data.get('found_paths', [])
    
    # Add target as a node
    if target:
        graph_engine.add_node(
            target,
            'Host',
            {
                'hostname': target,
                'tool': 'gobuster',
                'paths_found': len(found_paths),
                'total_found': scan_data.get('total_found', 0)
            }
        )
        nodes_added += 1
    
    # Add each found path as a node and connect to target
    for path in found_paths:
        if path:
            path_id = f"{target}{path}" if not path.startswith('/') else f"{target}{path}"
            graph_engine.add_node(
                path_id,
                'Path',
                {
                    'path': path,
                    'host': target,
                    'tool': 'gobuster'
                }
            )
            nodes_added += 1
            
            # Connect target to path
            graph_engine.add_edge(
                target,
                path_id,
                'HAS_PATH',
                {'tool': 'gobuster'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_dig(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Dig DNS format"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    queries = data.get('queries', {})
    
    # Add target domain as a node
    if target:
        graph_engine.add_node(
            target,
            'Domain',
            {
                'domain': target,
                'tool': 'dig'
            }
        )
        nodes_added += 1
    
    # Process each query type (A, AAAA, MX, NS, TXT, CNAME)
    for query_type, query_data in queries.items():
        if not isinstance(query_data, dict):
            continue
        
        records = query_data.get('data', {}).get('records', [])
        for record in records:
            record_value = record.get('value')
            record_type = record.get('type', query_type)
            
            if record_value:
                # Add DNS record as a node
                record_id = f"{record_value}"
                node_type = 'IP' if record_type in ['A', 'AAAA'] else 'DNS_Record'
                
                graph_engine.add_node(
                    record_id,
                    node_type,
                    {
                        'value': record_value,
                        'record_type': record_type,
                        'priority': record.get('priority'),
                        'domain': target,
                        'tool': 'dig'
                    }
                )
                nodes_added += 1
                
                # Connect domain to DNS record
                edge_type = {
                    'A': 'RESOLVES_TO',
                    'AAAA': 'RESOLVES_TO',
                    'MX': 'HAS_MX',
                    'NS': 'HAS_NS',
                    'TXT': 'HAS_TXT',
                    'CNAME': 'ALIAS_OF'
                }.get(record_type, 'HAS_RECORD')
                
                graph_engine.add_edge(
                    target,
                    record_id,
                    edge_type,
                    {
                        'record_type': record_type,
                        'priority': record.get('priority'),
                        'tool': 'dig'
                    }
                )
                edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_httpx(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process HTTPX format - HTTP probe results"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    if '://' in target:
        target = target.split('://')[1].split('/')[0]
    
    scan_data = data.get('data', {})
    enhanced = scan_data.get('enhanced', {})
    results = scan_data.get('results', [])
    endpoints = enhanced.get('endpoints', [])
    technologies = scan_data.get('technologies', []) or enhanced.get('technologies', [])
    security_headers = scan_data.get('security_headers', {}) or enhanced.get('security_headers', {})
    
    # Add target host node
    if target:
        graph_engine.add_node(
            target,
            'Host',
            {
                'hostname': target,
                'tool': 'httpx',
                'endpoints_count': len(endpoints),
                'technologies': technologies,
                'security_headers': security_headers
            }
        )
        nodes_added += 1
    
    # Process endpoints
    for endpoint in endpoints:
        if isinstance(endpoint, str):
            endpoint_url = endpoint
        elif isinstance(endpoint, dict):
            endpoint_url = endpoint.get('url', endpoint.get('endpoint', ''))
        else:
            continue
        
        if endpoint_url:
            # Extract path from URL
            if '://' in endpoint_url:
                path = '/' + '/'.join(endpoint_url.split('://')[1].split('/')[1:])
            else:
                path = endpoint_url if endpoint_url.startswith('/') else '/' + endpoint_url
            
            endpoint_id = f"{target}{path}"
            graph_engine.add_node(
                endpoint_id,
                'Endpoint',
                {
                    'url': endpoint_url,
                    'path': path,
                    'host': target,
                    'tool': 'httpx'
                }
            )
            nodes_added += 1
            
            # Connect host to endpoint
            graph_engine.add_edge(
                target,
                endpoint_id,
                'HAS_ENDPOINT',
                {'tool': 'httpx'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_whatweb(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process WhatWeb format - Web technology detection"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    if '://' in target:
        target = target.split('://')[1].split('/')[0]
    
    scan_data = data.get('data', {})
    technologies = scan_data.get('technologies', [])
    enhanced = scan_data.get('enhanced', {})
    categories = enhanced.get('categories', {})
    versions = enhanced.get('versions', {})
    
    # Add target host node with technology info
    if target:
        graph_engine.add_node(
            target,
            'Host',
            {
                'hostname': target,
                'tool': 'whatweb',
                'technologies': technologies,
                'categories': categories,
                'versions': versions
            }
        )
        nodes_added += 1
    
    # Add technology nodes
    for tech in technologies:
        if tech:
            tech_id = f"{target}:tech:{tech}"
            graph_engine.add_node(
                tech_id,
                'Technology',
                {
                    'name': tech,
                    'host': target,
                    'tool': 'whatweb'
                }
            )
            nodes_added += 1
            
            # Connect host to technology
            graph_engine.add_edge(
                target,
                tech_id,
                'USES_TECHNOLOGY',
                {'tool': 'whatweb'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_wafw00f(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process WAFW00F format - WAF detection"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    if '://' in target:
        target = target.split('://')[1].split('/')[0]
    
    scan_data = data.get('data', {})
    waf_detected = scan_data.get('waf_detected', False)
    waf_name = scan_data.get('waf_name')
    
    # Try to extract WAF name from raw output if not in data
    if waf_detected and not waf_name:
        raw_output = scan_data.get('output', '') or data.get('raw_output', '')
        # Look for WAF name in output (e.g., "is behind Kona SiteDefender (Akamai) WAF")
        import re
        match = re.search(r'is behind\s+([^(]+)', raw_output)
        if match:
            waf_name = match.group(1).strip()
        else:
            # Try alternative pattern
            match = re.search(r'behind\s+([A-Za-z0-9\s]+?)\s+WAF', raw_output)
            if match:
                waf_name = match.group(1).strip()
    
    # Add target host node with WAF info
    if target:
        graph_engine.add_node(
            target,
            'Host',
            {
                'hostname': target,
                'tool': 'wafw00f',
                'waf_detected': waf_detected,
                'waf_name': waf_name
            }
        )
        nodes_added += 1
    
    # Add WAF node if detected
    if waf_detected and waf_name:
        waf_id = f"{target}:waf:{waf_name}"
        graph_engine.add_node(
            waf_id,
            'WAF',
            {
                'name': waf_name,
                'host': target,
                'tool': 'wafw00f'
            }
        )
        nodes_added += 1
        
        # Connect host to WAF
        graph_engine.add_edge(
            target,
            waf_id,
            'PROTECTED_BY',
            {'tool': 'wafw00f'}
        )
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_geoip(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process GeoIP format - IP geolocation data"""
    nodes_added = 0
    edges_added = 0
    
    # GeoIP data is a dictionary with IP addresses as keys
    for ip_address, ip_data in data.items():
        if not isinstance(ip_data, dict):
            continue
        
        ip_info = ip_data.get('data', {}) if 'data' in ip_data else ip_data
        country = ip_info.get('country', 'Unknown')
        city = ip_info.get('city', '')
        org = ip_info.get('org', '')
        asn = ip_info.get('asn', '')
        
        # Add/update IP node with geo information
        graph_engine.add_node(
            ip_address,
            'IP',
            {
                'ip': ip_address,
                'country': country,
                'country_code': ip_info.get('country_code', ''),
                'city': city,
                'region': ip_info.get('region', ''),
                'latitude': ip_info.get('latitude'),
                'longitude': ip_info.get('longitude'),
                'org': org,
                'asn': asn,
                'isp': ip_info.get('isp', ''),
                'tool': 'geoip'
            }
        )
        nodes_added += 1
        
        # Add location node if we have city/country
        if city or country:
            location_id = f"{country}:{city}" if city else country
            graph_engine.add_node(
                location_id,
                'Location',
                {
                    'country': country,
                    'city': city,
                    'country_code': ip_info.get('country_code', ''),
                    'tool': 'geoip'
                }
            )
            nodes_added += 1
            
            # Connect IP to location
            graph_engine.add_edge(
                ip_address,
                location_id,
                'LOCATED_IN',
                {'tool': 'geoip'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_certificate_transparency(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Certificate Transparency format - SSL certificate data"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    certificates = data.get('data', {}).get('certificates', [])
    
    # Add target domain node
    if target:
        graph_engine.add_node(
            target,
            'Domain',
            {
                'domain': target,
                'tool': 'certificate_transparency',
                'certificates_count': len(certificates)
            }
        )
        nodes_added += 1
    
    # Process certificates
    for cert in certificates:
        if not isinstance(cert, dict):
            continue
        
        cert_id = cert.get('id') or cert.get('serial_number', f"cert_{nodes_added}")
        common_name = cert.get('common_name', '')
        issuer = cert.get('issuer', '')
        name = cert.get('name', '')
        
        # Create certificate node
        cert_node_id = f"{target}:cert:{cert_id}"
        graph_engine.add_node(
            cert_node_id,
            'Certificate',
            {
                'id': cert_id,
                'common_name': common_name,
                'issuer': issuer,
                'name': name,
                'serial_number': cert.get('serial_number', ''),
                'not_before': cert.get('not_before', ''),
                'not_after': cert.get('not_after', ''),
                'domain': target,
                'tool': 'certificate_transparency'
            }
        )
        nodes_added += 1
        
        # Connect domain to certificate
        graph_engine.add_edge(
            target,
            cert_node_id,
            'HAS_CERTIFICATE',
            {'tool': 'certificate_transparency'}
        )
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_whois_domain(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Domain WHOIS format"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    whois_data = data.get('data', {})
    
    # Add domain node with WHOIS info
    if target:
        graph_engine.add_node(
            target,
            'Domain',
            {
                'domain': target,
                'tool': 'whois_domain',
                'registrar': whois_data.get('registrar', ''),
                'creation_date': whois_data.get('creation_date', ''),
                'expiration_date': whois_data.get('expiration_date', ''),
                'name_servers': whois_data.get('name_servers', []),
                'status': whois_data.get('status', [])
            }
        )
        nodes_added += 1
        
        # Add name server nodes
        for ns in whois_data.get('name_servers', []):
            if ns:
                graph_engine.add_node(
                    ns,
                    'NameServer',
                    {
                        'nameserver': ns,
                        'domain': target,
                        'tool': 'whois_domain'
                    }
                )
                nodes_added += 1
                
                # Connect domain to nameserver
                graph_engine.add_edge(
                    target,
                    ns,
                    'HAS_NAMESERVER',
                    {'tool': 'whois_domain'}
                )
                edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_whois_ips(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process IP WHOIS format - dictionary with IPs as keys"""
    nodes_added = 0
    edges_added = 0
    
    for ip_address, ip_data in data.items():
        if not isinstance(ip_data, dict):
            continue
        
        whois_info = ip_data.get('data', {}) if 'data' in ip_data else ip_data
        org = whois_info.get('org', '')
        asn = whois_info.get('asn', '')
        asn_description = whois_info.get('asn_description', '')
        netrange = whois_info.get('netrange', '')
        country = whois_info.get('country', '')
        city = whois_info.get('city', '')
        
        # Add/update IP node with WHOIS information
        graph_engine.add_node(
            ip_address,
            'IP',
            {
                'ip': ip_address,
                'tool': 'whois_ips',
                'org': org,
                'asn': asn,
                'asn_description': asn_description,
                'netrange': netrange,
                'country': country,
                'city': city
            }
        )
        nodes_added += 1
        
        # Add organization node if present
        if org:
            org_id = f"org:{org}"
            graph_engine.add_node(
                org_id,
                'Organization',
                {
                    'name': org,
                    'tool': 'whois_ips'
                }
            )
            nodes_added += 1
            
            # Connect IP to organization
            graph_engine.add_edge(
                ip_address,
                org_id,
                'OWNED_BY',
                {'tool': 'whois_ips'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_network_topology(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Network Topology format - pre-built nodes and edges"""
    nodes_added = 0
    edges_added = 0
    
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    
    # Process nodes
    for node in nodes:
        if isinstance(node, dict):
            node_id = node.get('id')
            node_type = node.get('type', 'Entity')
            node_label = node.get('label', node_id)
            
            if node_id:
                graph_engine.add_node(
                    node_id,
                    node_type,
                    {
                        'label': node_label,
                        'tool': 'network_topology',
                        **{k: v for k, v in node.items() if k not in ['id', 'type', 'label']}
                    }
                )
                nodes_added += 1
    
    # Process edges
    for edge in edges:
        if isinstance(edge, dict):
            source = edge.get('from') or edge.get('source')
            target = edge.get('to') or edge.get('target')
            edge_type = edge.get('type', 'RELATED_TO')
            
            if source and target:
                graph_engine.add_edge(
                    source,
                    target,
                    edge_type,
                    {
                        'tool': 'network_topology',
                        **{k: v for k, v in edge.items() if k not in ['from', 'to', 'source', 'target', 'type']}
                    }
                )
                edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

def process_ip_domain_mapping(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process IP-Domain Mapping format - simple IP to domain mapping"""
    nodes_added = 0
    edges_added = 0
    
    # Simple format: {"ip": "domain"}
    for ip_address, domain in data.items():
        if ip_address and domain:
            # Ensure IP node exists
            graph_engine.add_node(
                ip_address,
                'IP',
                {
                    'ip': ip_address,
                    'tool': 'ip_domain_mapping'
                }
            )
            nodes_added += 1
            
            # Ensure domain node exists
            graph_engine.add_node(
                domain,
                'Domain',
                {
                    'domain': domain,
                    'tool': 'ip_domain_mapping'
                }
            )
            nodes_added += 1
            
            # Connect IP to domain
            graph_engine.add_edge(
                domain,
                ip_address,
                'RESOLVES_TO',
                {'tool': 'ip_domain_mapping'}
            )
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

