"""
Nmap Integration Plugin - Parse and visualize nmap scan results
Supports XML output from nmap scans
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import io

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process nmap XML output
    
    Expected format: Nmap XML output (as string or file content)
    """
    nodes_added = 0
    edges_added = 0
    
    # Handle string input
    if isinstance(data, str):
        xml_data = data
    elif isinstance(data, dict) and 'xml' in data:
        xml_data = data['xml']
    else:
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'Nmap data must be XML string or dict with "xml" key'
        }
    
    try:
        root = ET.fromstring(xml_data)
        
        # Parse hosts
        for host in root.findall('host'):
            # Get host address
            address_elem = host.find('address')
            if address_elem is None:
                continue
            
            host_ip = address_elem.get('addr')
            host_type = address_elem.get('addrtype', 'ipv4')
            
            # Get hostname
            hostnames = host.find('hostnames')
            hostname = None
            if hostnames is not None:
                hostname_elem = hostnames.find('hostname')
                if hostname_elem is not None:
                    hostname = hostname_elem.get('name')
            
            # Get OS detection
            os_info = None
            osmatch = host.find('os/osmatch')
            if osmatch is not None:
                os_info = osmatch.get('name')
            
            # Get status
            status = host.find('status')
            state = status.get('state') if status is not None else 'unknown'
            
            # Create host node
            host_id = hostname or host_ip
            properties = {
                'ip': host_ip,
                'hostname': hostname,
                'type': host_type,
                'os': os_info,
                'state': state,
                'ports': []
            }
            
            # Parse ports
            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_id = port.get('portid')
                    protocol = port.get('protocol', 'tcp')
                    state_elem = port.find('state')
                    port_state = state_elem.get('state') if state_elem is not None else 'unknown'
                    
                    # Get service info
                    service_elem = port.find('service')
                    service_name = None
                    service_product = None
                    service_version = None
                    if service_elem is not None:
                        service_name = service_elem.get('name')
                        service_product = service_elem.get('product')
                        service_version = service_elem.get('version')
                    
                    port_info = {
                        'port': port_id,
                        'protocol': protocol,
                        'state': port_state,
                        'service': service_name,
                        'product': service_product,
                        'version': service_version
                    }
                    properties['ports'].append(port_info)
                    
                    # Create port node if significant
                    if port_state == 'open':
                        port_node_id = f"{host_ip}:{port_id}"
                        graph_engine.add_node(
                            port_node_id,
                            'Port',
                            {
                                'port': port_id,
                                'protocol': protocol,
                                'service': service_name,
                                'product': service_product,
                                'version': service_version,
                                'host': host_ip
                            }
                        )
                        nodes_added += 1
                        
                        # Connect host to port
                        graph_engine.add_edge(
                            host_id,
                            port_node_id,
                            'HAS_PORT',
                            {'state': port_state}
                        )
                        edges_added += 1
            
            # Add host node
            graph_engine.add_node(host_id, 'Host', properties)
            nodes_added += 1
        
        return {
            'nodes_added': nodes_added,
            'edges_added': edges_added,
            'message': f'Processed nmap scan results: {nodes_added} nodes, {edges_added} edges'
        }
    
    except ET.ParseError as e:
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': f'Invalid XML format: {str(e)}'
        }
    except Exception as e:
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': f'Nmap parsing failed: {str(e)}'
        }

