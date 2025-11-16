"""
Network Topology Plugin - Processes network scan data
"""
from typing import Dict, Any, List

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process network topology data
    
    Expected format:
    {
        "hosts": [
            {"ip": "192.168.1.1", "hostname": "router", "ports": [80, 443]},
            ...
        ],
        "connections": [
            {"source": "192.168.1.1", "target": "192.168.1.2", "protocol": "tcp", "port": 22}
        ]
    }
    """
    nodes_added = 0
    edges_added = 0
    
    if isinstance(data, dict):
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
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'message': f'Processed {nodes_added} hosts and {edges_added} connections'
    }

