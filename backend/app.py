"""
WolfTrace Backend - Main API Server
"""
from flask import Flask, request, jsonify, send_file, g, Response
from flask_cors import CORS
import os
import json
import zipfile
import logging
import time
import traceback
import uuid
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from graph_engine import GraphEngine
from database import DatabaseFactory, DatabaseType
from migrations import MigrationManager
from plugin_manager import PluginManager
from pathlib import Path
from graph_analytics import GraphAnalytics
from session_manager import SessionManager
from query_builder import QueryBuilder
from graph_comparison import GraphComparison
from report_generator import ReportGenerator
from bulk_operations import BulkOperations
from graph_templates import GraphTemplates
from history_manager import HistoryManager
from advanced_search import AdvancedSearch
from response_wrapper import ResponseWrapper
from openapi_spec import generate_openapi_spec
from logger_config import setup_logging, get_logger, log_performance
from exceptions import (
    WolfTraceException,
    ValidationError,
    NodeNotFoundError,
    PluginNotFoundError,
    SessionError,
    ImportError as WolfImportError,
    RequestTooLargeError
)
from validators import (
    validate_node_id,
    validate_node_ids,
    validate_edge_spec,
    validate_json_schema,
    validate_request_size,
    sanitize_properties,
    IMPORT_SCHEMA,
    IMPORT_AUTODETECT_SCHEMA,
    PATHS_SCHEMA,
    BULK_DELETE_NODES_SCHEMA,
    BULK_DELETE_EDGES_SCHEMA,
    BULK_UPDATE_NODES_SCHEMA,
    SESSION_SAVE_SCHEMA,
    QUERY_SCHEMA,
    MAX_REQUEST_SIZE
)

load_dotenv()

# Configure advanced logging system
logger = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    enable_json=os.getenv('LOG_JSON', 'false').lower() == 'true',
    enable_access_log=True
)

app = Flask(__name__)
CORS(app)

# Request logging middleware
@app.before_request
def log_request_info():
    """Log incoming requests and validate request size"""
    g.start_time = time.time()
    
    # Validate request size
    content_length = request.content_length
    if content_length:
        try:
            validate_request_size(content_length, MAX_REQUEST_SIZE)
        except RequestTooLargeError as e:
            logger.warning(
                f"Request too large: {content_length} bytes",
                extra={'ip': request.remote_addr, 'path': request.path}
            )
            return jsonify(e.to_dict()), 413
    
    logger.debug(
        f"Incoming request: {request.method} {request.path}",
        extra={
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'content_type': request.content_type
        }
    )

@app.after_request
def log_response_info(response):
    """Log outgoing responses"""
    duration = time.time() - g.get('start_time', 0)
    access_logger = logging.getLogger('wolftrace.access')
    
    access_logger.info(
        f"{request.method} {request.path}",
        extra={
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': duration,
            'ip': request.remote_addr,
            'response_size': len(response.get_data())
        }
    )
    
    # Log slow requests
    if duration > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.path} took {duration:.3f}s",
            extra={'duration': duration, 'path': request.path}
        )
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler with detailed logging"""
    # Handle WolfTrace custom exceptions
    if isinstance(e, WolfTraceException):
        logger.warning(
            f"WolfTrace exception: {e.error_code} - {e.message}",
            extra={
                'error_code': e.error_code,
                'path': request.path,
                'method': request.method,
                'ip': request.remote_addr,
                'details': e.details
            }
        )
        # Determine appropriate status code
        status_code = 400
        if isinstance(e, NodeNotFoundError):
            status_code = 404
        elif isinstance(e, PluginNotFoundError):
            status_code = 404
        elif isinstance(e, SessionError) and 'not found' in e.message.lower():
            status_code = 404
        elif isinstance(e, RequestTooLargeError):
            status_code = 413
        
        return jsonify(e.to_dict()), status_code
    
    # Handle other exceptions with full stack trace
    logger.error(
        f"Unhandled exception: {str(e)}",
        extra={
            'path': request.path,
            'method': request.method,
            'ip': request.remote_addr,
            'exception_type': type(e).__name__,
            'traceback': traceback.format_exc()
        },
        exc_info=True
    )
    
    # Return generic error in production
    return jsonify({
        "error": "Internal server error",
        "error_code": "INTERNAL_ERROR",
        "message": str(e) if app.debug else "An unexpected error occurred"
    }), 500

# Initialize persistence backend
db_backend = None
migration_manager = None

# Configure database backend from environment
db_backend_type = os.getenv('DB_BACKEND', 'memory').lower()
db_uri = os.getenv('DB_URI', 'neo4j://127.0.0.1:7687')
db_user = os.getenv('DB_USERNAME', 'neo4j')
db_password = os.getenv('DB_PASSWORD', 'lunalynx')
db_pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
db_max_conn_lifetime = int(os.getenv('DB_MAX_CONN_LIFETIME', '3600'))
db_acquire_timeout = int(os.getenv('DB_ACQUIRE_TIMEOUT', '30'))
db_max_retry_time = int(os.getenv('DB_MAX_RETRY_TIME', '15'))

# Initialize graph engine
graph_engine = GraphEngine()

if db_backend_type == 'neo4j':
    try:
        db_backend = DatabaseFactory.create_backend(
            DatabaseType.NEO4J,
            uri=db_uri,
            username=db_user,
            password=db_password,
            pool_size=db_pool_size,
            max_conn_lifetime=db_max_conn_lifetime,
            acquire_timeout=db_acquire_timeout,
            max_retry_time=db_max_retry_time
        )
        db_backend.connect()
        migration_manager = MigrationManager(db_backend=db_backend)
        applied = migration_manager.apply_all_pending()
        if applied:
            logger.info(f"Applied migrations: {applied}")
        graph_engine.set_backend(db_backend)
        sync_stats = graph_engine.sync_from_backend()
        logger.info(
            f"Synced graph from Neo4j at startup (nodes={sync_stats['nodes']}, edges={sync_stats['edges']})"
        )
    except Exception as e:
        logger.error(f"Neo4j connection failed, falling back to in-memory backend: {str(e)}")
        db_backend = DatabaseFactory.create_backend(DatabaseType.IN_MEMORY, graph_engine=graph_engine)
        db_backend.connect()
else:
    db_backend = DatabaseFactory.create_backend(DatabaseType.IN_MEMORY, graph_engine=graph_engine)
    db_backend.connect()

# Plugins are now in backend/plugins directory
plugins_path = str((Path(__file__).resolve().parent / 'plugins').resolve())
plugin_manager = PluginManager(plugins_dir=plugins_path)
analytics = GraphAnalytics(graph_engine)
session_manager = SessionManager()
query_builder = QueryBuilder(graph_engine)
graph_comparison = GraphComparison(graph_engine)
report_generator = ReportGenerator(graph_engine, analytics)
bulk_operations = BulkOperations(graph_engine, db_backend)
graph_templates = GraphTemplates()
history_manager = HistoryManager()
advanced_search = AdvancedSearch(graph_engine)

# Background task executor for heavy operations (e.g., long path searches)
task_executor = ThreadPoolExecutor(max_workers=4)
task_registry = {}

# Helper function to restore graph state (eliminates code duplication)
def _restore_graph_from_state(state: Dict):
    """
    Restore graph engine from saved state
    
    Args:
        state: Dictionary with 'nodes' and 'edges' keys
    """
    graph_engine.clear()
    for node in state.get('nodes', []):
        graph_engine.add_node(node['id'], node.get('type', 'Entity'), node)
    for edge in state.get('edges', []):
        source = edge.get('source')
        target = edge.get('target')
        graph_engine.add_edge(source, target, edge.get('type', 'RELATED_TO'), edge)

@app.route('/api', methods=['GET'])
def api_root():
    """API root - list all available endpoints"""
    return jsonify({
        "name": "WolfTrace API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "graph": "/api/graph",
            "nodes": "/api/nodes",
            "edges": "/api/edges",
            "plugins": "/api/plugins",
            "import": "/api/import",
            "paths": "/api/paths",
            "search": "/api/search",
            "clear": "/api/clear",
            "export": "/api/export",
            "sessions": "/api/sessions",
            "analytics": "/api/analytics/stats",
            "query": "/api/query",
            "compare": "/api/compare",
            "report": "/api/report",
            "bulk": "/api/bulk/*",
            "templates": "/api/templates",
            "history": "/api/history/*"
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({"status": "ok"})

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes in the graph"""
    try:
        node_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 100))
        cursor = request.args.get('cursor')
        limit = max(1, min(limit, 1000))
        result = graph_engine.get_nodes_paginated(node_type=node_type, limit=limit, cursor=cursor)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting nodes: {str(e)}", exc_info=True)
        raise

@app.route('/api/edges', methods=['GET'])
def get_edges():
    """Get all edges in the graph"""
    try:
        edge_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 200))
        cursor = request.args.get('cursor')
        limit = max(1, min(limit, 2000))
        result = graph_engine.get_edges_paginated(edge_type=edge_type, limit=limit, cursor=cursor)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting edges: {str(e)}", exc_info=True)
        raise

@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get full graph data"""
    try:
        graph_data = graph_engine.get_full_graph()
        return jsonify(graph_data)
    except Exception as e:
        logger.error(f"Error getting graph: {str(e)}", exc_info=True)
        raise

@app.route('/api/paths', methods=['POST'])
def find_paths():
    """Find paths between nodes with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, PATHS_SCHEMA)
        
        source = data.get('source')
        target = data.get('target')
        max_depth = data.get('max_depth', 5)
        max_paths = data.get('max_paths', 100)
        run_async = str(request.args.get('async', 'false')).lower() == 'true'
        
        # Validate node IDs
        validate_node_id(source)
        validate_node_id(target)
        
        # Check if nodes exist
        if source not in graph_engine.graph:
            raise NodeNotFoundError(source)
        if target not in graph_engine.graph:
            raise NodeNotFoundError(target)
        
        if run_async:
            task_id = f"task_{uuid.uuid4().hex}"
            future = task_executor.submit(graph_engine.find_paths, source, target, max_depth, max_paths)
            task_registry[task_id] = future
            return jsonify({"task_id": task_id, "status": "running"}), 202
        paths = graph_engine.find_paths(source, target, max_depth, max_paths)
        return jsonify(paths)
    except (ValidationError, NodeNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Error finding paths: {str(e)}", exc_info=True)
        raise

@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """List available plugins"""
    try:
        plugins = plugin_manager.list_plugins()
        return jsonify(plugins)
    except Exception as e:
        logger.error(f"Error listing plugins: {str(e)}", exc_info=True)
        raise

@app.route('/api/import', methods=['POST'])
@log_performance("import_data")
def import_data():
    """Import data via plugin with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, IMPORT_SCHEMA)
        
        collector = data.get('collector')
        import_data = data.get('data')
        
        # Sanitize properties if data is a dict
        if isinstance(import_data, dict):
            import_data = sanitize_properties(import_data)
        
        logger.info(f"Importing data with plugin: {collector}")
        
        # Check if plugin exists
        if collector not in plugin_manager.plugins:
            raise PluginNotFoundError(collector)
        
        result = plugin_manager.process_data(collector, import_data, graph_engine)
        nodes_added = result.get('nodes_added', 0)
        edges_added = result.get('edges_added', 0)
        logger.info(f"Import successful: {nodes_added} nodes, {edges_added} edges added")
        history_manager.save_state(graph_engine.get_full_graph(), f"Import data via {collector}")
        return jsonify(result)
    except (ValidationError, PluginNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        raise WolfImportError(f"Import operation failed: {str(e)}")

# Helper function to return standardized error responses
def _error_response(message: str, error_code: str = "INVALID_REQUEST", status_code: int = 400, details: Dict = None):
    """
    Return standardized error response in JSON format
    
    Args:
        message: Error message
        error_code: Error code identifier
        status_code: HTTP status code
        details: Optional additional error details
        
    Returns:
        Tuple of (response dict, status code)
    """
    error_response = {
        'error': True,
        'error_code': error_code,
        'message': message
    }
    if details:
        error_response['details'] = details
    return jsonify(error_response), status_code

def _merge_json_objects(acc, obj):
    """
    Merge two JSON-like Python objects (dicts). 
    
    Strategy:
    - Lists are concatenated
    - Dicts are merged recursively
    - Scalars are overridden
    - None values are replaced with the other value
    
    Args:
        acc: Accumulator object (can be None)
        obj: Object to merge into accumulator
        
    Returns:
        Merged object
    """
    # Handle None cases
    if acc is None:
        return obj
    if obj is None:
        return acc
    
    # Both are dicts - merge recursively
    if isinstance(acc, dict) and isinstance(obj, dict):
        result = dict(acc)
        for key, value in obj.items():
            if key in result:
                # Key exists in both - decide merge strategy based on types
                if isinstance(result[key], list) and isinstance(value, list):
                    # Both lists - concatenate
                    result[key] = result[key] + value
                elif isinstance(result[key], dict) and isinstance(value, dict):
                    # Both dicts - recurse
                    result[key] = _merge_json_objects(result[key], value)
                else:
                    # Different types or scalars - override
                    result[key] = value
            else:
                # Key only in obj - add it
                result[key] = value
        return result
    
    # Both are lists - concatenate
    if isinstance(acc, list) and isinstance(obj, list):
        return acc + obj
    
    # Default: obj overrides acc
    return obj

@app.route('/api/import-zip', methods=['POST'])
def import_zip():
    """
    Import a ZIP archive containing one or more JSON files.
    Merges all JSON files into a single object and passes to the given plugin.
    """
    collector = request.form.get('collector')
    file = request.files.get('file')

    if not collector:
        return _error_response('Collector name required', error_code='MISSING_COLLECTOR_NAME', status_code=400)
    if not file:
        return _error_response('ZIP file required (multipart/form-data with file)', error_code='MISSING_FILE', status_code=400)

    try:
        merged = None
        # Read file content into memory to avoid SpooledTemporaryFile seekable issue
        file.seek(0)  # Reset file pointer
        file_content = file.read()
        
        with zipfile.ZipFile(BytesIO(file_content)) as zf:
            for name in zf.namelist():
                if name.lower().endswith('.json'):
                    with zf.open(name) as f:
                        try:
                            data = json.load(f)
                            # Extract filename without extension to use as key
                            filename_key = Path(name).stem.lower()
                            if merged is None:
                                merged = {}
                            # Add data under filename key for plugin detection
                            merged[filename_key] = data
                            # For metadata, also merge top-level keys
                            if filename_key == 'metadata':
                                merged = _merge_json_objects(merged, data)
                        except Exception:
                            # skip invalid JSON entries
                            continue
        if merged is None:
            return _error_response('No valid JSON files found in archive', error_code='NO_JSON_FILES', status_code=400)

        result = plugin_manager.process_data(collector, merged, graph_engine)
        history_manager.save_state(graph_engine.get_full_graph(), f"Import ZIP via {collector}")
        return jsonify(result)
    except zipfile.BadZipFile:
        return _error_response('Invalid ZIP file', error_code='INVALID_ZIP', status_code=400)
    except Exception as e:
        return _error_response(str(e), error_code='IMPORT_ERROR', status_code=400)

@app.route('/api/import-autodetect', methods=['POST'])
@log_performance("import_autodetect")
def import_autodetect():
    """Import data with automatic plugin detection and validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, IMPORT_AUTODETECT_SCHEMA)
        
        import_data = data.get('data')
        
        # Sanitize properties if data is a dict
        if isinstance(import_data, dict):
            import_data = sanitize_properties(import_data)
        
        data_keys = list(import_data.keys())[:10] if isinstance(import_data, dict) else 'non-dict'
        logger.info(f"Import autodetect: Analyzing data structure (keys: {data_keys})")
        
        # When payload clearly has a graph (nodes + edges), use web plugin so we get the full graph
        nlist = import_data.get('nodes') if isinstance(import_data.get('nodes'), list) else []
        elist = import_data.get('edges') if isinstance(import_data.get('edges'), list) else []
        if len(nlist) > 0 and len(elist) > 0 and 'web' in plugin_manager.plugins:
            detected_plugin = 'web'
            logger.info("Import autodetect: Using web plugin for graph (nodes + edges present)")
        else:
            detected_plugin = plugin_manager.detect_plugin(import_data)
        
        if not detected_plugin:
            logger.warning(
                "Import autodetect: Could not detect plugin for data format",
                extra={'data_keys': data_keys if isinstance(data_keys, list) else str(data_keys)}
            )
            raise WolfImportError(
                "Could not detect appropriate plugin for this data format",
                details={'available_plugins': list(plugin_manager.plugins.keys())}
            )
        
        logger.info(f"Import autodetect: Detected plugin '{detected_plugin}' for data")
        
        # Process with detected plugin
        result = plugin_manager.process_data(detected_plugin, import_data, graph_engine)
        nodes_added = result.get('nodes_added', 0)
        edges_added = result.get('edges_added', 0)
        
        logger.info(
            f"Import autodetect: Successfully processed with '{detected_plugin}'",
            extra={
                'plugin': detected_plugin,
                'nodes_added': nodes_added,
                'edges_added': edges_added
            }
        )
        
        history_manager.save_state(
            graph_engine.get_full_graph(),
            f"Import data via {detected_plugin} (autodetected)"
        )
        
        return jsonify({
            **result,
            'detected_plugin': detected_plugin
        })
    except Exception as e:
        logger.error(
            f"Import autodetect: Error processing data - {str(e)}",
            exc_info=True,
            extra={'error_type': type(e).__name__}
        )
        return jsonify({"error": str(e)}), 400

@app.route('/api/import-zip-autodetect', methods=['POST'])
@log_performance("import_zip_autodetect")
def import_zip_autodetect():
    """Import ZIP archive with automatic plugin detection"""
    file = request.files.get('file')

    if not file:
        logger.error("Import ZIP autodetect: No file received in request")
        return jsonify({"error": "ZIP file required (multipart/form-data with 'file')"}), 400

    try:
        logger.info(f"Import ZIP autodetect: Processing file '{file.filename}'")
        merged = None
        json_files = []
        total_size = 0
        
        # Read file content into memory to avoid SpooledTemporaryFile seekable issue
        file.seek(0)  # Reset file pointer
        file_content = file.read()
        
        with zipfile.ZipFile(BytesIO(file_content)) as zf:
            for name in zf.namelist():
                if name.lower().endswith('.json'):
                    json_files.append(name)
                    with zf.open(name) as f:
                        try:
                            data = json.load(f)
                            file_size = len(json.dumps(data))
                            total_size += file_size
                            data_keys = list(data.keys())[:10] if isinstance(data, dict) else 'non-dict'
                            logger.debug(
                                f"Loaded JSON file: {name}",
                                extra={
                                    'file_name': name,
                                    'keys': data_keys if isinstance(data_keys, list) else str(data_keys),
                                    'size': file_size
                                }
                            )
                            
                            # Extract filename without extension to use as key
                            # This allows web plugin to find data by tool name (e.g., 'rustscan', 'dns_dig')
                            filename_key = Path(name).stem.lower()  # e.g., 'rustscan.json' -> 'rustscan'
                            
                            # Initialize merged dict if needed
                            if merged is None:
                                merged = {}
                            
                            # Add data under filename key for plugin detection
                            merged[filename_key] = data
                            
                            # For metadata.json, also merge its keys at top level for plugin detection
                            if filename_key == 'metadata':
                                merged = _merge_json_objects(merged, data)
                        except Exception as e:
                            logger.warning(
                                f"Skipping invalid JSON file: {name}",
                                extra={'file_name': name, 'error': str(e)}
                            )
                            continue
        
        logger.info(
            f"Import ZIP autodetect: Processed {len(json_files)} JSON files",
            extra={
                'file_name': file.filename,
                'json_files_count': len(json_files),
                'total_size': total_size,
                'json_files': json_files
            }
        )
        
        if merged is None:
            logger.error("Import ZIP autodetect: No valid JSON files found in archive")
            return jsonify({"error": "No valid JSON files found in archive"}), 400

        # Promote nested nodes/edges to top level so the web plugin sees the full graph
        # (e.g. ZIP with graph.json {nodes, edges} or nodes.json/edges.json as separate files)
        if 'nodes' not in merged or 'edges' not in merged:
            for _key, val in merged.items():
                if isinstance(val, dict) and 'nodes' in val and 'edges' in val:
                    nlist, elist = val.get('nodes'), val.get('edges')
                    if isinstance(nlist, list) and isinstance(elist, list) and len(nlist) > 0:
                        merged.setdefault('nodes', nlist)
                        merged.setdefault('edges', elist)
                        break
        # If we have separate nodes.json and edges.json they're already merged["nodes"] and merged["edges"]
        # Ensure we keep the largest graph if multiple keys had nodes/edges (e.g. metadata merged one node)
        if 'nodes' in merged and 'edges' in merged:
            nlist = merged['nodes'] if isinstance(merged['nodes'], list) else []
            elist = merged['edges'] if isinstance(merged['edges'], list) else []
            for _key, val in merged.items():
                if isinstance(val, dict) and 'nodes' in val and 'edges' in val:
                    vn, ve = val.get('nodes'), val.get('edges')
                    if isinstance(vn, list) and isinstance(ve, list) and len(vn) > len(nlist):
                        nlist, elist = vn, ve
            merged['nodes'] = nlist
            merged['edges'] = elist

        merged_keys = list(merged.keys())[:20]
        logger.debug(f"Import ZIP autodetect: Merged data structure (keys: {merged_keys})")
        
        # When ZIP clearly contains a graph (nodes + edges), use web plugin so we get the full graph.
        # Otherwise compliance can be chosen (e.g. due to metadata "tool") and only one "Agent" node is added.
        nlist = merged.get('nodes') if isinstance(merged.get('nodes'), list) else []
        elist = merged.get('edges') if isinstance(merged.get('edges'), list) else []
        if len(nlist) > 0 and len(elist) > 0 and 'web' in plugin_manager.plugins:
            detected_plugin = 'web'
            logger.info("Import ZIP autodetect: Using web plugin for graph (nodes + edges present)")
        else:
            detected_plugin = plugin_manager.detect_plugin(merged)
        
        if not detected_plugin:
            logger.warning(
                "Import ZIP autodetect: Could not detect plugin for merged data",
                extra={'merged_keys': merged_keys}
            )
            return jsonify({"error": "Could not detect appropriate plugin for this data format"}), 400

        logger.info(f"Import ZIP autodetect: Detected plugin '{detected_plugin}'")
        
        # Process with detected plugin
        result = plugin_manager.process_data(detected_plugin, merged, graph_engine)
        nodes_added = result.get('nodes_added', 0)
        edges_added = result.get('edges_added', 0)
        
        logger.info(
            f"Import ZIP autodetect: Successfully processed",
            extra={
                'file_name': file.filename,
                'plugin': detected_plugin,
                'nodes_added': nodes_added,
                'edges_added': edges_added,
                'files_processed': len(json_files)
            }
        )
        
        history_manager.save_state(
            graph_engine.get_full_graph(),
            f"Import ZIP via {detected_plugin} (autodetected)"
        )
        
        return jsonify({
            **result,
            'detected_plugin': detected_plugin
        })
    except zipfile.BadZipFile as e:
        logger.error(
            f"Import ZIP autodetect: Invalid ZIP file - {str(e)}",
            extra={'file_name': file.filename if file else 'unknown'}
        )
        return jsonify({"error": "Invalid ZIP file"}), 400
    except Exception as e:
        logger.error(
            f"Import ZIP autodetect: Error processing ZIP - {str(e)}",
            exc_info=True,
            extra={
                'file_name': file.filename if file else 'unknown',
                'error_type': type(e).__name__
            }
        )
        return jsonify({"error": str(e)}), 400

@app.route('/api/clear', methods=['POST'])
def clear_graph():
    """Clear the graph"""
    graph_engine.clear()
    history_manager.save_state({'nodes': [], 'edges': []}, "Clear graph")
    return jsonify({"status": "cleared"})

@app.route('/api/search', methods=['GET'])
def search_nodes():
    """Search for nodes by ID or properties"""
    query = request.args.get('q', '').lower()
    node_type = request.args.get('type', None)
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    nodes = graph_engine.get_nodes(node_type)
    results = []
    
    for node in nodes:
        # Search in ID
        if query in node.get('id', '').lower():
            results.append(node)
            continue
        
        # Search in properties
        for key, value in node.items():
            if isinstance(value, str) and query in value.lower():
                results.append(node)
                break
            elif isinstance(value, (list, dict)) and query in str(value).lower():
                results.append(node)
                break
        
        if len(results) >= limit:
            break
    
    return jsonify(results[:limit])

@app.route('/api/analytics/stats', methods=['GET'])
def get_analytics_stats():
    """Get graph statistics and metrics"""
    stats = analytics.get_statistics()
    return jsonify(stats)

@app.route('/api/analytics/communities', methods=['GET'])
def get_communities():
    """Find communities in the graph"""
    max_communities = int(request.args.get('max', 10))
    communities = analytics.find_communities(max_communities)
    return jsonify(communities)

@app.route('/api/analytics/neighbors', methods=['GET'])
def get_neighbors():
    """Get neighbors of a node"""
    node_id = request.args.get('node')
    depth = int(request.args.get('depth', 1))
    
    if not node_id:
        return jsonify({"error": "Node ID required"}), 400
    
    neighbors = analytics.get_node_neighbors(node_id, depth)
    return jsonify(neighbors)

@app.route('/api/export', methods=['GET'])
def export_graph():
    """Export graph data as JSON"""
    format_type = request.args.get('format', 'json')
    stream = request.args.get('stream', 'false').lower() == 'true'
    page_size = int(request.args.get('page_size', 1000))
    page_size = max(100, min(page_size, 5000))
    
    if format_type == 'json':
        if stream:
            def generate():
                yield '{"nodes":['
                first = True
                cursor = None
                while True:
                    page = graph_engine.get_nodes_paginated(limit=page_size, cursor=cursor)
                    for item in page['items']:
                        if not first:
                            yield ','
                        yield json.dumps(item)
                        first = False
                    cursor = page.get('next_cursor')
                    if not cursor:
                        break
                yield '],"edges":['
                first_edge = True
                cursor = None
                while True:
                    page = graph_engine.get_edges_paginated(limit=page_size, cursor=cursor)
                    for item in page['items']:
                        if not first_edge:
                            yield ','
                        yield json.dumps(item)
                        first_edge = False
                    cursor = page.get('next_cursor')
                    if not cursor:
                        break
                yield ']}'
            return Response(generate(), mimetype='application/json')
        graph_data = graph_engine.get_full_graph()
        return jsonify(graph_data)
    else:
        return jsonify({"error": f"Format '{format_type}' not supported"}), 400

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all saved sessions"""
    try:
        limit = int(request.args.get('limit', 50))
        sessions = session_manager.list_sessions(filters=None, limit=limit)
        return jsonify(sessions)
    except ValueError:
        raise ValidationError("Invalid limit parameter", field="limit")
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise

@app.route('/api/sessions', methods=['POST'])
def save_session():
    """Save current graph as a session with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, SESSION_SAVE_SCHEMA)
        
        session_name = data.get('name', 'Untitled Session')
        metadata = data.get('metadata', {})
        
        # Sanitize metadata
        if metadata:
            metadata = sanitize_properties(metadata)
        
        graph_data = graph_engine.get_full_graph()
        logger.info(f"Saving session: {session_name}")
        session = session_manager.save_session(session_name, graph_data, metadata)
        return jsonify(session)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Error saving session: {str(e)}", exc_info=True)
        raise SessionError(f"Failed to save session: {str(e)}")

@app.route('/api/sessions/<session_id>', methods=['GET'])
def load_session(session_id):
    """Load a saved session with validation"""
    try:
        # Basic validation of session_id
        if not session_id or len(session_id) > 200:
            raise ValidationError("Invalid session ID", field="session_id")
        
        session_data = session_manager.load_session(session_id)
        return jsonify(session_data)
    except FileNotFoundError:
        raise SessionError(f"Session not found", session_id=session_id)
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {str(e)}", exc_info=True)
        raise

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session with validation"""
    try:
        # Basic validation of session_id
        if not session_id or len(session_id) > 200:
            raise ValidationError("Invalid session ID", field="session_id")
        
        if session_manager.delete_session(session_id):
            logger.info(f"Deleted session: {session_id}")
            return jsonify({"status": "deleted"})
        raise SessionError("Session not found", session_id=session_id)
    except SessionError as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}", exc_info=True)
        raise

@app.route('/api/sessions/<session_id>/restore', methods=['POST'])
def restore_session(session_id):
    """Restore a session to the current graph with validation"""
    try:
        # Basic validation of session_id
        if not session_id or len(session_id) > 200:
            raise ValidationError("Invalid session ID", field="session_id")
        
        session_data = session_manager.load_session(session_id)
        
        # Restore graph from saved session
        _restore_graph_from_state(session_data.get('graph', {}))
        
        return jsonify({"status": "restored", "session": session_data['name']})
    except FileNotFoundError:
        raise SessionError("Session not found", session_id=session_id)
    except (ValidationError, SessionError) as e:
        raise
    except Exception as e:
        logger.error(f"Error restoring session {session_id}: {str(e)}", exc_info=True)
        raise SessionError(f"Failed to restore session: {str(e)}", session_id=session_id)

@app.route('/api/query', methods=['POST'])
def query_graph():
    """Advanced query with filters and validation"""
    try:
        filters = request.json
        if not filters:
            filters = {}
        
        # Validate query schema
        if filters:
            validate_json_schema(filters, QUERY_SCHEMA)
        
        logger.debug(f"Executing query with filters: {filters}")
        result = query_builder.build_query(filters)
        return jsonify(result)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/query/stats', methods=['POST'])
def query_stats():
    """Get statistics for a query with validation"""
    try:
        filters = request.json
        if not filters:
            filters = {}
        
        # Validate query schema
        if filters:
            validate_json_schema(filters, QUERY_SCHEMA)
        
        stats = query_builder.get_statistics_for_query(filters)
        return jsonify(stats)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Query stats failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/graph/paginated', methods=['GET'])
def get_paginated_graph():
    """Get graph data with pagination"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    node_type = request.args.get('type', None)
    
    all_nodes = graph_engine.get_nodes(node_type)
    all_edges = graph_engine.get_edges()
    
    # Paginate nodes
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_nodes = all_nodes[start_idx:end_idx]
    
    # Get edges for paginated nodes
    node_ids = {node['id'] for node in paginated_nodes}
    paginated_edges = [
        edge for edge in all_edges
        if edge.get('source') in node_ids or edge.get('target') in node_ids
    ]
    
    return jsonify({
        'nodes': paginated_nodes,
        'edges': paginated_edges,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(all_nodes),
            'total_pages': (len(all_nodes) + per_page - 1) // per_page
        }
    })

# Graph Comparison endpoints
@app.route('/api/compare', methods=['POST'])
def compare_graphs():
    """Compare two graphs"""
    data = request.json
    graph1 = data.get('graph1', {})
    graph2 = data.get('graph2', {})
    
    if not graph1 or not graph2:
        return jsonify({"error": "Both graph1 and graph2 are required"}), 400
    
    comparison = graph_comparison.compare_graphs(graph1, graph2)
    return jsonify(comparison)

@app.route('/api/compare/diff-graph', methods=['POST'])
def get_diff_graph():
    """Get visualization graph showing differences"""
    data = request.json
    graph1 = data.get('graph1', {})
    graph2 = data.get('graph2', {})
    
    if not graph1 or not graph2:
        return jsonify({"error": "Both graph1 and graph2 are required"}), 400
    
    comparison = graph_comparison.compare_graphs(graph1, graph2)
    diff_graph = graph_comparison.create_diff_graph(comparison)
    return jsonify(diff_graph)

# Report generation endpoints
@app.route('/api/report', methods=['GET'])
def generate_report():
    """Generate report data"""
    include_graph = request.args.get('include_graph', 'false').lower() == 'true'
    format_type = request.args.get('format', 'json')
    
    report_data = report_generator.generate_report_data(include_graph)
    
    if format_type == 'html':
        html = report_generator.generate_html_report(report_data)
        return html, 200, {'Content-Type': 'text/html'}
    elif format_type == 'json':
        return jsonify(report_data)
    else:
        return jsonify({"error": f"Format '{format_type}' not supported"}), 400

# Bulk operations endpoints
@app.route('/api/bulk/nodes/delete', methods=['POST'])
def bulk_delete_nodes():
    """Delete multiple nodes with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, BULK_DELETE_NODES_SCHEMA)
        
        node_ids = data.get('node_ids', [])
        
        # Validate all node IDs
        validate_node_ids(node_ids)
        
        logger.info(f"Bulk deleting {len(node_ids)} nodes")
        result = bulk_operations.bulk_delete_nodes(node_ids)
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk delete {len(node_ids)} nodes")
        return jsonify(result)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk delete nodes failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/edges/delete', methods=['POST'])
def bulk_delete_edges():
    """Delete multiple edges with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, BULK_DELETE_EDGES_SCHEMA)
        
        edge_specs = data.get('edges', [])
        
        # Validate each edge specification
        for edge_spec in edge_specs:
            validate_edge_spec(edge_spec)
        
        logger.info(f"Bulk deleting {len(edge_specs)} edges")
        result = bulk_operations.bulk_delete_edges(edge_specs)
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk delete {len(edge_specs)} edges")
        return jsonify(result)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk delete edges failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/nodes/update', methods=['POST'])
def bulk_update_nodes():
    """Update multiple nodes with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate schema
        validate_json_schema(data, BULK_UPDATE_NODES_SCHEMA)
        
        updates = data.get('updates', [])
        
        # Validate and sanitize each update
        for update in updates:
            node_id = update.get('id')
            validate_node_id(node_id)
            if 'properties' in update:
                update['properties'] = sanitize_properties(update['properties'])
        
        logger.info(f"Bulk updating {len(updates)} nodes")
        result = bulk_operations.bulk_update_nodes(updates)
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk update {len(updates)} nodes")
        return jsonify(result)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk update nodes failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/nodes/tag', methods=['POST'])
def bulk_tag_nodes():
    """Tag multiple nodes with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        node_ids = data.get('node_ids', [])
        tags = data.get('tags', [])
        operation = data.get('operation', 'add')
        
        if not node_ids:
            raise ValidationError("node_ids array is required", field="node_ids")
        if not tags:
            raise ValidationError("tags array is required", field="tags")
        if operation not in ['add', 'remove']:
            raise ValidationError("operation must be 'add' or 'remove'", field="operation")
        
        # Validate node IDs
        validate_node_ids(node_ids)
        
        logger.info(f"Bulk tagging {len(node_ids)} nodes with {len(tags)} tags")
        result = bulk_operations.bulk_tag_nodes(node_ids, tags, operation)
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk tag {len(node_ids)} nodes")
        return jsonify(result)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk tag nodes failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/nodes/export', methods=['POST'])
def bulk_export_nodes():
    """Export multiple nodes with validation"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        node_ids = data.get('node_ids', [])
        
        if not node_ids:
            raise ValidationError("node_ids array is required", field="node_ids")
        
        # Validate node IDs
        validate_node_ids(node_ids)
        
        nodes = bulk_operations.bulk_export_nodes(node_ids)
        return jsonify(nodes)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk export nodes failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/nodes/create', methods=['POST'])
def bulk_create_nodes():
    """Create multiple nodes in bulk"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        nodes = data.get('nodes', [])
        if not nodes:
            raise ValidationError("nodes array is required", field="nodes")
        
        logger.info(f"Bulk creating {len(nodes)} nodes")
        result = bulk_operations.bulk_create_nodes(nodes)
        if result.get('errors'):
            return jsonify(result), 207  # 207 Multi-Status for partial success
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk create {len(nodes)} nodes")
        return jsonify(result), 201
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk create nodes failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/edges/create', methods=['POST'])
def bulk_create_edges():
    """Create multiple edges in bulk"""
    try:
        data = request.json
        if not data:
            raise ValidationError("Request body is required")
        
        edges = data.get('edges', [])
        if not edges:
            raise ValidationError("edges array is required", field="edges")
        
        logger.info(f"Bulk creating {len(edges)} edges")
        result = bulk_operations.bulk_create_edges(edges)
        if result.get('errors'):
            return jsonify(result), 207  # 207 Multi-Status for partial success
        history_manager.save_state(graph_engine.get_full_graph(), f"Bulk create {len(edges)} edges")
        return jsonify(result), 201
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Bulk create edges failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/bulk/rollback', methods=['POST'])
def rollback_transaction():
    """Rollback the last bulk operation"""
    try:
        result = bulk_operations.rollback_transaction()
        history_manager.save_state(graph_engine.get_full_graph(), f"Rollback transaction ({result['rolled_back']} operations)")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}", exc_info=True)
        raise

# Advanced search endpoints
@app.route('/api/search/regex', methods=['GET'])
def search_regex():
    """Search nodes using regex pattern"""
    try:
        pattern = request.args.get('pattern', '')
        node_type = request.args.get('type')
        
        if not pattern:
            raise ValidationError("pattern parameter is required", field="pattern")
        
        results = advanced_search.search_regex(pattern, node_type)
        return jsonify(results)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Regex search failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/search/fuzzy', methods=['GET'])
def search_fuzzy():
    """Search nodes using fuzzy matching"""
    try:
        query = request.args.get('query', '')
        node_type = request.args.get('type')
        threshold = float(request.args.get('threshold', 0.6))
        limit = int(request.args.get('limit', 50))
        
        if not query:
            raise ValidationError("query parameter is required", field="query")
        if not (0 <= threshold <= 1):
            raise ValidationError("threshold must be between 0 and 1", field="threshold")
        
        results = advanced_search.search_fuzzy(query, node_type, threshold, limit)
        return jsonify(results)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Fuzzy search failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/search/full-text', methods=['GET'])
def search_full_text():
    """Full-text search across all node properties"""
    try:
        query = request.args.get('query', '')
        node_type = request.args.get('type')
        case_sensitive = request.args.get('case_sensitive', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        if not query:
            raise ValidationError("query parameter is required", field="query")
        
        results = advanced_search.search_full_text(query, node_type, case_sensitive, limit)
        return jsonify(results)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Full-text search failed: {str(e)}", exc_info=True)
        raise

@app.route('/api/search/advanced', methods=['POST'])
def search_advanced():
    """Advanced search with complex filters"""
    try:
        filters = request.json
        if not filters:
            raise ValidationError("Request body with filter specification is required")
        
        results = advanced_search.search_complex_filter(filters)
        return jsonify(results)
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Advanced search failed: {str(e)}", exc_info=True)
        raise

# Graph templates endpoints
@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List all available templates"""
    templates = graph_templates.list_templates()
    return jsonify(templates)

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific template"""
    template = graph_templates.get_template(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404
    return jsonify(template)

@app.route('/api/templates', methods=['POST'])
def save_template():
    """Save a new template"""
    template_data = request.json
    result = graph_templates.save_template(template_data)
    return jsonify(result)

@app.route('/api/templates/<template_id>/apply', methods=['POST'])
def apply_template(template_id):
    """Apply a template to the graph"""
    data = request.json
    variables = data.get('variables', {})
    
    result = graph_templates.create_from_template(template_id, graph_engine, variables)
    if 'error' in result:
        return jsonify(result), 400
    
    history_manager.save_state(graph_engine.get_full_graph(), f"Applied template: {template_id}")
    return jsonify(result)

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Check background task status"""
    future = task_registry.get(task_id)
    if not future:
        return jsonify({"error": "Task not found"}), 404
    if future.done():
        try:
            result = future.result()
            return jsonify({"status": "completed", "result": result})
        except Exception as e:
            return jsonify({"status": "failed", "error": str(e)}), 500
    return jsonify({"status": "running"})

# History/Undo-Redo endpoints
@app.route('/api/history/undo', methods=['POST'])
def undo():
    """Undo last operation"""
    previous_state = history_manager.undo()
    if not previous_state:
        return jsonify({"error": "Nothing to undo"}), 400
    
    # Restore graph state from history
    _restore_graph_from_state(previous_state)
    
    return jsonify({
        'status': 'undone',
        'graph': previous_state,
        'history_info': history_manager.get_history_info()
    })

@app.route('/api/history/redo', methods=['POST'])
def redo():
    """Redo last undone operation"""
    next_state = history_manager.redo()
    if not next_state:
        return jsonify({"error": "Nothing to redo"}), 400
    
    # Restore graph state from redo history
    _restore_graph_from_state(next_state)
    
    return jsonify({
        'status': 'redone',
        'graph': next_state,
        'history_info': history_manager.get_history_info()
    })

@app.route('/api/history/info', methods=['GET'])
def get_history_info():
    """Get history information"""
    return jsonify(history_manager.get_history_info())

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear history"""
    history_manager.clear()
    return jsonify({"status": "cleared"})

# OpenAPI/Swagger Documentation
SWAGGER_URL = '/docs'
API_URL = '/openapi.json'
REDOC_URL = '/redoc'

# Generate OpenAPI spec
@app.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """OpenAPI 3.0 specification - comprehensive API documentation"""
    base_url = request.host_url.rstrip('/')
    spec = generate_openapi_spec(base_url)
    return jsonify(spec)

# Swagger UI endpoint (manual implementation)
@app.route('/docs', methods=['GET'])
@app.route('/docs/', methods=['GET'])
def swagger_ui():
    """Swagger UI documentation"""
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>WolfTrace API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
        '''
    return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ReDoc endpoint
@app.route(REDOC_URL)
def redoc():
    """ReDoc documentation"""
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>WolfTrace API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url="/openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
    '''

# Save state after import operations

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

