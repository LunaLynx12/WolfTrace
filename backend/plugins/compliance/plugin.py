"""
Compliance Plugin - Processes Alina Compliance Agent output
Supports: GDPR, ISO 27001, and other EU-compliant standards
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process compliance data from Alina Compliance Agent
    
    Supports processing individual JSON files or merged data:
    - metadata.json: Agent metadata and configuration
    - compliance_checks.json: Compliance check results
    - standards.json: Standards being checked
    - system_config.json: System configuration scan results
    - firewall_rules.json: Firewall rules with compliance status
    """
    nodes_added = 0
    edges_added = 0
    
    if not isinstance(data, dict):
        return {
            'nodes_added': 0,
            'edges_added': 0,
            'error': 'Compliance data must be a dictionary'
        }
    
    # Check if this is a merged format with multiple files
    processors = {
        'metadata': process_metadata,
        'compliance_checks': process_compliance_checks,
        'standards': process_standards,
        'system_config': process_system_config,
        'firewall_rules': process_firewall_rules,
        'processes_data': process_processes,
        'filespermissions_data': process_file_permissions,
        'container_data': process_containers,
        'secrets_data': process_secrets,
        'software_data': process_software,
        'systeminfo_data': process_system_info,
        'users_data': process_users
    }
    
    # Process each file type if present
    for key, processor_func in processors.items():
        if key in data:
            result = processor_func(data[key], graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
    
    # If data is at root level (single file), try to detect type
    if nodes_added == 0:
        if 'agent_type' in data or 'tool' in data:
            result = process_metadata(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'compliance_results' in data or 'checks' in data:
            result = process_compliance_checks(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'standards' in data:
            result = process_standards(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'system_info' in data:
            result = process_system_config(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'firewall_type' in data or 'rules' in data:
            result = process_firewall_rules(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'running_processes' in data:
            result = process_processes(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'suid_files' in data or 'sgid_files' in data or 'world_writable_files' in data:
            result = process_file_permissions(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'in_container' in data or 'docker_info' in data:
            result = process_containers(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'passwords' in data or 'api_keys' in data or 'tokens' in data:
            result = process_secrets(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'installed_packages' in data:
            result = process_software(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'os_info' in data or 'kernel_info' in data:
            result = process_system_info(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
        elif 'current_user' in data or 'sudo_config' in data:
            result = process_users(data, graph_engine)
            nodes_added += result.get('nodes_added', 0)
            edges_added += result.get('edges_added', 0)
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added
    }


def process_metadata(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process metadata.json"""
    nodes_added = 0
    edges_added = 0
    
    tool = data.get('tool', 'Alina Compliance Agent')
    target_cloud = data.get('target_cloud', 'unknown')
    standards = data.get('standards_checked', [])
    
    # Create agent node
    agent_id = f"Agent:{tool}"
    agent_properties = {
        'tool': tool,
        'version': data.get('version', ''),
        'agent_type': data.get('agent_type', 'compliance'),
        'target_cloud': target_cloud,
        'scan_types': data.get('scan_types', []),
        'standards_checked': standards,
        'generated_at': data.get('generated_at', '')
    }
    graph_engine.add_node(agent_id, 'Agent', agent_properties)
    nodes_added += 1
    
    # Link to cloud/system
    if target_cloud and target_cloud != 'unknown':
        system_id = f"System:{target_cloud}"
        graph_engine.add_node(system_id, 'System', {'name': target_cloud, 'cloud_provider': target_cloud})
        nodes_added += 1
        graph_engine.add_edge(agent_id, system_id, 'SCANS', {})
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_compliance_checks(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process compliance_checks.json"""
    nodes_added = 0
    edges_added = 0
    
    target = data.get('target', 'unknown')
    cloud_provider = data.get('cloud_provider', 'unknown')
    compliance_results = data.get('compliance_results', {})
    checks = data.get('checks', [])
    
    # Create system node
    system_id = f"System:{target}"
    system_properties = {
        'name': target,
        'cloud_provider': cloud_provider,
        'scan_date': data.get('scan_date', ''),
        'compliance_score': compliance_results.get('compliance_score', 0),
        'total_checks': compliance_results.get('total_checks', 0),
        'passed': compliance_results.get('passed', 0),
        'failed': compliance_results.get('failed', 0),
        'warnings': compliance_results.get('warnings', 0)
    }
    graph_engine.add_node(system_id, 'System', system_properties)
    nodes_added += 1
    
    # Process each compliance check
    for check in checks:
        check_id = check.get('id', f"Check:{target}:{len(checks)}")
        standard = check.get('standard', 'Unknown')
        status = check.get('status', 'unknown')
        category = check.get('category', '')
        
        # Create compliance check node
        check_properties = {
            'check_name': check.get('check_name', ''),
            'standard': standard,
            'category': category,
            'status': status,
            'compliance_status': status,  # Also set compliance_status for color coding
            'severity': check.get('severity', 'medium'),
            'description': check.get('description', ''),
            'details': check.get('details', {}),
            'remediation': check.get('remediation', '')
        }
        graph_engine.add_node(check_id, 'ComplianceCheck', check_properties)
        nodes_added += 1
        
        # Link check to system
        graph_engine.add_edge(system_id, check_id, 'HAS_CHECK', {
            'status': status,
            'severity': check.get('severity', 'medium')
        })
        edges_added += 1
        
        # Create standard node and link
        standard_id = f"Standard:{standard}"
        graph_engine.add_node(standard_id, 'Standard', {
            'name': standard,
            'region': 'EU' if 'GDPR' in standard else 'International'
        })
        nodes_added += 1
        
        graph_engine.add_edge(check_id, standard_id, 'CHECKS_STANDARD', {})
        edges_added += 1
        
        # Link system to standard
        graph_engine.add_edge(system_id, standard_id, 'MUST_COMPLY', {})
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_standards(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process standards.json"""
    nodes_added = 0
    edges_added = 0
    
    standards = data.get('standards', [])
    
    for standard in standards:
        standard_id = standard.get('id', '')
        if not standard_id:
            continue
        
        standard_node_id = f"Standard:{standard_id}"
        standard_properties = {
            'name': standard.get('name', ''),
            'id': standard_id,
            'region': standard.get('region', ''),
            'version': standard.get('version', ''),
            'description': standard.get('description', ''),
            'categories': standard.get('categories', [])
        }
        graph_engine.add_node(standard_node_id, 'Standard', standard_properties)
        nodes_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_system_config(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process system_config.json"""
    nodes_added = 0
    edges_added = 0
    
    system_info = data.get('system_info', {})
    hostname = system_info.get('hostname', 'unknown')
    cloud_provider = system_info.get('cloud_provider', 'unknown')
    
    # Create system node
    system_id = f"System:{hostname}"
    system_properties = {
        'hostname': hostname,
        'os': system_info.get('os', ''),
        'os_version': system_info.get('os_version', ''),
        'cloud_provider': cloud_provider,
        'instance_type': system_info.get('instance_type', ''),
        'region': system_info.get('region', ''),
        'scan_date': data.get('scan_date', '')
    }
    graph_engine.add_node(system_id, 'System', system_properties)
    nodes_added += 1
    
    # Process configurations
    configurations = data.get('configurations', {})
    for config_type, config_data in configurations.items():
        config_id = f"Config:{hostname}:{config_type}"
        config_properties = {
            'type': config_type,
            'system': hostname,
            **config_data
        }
        graph_engine.add_node(config_id, 'Configuration', config_properties)
        nodes_added += 1
        
        # Link config to system
        graph_engine.add_edge(system_id, config_id, 'HAS_CONFIG', {
            'config_type': config_type
        })
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_firewall_rules(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process firewall_rules.json - firewall rules with compliance status"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    firewall_type = data.get('firewall_type', 'unknown')
    rules = data.get('rules', [])
    compliance_summary = data.get('compliance_summary', {})
    
    # Create firewall node
    firewall_id = f"Firewall:{host}"
    firewall_properties = {
        'host': host,
        'firewall_type': firewall_type,
        'scan_date': data.get('scan_date', ''),
        'total_rules': compliance_summary.get('total_rules', len(rules)),
        'passed': compliance_summary.get('passed', 0),
        'failed': compliance_summary.get('failed', 0),
        'compliance_score': compliance_summary.get('compliance_score', 0),
        'default_policy': data.get('default_policy', {})
    }
    graph_engine.add_node(firewall_id, 'Firewall', firewall_properties)
    nodes_added += 1
    
    # Link firewall to system
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host})
    nodes_added += 1
    graph_engine.add_edge(system_id, firewall_id, 'HAS_FIREWALL', {})
    edges_added += 1
    
    # Process each firewall rule
    for rule in rules:
        rule_id = rule.get('id', f"Rule:{host}:{len(rules)}")
        compliance_status = rule.get('compliance_status', 'unknown')
        standard = rule.get('standard', 'Unknown')
        check_id = rule.get('check_id', '')
        
        # Create firewall rule node with compliance status
        rule_properties = {
            'chain': rule.get('chain', ''),
            'protocol': rule.get('protocol', ''),
            'port': rule.get('port', ''),
            'source': rule.get('source', ''),
            'action': rule.get('action', ''),
            'description': rule.get('description', ''),
            'compliance_status': compliance_status,  # 'passed' or 'failed' - used for color coding
            'status': compliance_status,  # Also set status for compatibility
            'standard': standard,
            'check_id': check_id,
            'reason': rule.get('reason', ''),
            'remediation': rule.get('remediation', '')
        }
        graph_engine.add_node(rule_id, 'FirewallRule', rule_properties)
        nodes_added += 1
        
        # Link rule to firewall
        graph_engine.add_edge(firewall_id, rule_id, 'HAS_RULE', {
            'compliance_status': compliance_status
        })
        edges_added += 1
        
        # Link rule to standard if available
        if standard and standard != 'Unknown':
            standard_id = f"Standard:{standard}"
            graph_engine.add_node(standard_id, 'Standard', {
                'name': standard,
                'region': 'EU' if 'GDPR' in standard else 'International'
            })
            nodes_added += 1
            graph_engine.add_edge(rule_id, standard_id, 'CHECKS_STANDARD', {
                'compliance_status': compliance_status
            })
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_processes(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process processes_data.json - running processes"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    processes = data.get('running_processes', [])
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host, 'scan_date': data.get('scan_date', '')})
    nodes_added += 1
    
    # Process each running process
    for proc in processes:
        pid = proc.get('pid', '')
        proc_id = f"Process:{host}:{pid}"
        
        proc_properties = {
            'pid': pid,
            'user': proc.get('user', ''),
            'command': proc.get('command', ''),
            'cpu': proc.get('cpu', ''),
            'mem': proc.get('mem', ''),
            'vsz': proc.get('vsz', ''),
            'rss': proc.get('rss', ''),
            'tty': proc.get('tty', ''),
            'stat': proc.get('stat', ''),
            'start': proc.get('start', ''),
            'time': proc.get('time', '')
        }
        graph_engine.add_node(proc_id, 'Process', proc_properties)
        nodes_added += 1
        
        # Link process to system
        graph_engine.add_edge(system_id, proc_id, 'HAS_PROCESS', {})
        edges_added += 1
        
        # Link process to user if available
        if proc.get('user'):
            user_id = f"User:{host}:{proc.get('user')}"
            graph_engine.add_node(user_id, 'User', {'username': proc.get('user'), 'host': host})
            nodes_added += 1
            graph_engine.add_edge(user_id, proc_id, 'RUNS_PROCESS', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_file_permissions(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process filespermissions_data.json - file permissions (SUID, SGID, world-writable)"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    suid_files = data.get('suid_files', [])
    sgid_files = data.get('sgid_files', [])
    world_writable_files = data.get('world_writable_files', [])
    writable_files = data.get('writable_files', [])
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host, 'scan_date': data.get('scan_date', '')})
    nodes_added += 1
    
    # Process SUID files
    for file_path in suid_files:
        file_id = f"File:{host}:{file_path}"
        file_properties = {
            'path': file_path,
            'permission_type': 'SUID',
            'compliance_status': 'failed',  # SUID files are often security risks
            'status': 'failed',
            'risk_level': 'high'
        }
        graph_engine.add_node(file_id, 'File', file_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, file_id, 'HAS_FILE', {'permission_type': 'SUID'})
        edges_added += 1
    
    # Process SGID files
    for file_path in sgid_files:
        file_id = f"File:{host}:{file_path}"
        file_properties = {
            'path': file_path,
            'permission_type': 'SGID',
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'high'
        }
        graph_engine.add_node(file_id, 'File', file_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, file_id, 'HAS_FILE', {'permission_type': 'SGID'})
        edges_added += 1
    
    # Process world-writable files
    for file_path in world_writable_files:
        file_id = f"File:{host}:{file_path}"
        file_properties = {
            'path': file_path,
            'permission_type': 'world_writable',
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'medium'
        }
        graph_engine.add_node(file_id, 'File', file_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, file_id, 'HAS_FILE', {'permission_type': 'world_writable'})
        edges_added += 1
    
    # Process writable files (lower risk)
    for file_path in writable_files:
        file_id = f"File:{host}:{file_path}"
        file_properties = {
            'path': file_path,
            'permission_type': 'writable',
            'compliance_status': 'passed',
            'status': 'passed',
            'risk_level': 'low'
        }
        graph_engine.add_node(file_id, 'File', file_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, file_id, 'HAS_FILE', {'permission_type': 'writable'})
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_containers(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process container_data.json - Docker/container information"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    in_container = data.get('in_container', False)
    container_type = data.get('container_type', '')
    docker_info = data.get('docker_info', {})
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {
        'name': host,
        'in_container': in_container,
        'container_type': container_type,
        'scan_date': data.get('scan_date', '')
    })
    nodes_added += 1
    
    # Process Docker info if available
    if docker_info.get('docker_socket_accessible'):
        docker_id = f"Docker:{host}"
        docker_properties = {
            'host': host,
            'docker_version': docker_info.get('docker_version', ''),
            'socket_accessible': docker_info.get('docker_socket_accessible', False),
            'compliance_status': 'failed' if docker_info.get('docker_socket_accessible') else 'passed',
            'status': 'failed' if docker_info.get('docker_socket_accessible') else 'passed'
        }
        graph_engine.add_node(docker_id, 'Docker', docker_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, docker_id, 'HAS_DOCKER', {})
        edges_added += 1
        
        # Process Docker images
        for image in docker_info.get('docker_images', []):
            image_id = f"Image:{host}:{image.get('repository', 'unknown')}:{image.get('tag', 'latest')}"
            image_properties = {
                'repository': image.get('repository', ''),
                'tag': image.get('tag', ''),
                'image_id': image.get('image_id', ''),
                'host': host
            }
            graph_engine.add_node(image_id, 'DockerImage', image_properties)
            nodes_added += 1
            graph_engine.add_edge(docker_id, image_id, 'HAS_IMAGE', {})
            edges_added += 1
        
        # Process Docker containers
        for container in docker_info.get('docker_containers', []):
            container_id = f"Container:{host}:{container.get('id', 'unknown')}"
            container_properties = {
                'id': container.get('id', ''),
                'name': container.get('name', ''),
                'image': container.get('image', ''),
                'status': container.get('status', ''),
                'host': host
            }
            graph_engine.add_node(container_id, 'Container', container_properties)
            nodes_added += 1
            graph_engine.add_edge(docker_id, container_id, 'HAS_CONTAINER', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_secrets(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process secrets_data.json - passwords, API keys, tokens"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    passwords = data.get('passwords', [])
    api_keys = data.get('api_keys', [])
    tokens = data.get('tokens', [])
    aws_credentials = data.get('aws_credentials', [])
    ssh_keys = data.get('ssh_keys', [])
    database_credentials = data.get('database_credentials', [])
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host, 'scan_date': data.get('scan_date', '')})
    nodes_added += 1
    
    # Process passwords
    for pwd in passwords:
        secret_id = f"Secret:{host}:password:{pwd.get('file', 'unknown')}:{pwd.get('line_number', '')}"
        secret_properties = {
            'type': 'password',
            'file': pwd.get('file', ''),
            'line_number': pwd.get('line_number', ''),
            'match_preview': pwd.get('match_preview', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'critical'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'password'})
        edges_added += 1
    
    # Process API keys
    for key in api_keys:
        secret_id = f"Secret:{host}:api_key:{key.get('file', 'unknown')}:{key.get('line_number', '')}"
        secret_properties = {
            'type': 'api_key',
            'file': key.get('file', ''),
            'line_number': key.get('line_number', ''),
            'match_preview': key.get('match_preview', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'critical'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'api_key'})
        edges_added += 1
    
    # Process tokens
    for token in tokens:
        secret_id = f"Secret:{host}:token:{token.get('file', 'unknown')}:{token.get('line_number', '')}"
        secret_properties = {
            'type': 'token',
            'file': token.get('file', ''),
            'line_number': token.get('line_number', ''),
            'match_preview': token.get('match_preview', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'critical'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'token'})
        edges_added += 1
    
    # Process AWS credentials
    for cred in aws_credentials:
        secret_id = f"Secret:{host}:aws:{cred.get('file', 'unknown')}:{cred.get('line_number', '')}"
        secret_properties = {
            'type': 'aws_credentials',
            'file': cred.get('file', ''),
            'line_number': cred.get('line_number', ''),
            'match_preview': cred.get('match_preview', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'critical'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'aws_credentials'})
        edges_added += 1
    
    # Process SSH keys
    for key in ssh_keys:
        secret_id = f"Secret:{host}:ssh_key:{key.get('file', 'unknown')}"
        secret_properties = {
            'type': 'ssh_key',
            'file': key.get('file', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'high'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'ssh_key'})
        edges_added += 1
    
    # Process database credentials
    for cred in database_credentials:
        secret_id = f"Secret:{host}:db:{cred.get('file', 'unknown')}:{cred.get('line_number', '')}"
        secret_properties = {
            'type': 'database_credentials',
            'file': cred.get('file', ''),
            'line_number': cred.get('line_number', ''),
            'match_preview': cred.get('match_preview', ''),
            'compliance_status': 'failed',
            'status': 'failed',
            'risk_level': 'critical'
        }
        graph_engine.add_node(secret_id, 'Secret', secret_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, secret_id, 'HAS_SECRET', {'type': 'database_credentials'})
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_software(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process software_data.json - installed packages"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    installed_packages = data.get('installed_packages', {})
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host, 'scan_date': data.get('scan_date', '')})
    nodes_added += 1
    
    # Process packages by package manager
    for pkg_manager, packages in installed_packages.items():
        for pkg in packages:
            pkg_id = f"Package:{host}:{pkg.get('name', 'unknown')}"
            pkg_properties = {
                'name': pkg.get('name', ''),
                'version': pkg.get('version', ''),
                'package_manager': pkg_manager,
                'host': host
            }
            graph_engine.add_node(pkg_id, 'Package', pkg_properties)
            nodes_added += 1
            graph_engine.add_edge(system_id, pkg_id, 'HAS_PACKAGE', {'package_manager': pkg_manager})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_system_info(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process systeminfo_data.json - system information"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    os_info = data.get('os_info', {})
    kernel_info = data.get('kernel_info', {})
    
    # Create system node with all OS info
    system_id = f"System:{host}"
    system_properties = {
        'name': host,
        'scan_date': data.get('scan_date', ''),
        'os': os_info.get('system', ''),
        'os_release': os_info.get('release', ''),
        'os_version': os_info.get('version', ''),
        'machine': os_info.get('machine', ''),
        'processor': os_info.get('processor', ''),
        'platform': os_info.get('platform', ''),
        'kernel_release': kernel_info.get('kernel_release', ''),
        'kernel_version': kernel_info.get('kernel_version', ''),
        'loaded_modules_count': kernel_info.get('loaded_modules_count', 0)
    }
    
    # Add OS release details
    os_release = os_info.get('os_release', {})
    if os_release:
        system_properties.update({
            'os_name': os_release.get('NAME', ''),
            'os_pretty_name': os_release.get('PRETTY_NAME', ''),
            'os_version_id': os_release.get('VERSION_ID', ''),
            'os_id': os_release.get('ID', ''),
            'os_id_like': os_release.get('ID_LIKE', '')
        })
    
    graph_engine.add_node(system_id, 'System', system_properties)
    nodes_added += 1
    
    # Process loaded kernel modules
    for module in kernel_info.get('loaded_modules', []):
        module_id = f"Module:{host}:{module}"
        graph_engine.add_node(module_id, 'KernelModule', {'name': module, 'host': host})
        nodes_added += 1
        graph_engine.add_edge(system_id, module_id, 'HAS_MODULE', {})
        edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}


def process_users(data: Dict[str, Any], graph_engine) -> Dict[str, Any]:
    """Process users_data.json - user accounts and sudo configuration"""
    nodes_added = 0
    edges_added = 0
    
    host = data.get('host', 'unknown')
    current_user = data.get('current_user', {})
    sudo_config = data.get('sudo_config', {})
    doas_config = data.get('doas_config', {})
    pkexec_polkit = data.get('pkexec_polkit', {})
    
    # Create system node
    system_id = f"System:{host}"
    graph_engine.add_node(system_id, 'System', {'name': host, 'scan_date': data.get('scan_date', '')})
    nodes_added += 1
    
    # Process current user
    if current_user:
        user_id = f"User:{host}:{current_user.get('username', 'unknown')}"
        user_properties = {
            'username': current_user.get('username', ''),
            'uid': current_user.get('uid', ''),
            'gid': current_user.get('gid', ''),
            'home': current_user.get('home', ''),
            'shell': current_user.get('shell', ''),
            'is_root': current_user.get('is_root', False),
            'host': host
        }
        graph_engine.add_node(user_id, 'User', user_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, user_id, 'HAS_USER', {})
        edges_added += 1
        
        # Process user groups
        for group in current_user.get('groups', []):
            group_id = f"Group:{host}:{group}"
            graph_engine.add_node(group_id, 'Group', {'name': group, 'host': host})
            nodes_added += 1
            graph_engine.add_edge(user_id, group_id, 'MEMBER_OF', {})
            edges_added += 1
    
    # Process sudo configuration
    if sudo_config:
        sudo_id = f"SudoConfig:{host}"
        sudo_properties = {
            'host': host,
            'sudoers_file': sudo_config.get('sudoers_file', []),
            'sudoers_d_files': sudo_config.get('sudoers_d_files', [])
        }
        graph_engine.add_node(sudo_id, 'SudoConfig', sudo_properties)
        nodes_added += 1
        graph_engine.add_edge(system_id, sudo_id, 'HAS_SUDO_CONFIG', {})
        edges_added += 1
    
    # Process polkit policies
    if pkexec_polkit and pkexec_polkit.get('polkit_policies'):
        for policy in pkexec_polkit.get('polkit_policies', []):
            policy_id = f"Policy:{host}:{policy.get('file', 'unknown')}"
            policy_properties = {
                'file': policy.get('file', ''),
                'type': policy.get('type', ''),
                'host': host
            }
            graph_engine.add_node(policy_id, 'PolkitPolicy', policy_properties)
            nodes_added += 1
            graph_engine.add_edge(system_id, policy_id, 'HAS_POLICY', {})
            edges_added += 1
    
    return {'nodes_added': nodes_added, 'edges_added': edges_added}
