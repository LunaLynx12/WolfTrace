"""
Web Reconnaissance Plugin - Processes LangChain Recon Agent output
Supports: RustScan, DNS Dig, HTTPX, Gobuster, Nikto, Nuclei, Certificate Transparency,
WHOIS, Network Topology, and all related web reconnaissance data
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process web reconnaissance data from LangChain Recon Agent
    
    Supports processing individual JSON files or merged data:
    - rustscan.json: Port scan data
    - dns_dig.json: DNS records
    - httpx.json: HTTP endpoint data
    - gobuster.json: Directory enumeration
    - nikto.json: Security scan results
    - nuclei.json: Vulnerability findings
    - certificate_transparency.json: SSL certificates
    - whois_domain.json: Domain registration info
    - network_topology.json: Pre-built graph structure
    """
    nodes_added = 0
    edges_added = 0
    
    if not isinstance(data, dict):
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'Web data must be a dictionary'
        }
    
    # Check if this is a merged format with multiple tool results
    tool_processors = {
        'rustscan': process_rustscan,
        'dns_dig': process_dns_dig,
        'httpx': process_httpx,
        'gobuster': process_gobuster,
        'nikto': process_nikto,
        'nuclei': process_nuclei,
        'certificate_transparency': process_certificate_transparency,
        'whois_domain': process_whois_domain,
        'network_topology': process_network_topology,
        'security_analysis': process_security_analysis,
        'statistics': process_statistics,
        'summary': process_summary,
        'threat_assessment': process_threat_assessment,
        'vulnerability_summary': process_vulnerability_summary,
    }
    
    # Process each tool's data if present
    for tool_name, processor_func in tool_processors.items():
        if tool_name in data:
            try:
                logger.info(f"Processing {tool_name} data")
                result = processor_func(data[tool_name], graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing {tool_name}: {str(e)}", exc_info=True)
    
    # If no tool-specific keys found, try to detect format from structure
    if nodes_added == 0 and edges_added == 0:
        # Check for metadata.json structure
        if 'tool' in data and 'LangChain Recon Agent' in str(data.get('tool', '')):
            logger.info("Detected LangChain Recon Agent metadata format")
            # This is metadata, skip processing
            return {'nodes_added': 0, 'edges_added': 0, 'message': 'Metadata file, no graph data'}
        
        # Try individual file formats
        if 'data' in data and 'hosts' in data.get('data', {}):
            # RustScan format
            try:
                result = process_rustscan(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing RustScan format: {str(e)}", exc_info=True)
        
        elif 'queries' in data:
            # DNS Dig format
            try:
                result = process_dns_dig(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing DNS Dig format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'results' in data.get('data', {}):
            # HTTPX format
            try:
                result = process_httpx(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing HTTPX format: {str(e)}", exc_info=True)
        
        elif 'nodes' in data and 'edges' in data:
            # Network topology format
            try:
                result = process_network_topology(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing network topology format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'certificates' in data.get('data', {}):
            # Certificate Transparency format
            try:
                result = process_certificate_transparency(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing Certificate Transparency format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'registrar' in data.get('data', {}):
            # WHOIS domain format
            try:
                result = process_whois_domain(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing WHOIS domain format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'paths' in data.get('data', {}):
            # Gobuster format
            try:
                result = process_gobuster(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing Gobuster format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'vulnerabilities' in data.get('data', {}):
            # Nikto format
            try:
                result = process_nikto(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing Nikto format: {str(e)}", exc_info=True)
        
        elif 'data' in data and 'findings' in data.get('data', {}):
            # Nuclei format
            try:
                result = process_nuclei(data, graph_engine)
                nodes_added += result.get('nodes_added', 0)
                edges_added += result.get('edges_added', 0)
            except Exception as e:
                logger.error(f"Error processing Nuclei format: {str(e)}", exc_info=True)
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed {nodes_added} nodes and {edges_added} edges'
    }


def process_rustscan(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process RustScan port scan data"""
    nodes_added = 0
    edges_added = 0
    target = data.get('target', 'unknown')
    
    hosts_data = data.get('data', {}).get('hosts', []) if 'data' in data else data.get('hosts', [])
    
    for host in hosts_data:
        # Extract ALL host data
        host_status = host.get('status', {})
        host_statistics = host.get('statistics', {})
        host_script_results = host.get('script_results', {})
        host_hostnames = host.get('hostnames', [])
        
        # Extract IP addresses
        addresses = host.get('addresses', [])
        for addr_info in addresses:
            ip = addr_info.get('addr')
            if ip:
                # Include ALL IP-related data
                ip_properties = {
                    'addrtype': addr_info.get('addrtype', 'ipv4'),
                    'target': target,
                    'host_status': host_status.get('state', ''),
                    'host_statistics': host_statistics,
                    'script_results': host_script_results
                }
                # Add hostnames if available
                if host_hostnames:
                    ip_properties['hostnames'] = [h.get('name', '') for h in host_hostnames if h.get('name')]
                
                graph_engine.add_node(ip, 'IP', ip_properties)
                nodes_added += 1
                
                # Link IP to target domain
                if target and target != 'unknown':
                    graph_engine.add_edge(ip, target, 'RESOLVES_TO', {})
                    edges_added += 1
        
        # Process ports - include ALL port data
        ports = host.get('ports', [])
        for port_info in ports:
            port_num = port_info.get('port')
            service = port_info.get('service', 'unknown')
            protocol = port_info.get('protocol', 'tcp')
            
            if port_num and addresses:
                ip = addresses[0].get('addr') if addresses else None
                if ip:
                    # Create port node with ALL port data
                    port_id = f"{ip}:{port_num}"
                    port_properties = {
                        'port': port_num,
                        'protocol': protocol,
                        'service': service,
                        'state': port_info.get('state', 'unknown'),
                        'version': port_info.get('version', ''),
                        'target': target
                    }
                    # Add any other port properties
                    for key, value in port_info.items():
                        if key not in ['port', 'protocol', 'service', 'state', 'version']:
                            port_properties[key] = value
                    
                    graph_engine.add_node(port_id, 'Port', port_properties)
                    nodes_added += 1
                    
                    # Link port to IP
                    graph_engine.add_edge(ip, port_id, 'HAS_PORT', {
                        'protocol': protocol,
                        'service': service
                    })
                    edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_dns_dig(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process DNS Dig records"""
    nodes_added = 0
    edges_added = 0
    target = data.get('target', 'unknown')
    
    # Add target domain
    if target and target != 'unknown':
        graph_engine.add_node(target, 'Domain', {'target': target})
        nodes_added += 1
    
    queries = data.get('queries', {})
    
    for record_type, query_data in queries.items():
        if not isinstance(query_data, dict) or 'data' not in query_data:
            continue
        
        records = query_data.get('data', {}).get('records', [])
        
        for record in records:
            domain = record.get('domain') or record.get('value') or target
            value = record.get('value') or record.get('ipv4') or record.get('ipv6')
            
            # Include ALL record data
            record_properties = {
                'record_type': record_type,
                'domain': domain,
                'ttl': record.get('ttl', ''),
                'class': record.get('class', ''),
                'target': target
            }
            # Add any other record properties
            for key, val in record.items():
                if key not in ['domain', 'value', 'ipv4', 'ipv6', 'record_type', 'ttl', 'class']:
                    record_properties[key] = val
            
            if record_type == 'A' and value:
                # A record - link domain to IP
                record_properties['ipv4'] = value
                graph_engine.add_node(value, 'IP', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, value, 'RESOLVES_TO', {'record_type': 'A', 'ttl': record.get('ttl', '')})
                    edges_added += 1
            
            elif record_type == 'AAAA' and value:
                # AAAA record
                record_properties['ipv6'] = value
                graph_engine.add_node(value, 'IP', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, value, 'RESOLVES_TO', {'record_type': 'AAAA', 'ttl': record.get('ttl', '')})
                    edges_added += 1
            
            elif record_type == 'MX' and value:
                # MX record
                mx_parts = value.split() if isinstance(value, str) else [value]
                mx_domain = mx_parts[1] if len(mx_parts) > 1 else mx_parts[0] if mx_parts else value
                priority = record.get('priority', mx_parts[0] if len(mx_parts) > 1 and mx_parts[0].isdigit() else 0)
                record_properties['priority'] = priority
                graph_engine.add_node(mx_domain, 'Domain', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, mx_domain, 'HAS_MX', {'priority': priority, 'ttl': record.get('ttl', '')})
                    edges_added += 1
            
            elif record_type == 'NS' and value:
                # NS record
                graph_engine.add_node(value, 'Domain', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, value, 'HAS_NS', {'ttl': record.get('ttl', '')})
                    edges_added += 1
            
            elif record_type == 'CNAME' and value:
                # CNAME record
                graph_engine.add_node(value, 'Domain', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, value, 'CNAME_TO', {'ttl': record.get('ttl', '')})
                    edges_added += 1
            
            elif record_type == 'TXT' and value:
                # TXT record
                txt_id = f"TXT:{domain}:{str(value)[:50]}"
                record_properties['txt_value'] = value
                graph_engine.add_node(txt_id, 'TXTRecord', record_properties)
                nodes_added += 1
                
                if domain:
                    graph_engine.add_edge(domain, txt_id, 'HAS_TXT', {'ttl': record.get('ttl', '')})
                    edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_httpx(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process HTTPX endpoint data"""
    nodes_added = 0
    edges_added = 0
    
    results = data.get('data', {}).get('results', []) if 'data' in data else data.get('results', [])
    
    for result in results:
        url = result.get('url') or result.get('final_url', '')
        if not url:
            continue
        
        # Extract domain from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.hostname
        
        # Include ALL result data
        if domain:
            domain_properties = {
                'url': url,
                'final_url': result.get('final_url', ''),
                'status_code': result.get('status_code'),
                'title': result.get('title', ''),
                'tech': result.get('tech', []) or result.get('technologies', []),
                'content_length': result.get('content_length', 0),
                'location': result.get('location', ''),
                'is_redirect': result.get('is_redirect', False)
            }
            # Add headers if available
            if 'headers' in result:
                domain_properties['headers'] = result['headers']
            # Add enhanced data if available
            if 'enhanced' in result:
                domain_properties['enhanced'] = result['enhanced']
            # Add any other properties
            for key, value in result.items():
                if key not in ['url', 'final_url', 'status_code', 'title', 'tech', 'technologies', 'content_length', 'location', 'is_redirect', 'headers', 'enhanced']:
                    domain_properties[key] = value
            
            graph_engine.add_node(domain, 'Domain', domain_properties)
            nodes_added += 1
        
        # Add endpoint as node with ALL data
        endpoint_path = parsed.path or '/'
        endpoint_id = f"{domain}{endpoint_path}"
        endpoint_properties = {
            'path': endpoint_path,
            'status_code': result.get('status_code'),
            'title': result.get('title', ''),
            'content_length': result.get('content_length', 0),
            'tech': result.get('tech', []) or result.get('technologies', []),
            'final_url': result.get('final_url', ''),
            'location': result.get('location', ''),
            'is_redirect': result.get('is_redirect', False)
        }
        # Add headers if available
        if 'headers' in result:
            endpoint_properties['headers'] = result['headers']
        # Add enhanced data if available
        if 'enhanced' in result:
            endpoint_properties['enhanced'] = result['enhanced']
        # Add any other properties
        for key, value in result.items():
            if key not in ['url', 'final_url', 'path', 'status_code', 'title', 'tech', 'technologies', 'content_length', 'location', 'is_redirect', 'headers', 'enhanced']:
                endpoint_properties[key] = value
        
        graph_engine.add_node(endpoint_id, 'Endpoint', endpoint_properties)
        nodes_added += 1
        
        # Link endpoint to domain
        if domain:
            graph_engine.add_edge(domain, endpoint_id, 'HAS_ENDPOINT', {
                'status_code': result.get('status_code')
            })
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_gobuster(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Gobuster directory enumeration data"""
    nodes_added = 0
    edges_added = 0
    
    paths = data.get('data', {}).get('paths', []) if 'data' in data else data.get('paths', [])
    target = data.get('target', '')
    
    # Extract base domain
    from urllib.parse import urlparse
    parsed = urlparse(target)
    base_domain = parsed.netloc or parsed.hostname or target
    
    if base_domain:
        graph_engine.add_node(base_domain, 'Domain', {'target': target})
        nodes_added += 1
    
    for path_info in paths:
        path = path_info.get('path', '')
        full_url = path_info.get('full_url') or path_info.get('url', '')
        
        if full_url:
            parsed_path = urlparse(full_url)
            endpoint_id = f"{parsed_path.netloc}{parsed_path.path}"
            
            # Include ALL path data
            endpoint_properties = {
                'path': path,
                'status_code': path_info.get('status_code'),
                'size': path_info.get('size', 0),
                'full_url': full_url
            }
            # Add any other properties from path_info
            for key, value in path_info.items():
                if key not in ['path', 'status_code', 'size', 'full_url', 'url']:
                    endpoint_properties[key] = value
            
            graph_engine.add_node(endpoint_id, 'Endpoint', endpoint_properties)
            nodes_added += 1
            
            if base_domain:
                graph_engine.add_edge(base_domain, endpoint_id, 'HAS_ENDPOINT', {
                    'status_code': path_info.get('status_code')
                })
                edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_nikto(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Nikto security scan data"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', '')
    vulnerabilities = data.get('data', {}).get('vulnerabilities', []) if 'data' in data else data.get('vulnerabilities', [])
    
    # Extract domain/IP from target
    from urllib.parse import urlparse
    parsed = urlparse(f"http://{target}") if not target.startswith('http') else urlparse(target)
    domain = parsed.netloc or parsed.hostname or target
    
    if domain:
        graph_engine.add_node(domain, 'Domain', {'target': target})
        nodes_added += 1
    
    # Include scan_info if available
    scan_info = data.get('data', {}).get('scan_info', {}) if 'data' in data else data.get('scan_info', {})
    
    for vuln in vulnerabilities:
        vuln_id = f"{domain}:{vuln.get('path', '/')}:{vuln.get('description', '')[:50]}"
        
        # Include ALL vulnerability data
        vuln_properties = {
            'description': vuln.get('description', ''),
            'severity': vuln.get('severity', 'info'),
            'category': vuln.get('category', ''),
            'path': vuln.get('path', '/'),
            'target': target,
            'port': data.get('port', ''),
            'ssl': data.get('ssl', False),
            'scan_info': scan_info
        }
        # Add any other vulnerability properties
        for key, value in vuln.items():
            if key not in ['description', 'severity', 'category', 'path']:
                vuln_properties[key] = value
        
        graph_engine.add_node(vuln_id, 'Vulnerability', vuln_properties)
        nodes_added += 1
        
        if domain:
            graph_engine.add_edge(domain, vuln_id, 'HAS_VULNERABILITY', {
                'severity': vuln.get('severity', 'info')
            })
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_nuclei(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Nuclei vulnerability findings"""
    nodes_added = 0
    edges_added = 0
    
    findings = data.get('data', {}).get('findings', []) if 'data' in data else data.get('findings', [])
    
    for finding in findings:
        target_url = finding.get('matched-at') or finding.get('url', '')
        if not target_url:
            continue
        
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        domain = parsed.netloc or parsed.hostname
        
        if domain:
            graph_engine.add_node(domain, 'Domain', {'target': target_url})
            nodes_added += 1
        
        info = finding.get('info', {})
        template_id = finding.get('template-id') or finding.get('template_id') or info.get('name', 'unknown')
        severity = finding.get('severity') or info.get('severity', 'info')
        
        vuln_id = f"{domain}:{template_id}"
        
        # Include ALL vulnerability data
        vuln_properties = {
            'template_id': template_id,
            'template': finding.get('template', ''),
            'template_url': finding.get('template-url', ''),
            'template_path': finding.get('template-path', ''),
            'name': info.get('name', ''),
            'severity': severity,
            'description': info.get('description', ''),
            'tags': info.get('tags', []),
            'author': info.get('author', []),
            'reference': info.get('reference', []),
            'matched_at': finding.get('matched-at', ''),
            'extracted_results': finding.get('extracted-results', []),
            'ip': finding.get('ip', ''),
            'host': finding.get('host', ''),
            'port': finding.get('port', ''),
            'scheme': finding.get('scheme', ''),
            'url': finding.get('url', ''),
            'type': finding.get('type', ''),
            'timestamp': finding.get('timestamp', '')
        }
        # Extract classification data properly (CVSS, CVE, CWE)
        if 'classification' in info:
            classification = info['classification']
            vuln_properties['cve_id'] = classification.get('cve-id')
            vuln_properties['cwe_id'] = classification.get('cwe-id', [])
            vuln_properties['cvss_metrics'] = classification.get('cvss-metrics', '')
            # Also keep full classification object
            vuln_properties['classification'] = classification
        # Add metadata
        if 'metadata' in info:
            vuln_properties['metadata'] = info['metadata']
        # Add request/response if available (truncate if too long)
        if 'request' in finding:
            request_data = finding['request']
            vuln_properties['request'] = request_data[:1000] if len(str(request_data)) > 1000 else request_data
        if 'response' in finding:
            response_data = finding['response']
            vuln_properties['response'] = response_data[:1000] if len(str(response_data)) > 1000 else response_data
        
        graph_engine.add_node(vuln_id, 'Vulnerability', vuln_properties)
        nodes_added += 1
        
        if domain:
            graph_engine.add_edge(domain, vuln_id, 'HAS_VULNERABILITY', {
                'severity': severity,
                'template_id': template_id
            })
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_certificate_transparency(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process Certificate Transparency data"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', '')
    certificates = data.get('data', {}).get('certificates', []) if 'data' in data else data.get('certificates', [])
    
    for cert in certificates:
        common_name = cert.get('common_name') or cert.get('name', '').split('\n')[0] if cert.get('name') else ''
        if not common_name:
            continue
        
        # Extract domain from common name (handle wildcards)
        domain = common_name.replace('*.', '') if common_name.startswith('*.') else common_name
        
        # Include ALL certificate data
        cert_properties = {
            'certificate': True,
            'issuer': cert.get('issuer', ''),
            'not_before': cert.get('not_before', ''),
            'not_after': cert.get('not_after', ''),
            'serial_number': cert.get('serial_number', ''),
            'common_name': common_name,
            'target': target
        }
        # Add any other certificate properties
        for key, value in cert.items():
            if key not in ['issuer', 'not_before', 'not_after', 'serial_number', 'common_name', 'name']:
                cert_properties[key] = value
        
        graph_engine.add_node(domain, 'Domain', cert_properties)
        nodes_added += 1
        
        # Link certificate to target if different
        if target and target != domain:
            graph_engine.add_edge(target, domain, 'HAS_CERTIFICATE', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_whois_domain(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process WHOIS domain data"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', '')
    whois_data = data.get('data', {}) if 'data' in data else data
    
    if target:
        # Include ALL WHOIS data
        whois_properties = {
            'registrar': whois_data.get('registrar', ''),
            'creation_date': whois_data.get('creation_date', ''),
            'expiration_date': whois_data.get('expiration_date', ''),
            'updated_date': whois_data.get('updated_date', ''),
            'status': whois_data.get('status', []),
            'target': target
        }
        # Add any other WHOIS properties
        for key, value in whois_data.items():
            if key not in ['registrar', 'creation_date', 'expiration_date', 'updated_date', 'status', 'name_servers']:
                whois_properties[key] = value
        
        graph_engine.add_node(target, 'Domain', whois_properties)
        nodes_added += 1
        
        # Add name servers
        name_servers = whois_data.get('name_servers', [])
        for ns in name_servers:
            graph_engine.add_node(ns, 'Domain', {'type': 'nameserver'})
            nodes_added += 1
            graph_engine.add_edge(target, ns, 'HAS_NS', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_network_topology(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process pre-built network topology graph"""
    nodes_added = 0
    edges_added = 0
    
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    
    # Add nodes
    for node in nodes:
        node_id = node.get('id')
        node_type = node.get('type', 'Entity')
        properties = {k: v for k, v in node.items() if k not in ['id', 'type']}
        
        if node_id:
            graph_engine.add_node(node_id, node_type, properties)
            nodes_added += 1
    
    # Add edges
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        edge_type = edge.get('type', 'RELATED_TO')
        properties = {k: v for k, v in edge.items() if k not in ['source', 'target', 'type']}
        
        if source and target:
            graph_engine.add_edge(source, target, edge_type, properties)
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_security_analysis(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process security analysis data - creates AI node and links to vulnerabilities"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target') or data.get('security_analysis', {}).get('target', '')
    security_data = data.get('security_analysis', {}) if 'security_analysis' in data else data
    analysis = security_data.get('analysis', {})
    
    # Create AI Analysis node
    ai_node_id = f"AI_Analysis:{target}" if target else "AI_Analysis"
    
    # Include ALL security analysis data
    ai_properties = {
        'target': target,
        'full_analysis': analysis.get('full_analysis', ''),
        'raw_ai_response': security_data.get('raw_ai_response', ''),
        'threat_indicators': analysis.get('threat_indicators', {}),
        'risk_assessment': analysis.get('risk_assessment', {}),
        'recommendations': analysis.get('recommendations', {}),
        'structured_findings': analysis.get('structured_findings', {})
    }
    # Add any other properties
    for key, value in security_data.items():
        if key not in ['target', 'analysis', 'raw_ai_response']:
            ai_properties[key] = value
    
    graph_engine.add_node(ai_node_id, 'AI', ai_properties)
    nodes_added += 1
    
    # Link AI node to target domain
    if target:
        graph_engine.add_node(target, 'Domain', {'target': target})
        nodes_added += 1
        graph_engine.add_edge(ai_node_id, target, 'ANALYZES', {})
        edges_added += 1
    
    # Process vulnerabilities and link them to AI node
    vulnerabilities = analysis.get('vulnerabilities', [])
    for vuln in vulnerabilities:
        finding = vuln.get('finding', '')
        if finding:
            # Create vulnerability node from finding
            vuln_id = f"Vuln:{target}:{finding[:50]}" if target else f"Vuln:{finding[:50]}"
            vuln_properties = {
                'finding': finding,
                'extracted': vuln.get('extracted', False),
                'target': target,
                'source': 'AI_Analysis'
            }
            graph_engine.add_node(vuln_id, 'Vulnerability', vuln_properties)
            nodes_added += 1
            
            # Link AI to vulnerability
            graph_engine.add_edge(ai_node_id, vuln_id, 'IDENTIFIED_VULNERABILITY', {})
            edges_added += 1
            
            # Link vulnerability to target if available
            if target:
                graph_engine.add_edge(vuln_id, target, 'AFFECTS', {})
                edges_added += 1
    
    # Process structured findings (ports, services, etc.)
    structured = analysis.get('structured_findings', {})
    open_ports = structured.get('open_ports', [])
    for port_info in open_ports:
        port_num = port_info.get('port')
        if port_num and target:
            # Link ports to target
            port_id = f"{target}:{port_num}"
            graph_engine.add_node(port_id, 'Port', {
                'port': port_num,
                'protocol': port_info.get('protocol', 'tcp'),
                'service': port_info.get('service', ''),
                'version': port_info.get('version', ''),
                'source': 'AI_Analysis'
            })
            nodes_added += 1
            graph_engine.add_edge(ai_node_id, port_id, 'IDENTIFIED_PORT', {})
            edges_added += 1
            graph_engine.add_edge(port_id, target, 'EXPOSED_ON', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_statistics(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process scan statistics data"""
    nodes_added = 0
    edges_added = 0
    
    # Extract target from various possible locations
    target = data.get('target', '')
    if not target and 'scan_summary' in data:
        # Try to infer from statistics
        target = 'scan_statistics'
    
    if target:
        # Include ALL statistics data
        stats_properties = {
            'target': target,
            'scan_summary': data.get('scan_summary', {}),
            'dns_statistics': data.get('dns_statistics', {}),
            'port_statistics': data.get('port_statistics', {}),
            'service_statistics': data.get('service_statistics', {})
        }
        # Add any other properties
        for key, value in data.items():
            if key not in ['target', 'scan_summary', 'dns_statistics', 'port_statistics', 'service_statistics']:
                stats_properties[key] = value
        
        graph_engine.add_node(target, 'Domain', stats_properties)
        nodes_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_summary(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process scan summary data"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', '')
    
    if target:
        # Include ALL summary data
        summary_properties = {
            'target': target,
            'scan_date': data.get('scan_date', ''),
            'tools_executed': data.get('tools_executed', []),
            'scan_results': data.get('scan_results', {}),
            'security_findings': data.get('security_findings', {}),
            'ai_analysis_performed': data.get('ai_analysis_performed', False),
            'report_files': data.get('report_files', [])
        }
        # Add any other properties
        for key, value in data.items():
            if key not in ['target', 'scan_date', 'tools_executed', 'scan_results', 'security_findings', 'ai_analysis_performed', 'report_files']:
                summary_properties[key] = value
        
        graph_engine.add_node(target, 'Domain', summary_properties)
        nodes_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_threat_assessment(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process threat assessment data"""
    nodes_added = 0
    edges_added = 0
    
    # Threat assessment might not have a direct target, create a summary node
    threat_id = 'threat_assessment'
    
    # Include ALL threat assessment data
    threat_properties = {
        'dangerous_ips': data.get('dangerous_ips', []),
        'suspicious_ports': data.get('suspicious_ports', []),
        'risk_score': data.get('risk_score', 0),
        'threat_indicators': data.get('threat_indicators', []),
        'recommendations': data.get('recommendations', [])
    }
    # Add any other properties
    for key, value in data.items():
        if key not in ['dangerous_ips', 'suspicious_ports', 'risk_score', 'threat_indicators', 'recommendations']:
            threat_properties[key] = value
    
    graph_engine.add_node(threat_id, 'ThreatAssessment', threat_properties)
    nodes_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_vulnerability_summary(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process vulnerability summary data"""
    nodes_added = 0
    edges_added = 0
    
    # Vulnerability summary might not have a direct target, create a summary node
    vuln_summary_id = 'vulnerability_summary'
    
    # Include ALL vulnerability summary data
    vuln_summary_properties = {
        'total_vulnerabilities': data.get('total_vulnerabilities', 0),
        'by_severity': data.get('by_severity', {}),
        'vulnerable_services': data.get('vulnerable_services', []),
        'vulnerabilities': data.get('vulnerabilities', []),
        'risk_assessment': data.get('risk_assessment', {})
    }
    # Add any other properties
    for key, value in data.items():
        if key not in ['total_vulnerabilities', 'by_severity', 'vulnerable_services', 'vulnerabilities', 'risk_assessment']:
            vuln_summary_properties[key] = value
    
    graph_engine.add_node(vuln_summary_id, 'VulnerabilitySummary', vuln_summary_properties)
    nodes_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}

