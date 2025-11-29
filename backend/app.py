"""
WolfTrace Backend - Main API Server
"""
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
import os
import io
import json
import zipfile
import logging
import time
from dotenv import load_dotenv
from graph_engine import GraphEngine
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
from openapi_spec import generate_openapi_spec
from logger_config import setup_logging, get_logger, log_request_response, log_performance

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
    """Log incoming requests"""
    g.start_time = time.time()
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
    """Global exception handler with logging"""
    logger.error(
        f"Unhandled exception: {str(e)}",
        extra={
            'path': request.path,
            'method': request.method,
            'ip': request.remote_addr
        },
        exc_info=True
    )
    return jsonify({"error": "Internal server error"}), 500

# Initialize components
graph_engine = GraphEngine()
# Plugins are now in backend/plugins directory
plugins_path = str((Path(__file__).resolve().parent / 'plugins').resolve())
plugin_manager = PluginManager(plugins_dir=plugins_path)
analytics = GraphAnalytics(graph_engine)
session_manager = SessionManager()
query_builder = QueryBuilder(graph_engine)
graph_comparison = GraphComparison(graph_engine)
report_generator = ReportGenerator(graph_engine, analytics)
bulk_operations = BulkOperations(graph_engine)
graph_templates = GraphTemplates()
history_manager = HistoryManager()

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
@log_request_response
def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({"status": "ok"})

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes in the graph"""
    node_type = request.args.get('type', None)
    nodes = graph_engine.get_nodes(node_type)
    return jsonify(nodes)

@app.route('/api/edges', methods=['GET'])
def get_edges():
    """Get all edges in the graph"""
    edge_type = request.args.get('type', None)
    edges = graph_engine.get_edges(edge_type)
    return jsonify(edges)

@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get full graph data"""
    graph_data = graph_engine.get_full_graph()
    return jsonify(graph_data)

@app.route('/api/paths', methods=['POST'])
def find_paths():
    """Find paths between nodes"""
    data = request.json
    source = data.get('source')
    target = data.get('target')
    max_depth = data.get('max_depth', 5)
    
    if not source or not target:
        return jsonify({"error": "Missing source or target"}), 400
    
    paths = graph_engine.find_paths(source, target, max_depth)
    return jsonify(paths)

@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """List available plugins"""
    plugins = plugin_manager.list_plugins()
    return jsonify(plugins)

@app.route('/api/import', methods=['POST'])
@log_performance("import_data")
def import_data():
    """Import data via plugin"""
    data = request.json
    collector = data.get('collector')
    import_data = data.get('data')
    
    if not collector:
        logger.warning("Import request missing collector name")
        return jsonify({"error": "Collector name required"}), 400
    
    if not import_data:
        logger.warning("Import request missing data")
        return jsonify({"error": "Data required"}), 400
    
    try:
        logger.info(f"Importing data with plugin: {collector}")
        result = plugin_manager.process_data(collector, import_data, graph_engine)
        nodes_added = result.get('nodes_added', 0)
        edges_added = result.get('edges_added', 0)
        logger.info(f"Import successful: {nodes_added} nodes, {edges_added} edges added")
        history_manager.save_state(graph_engine.get_full_graph(), f"Import data via {collector}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Import failed with plugin {collector}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400

def _merge_json_objects(acc, obj):
    """
    Merge two JSON-like Python objects (dicts). Lists are concatenated,
    dicts are merged recursively, scalars override.
    """
    if acc is None:
        return obj
    if isinstance(acc, dict) and isinstance(obj, dict):
        out = dict(acc)
        for k, v in obj.items():
            if k in out:
                if isinstance(out[k], list) and isinstance(v, list):
                    out[k] = out[k] + v
                elif isinstance(out[k], dict) and isinstance(v, dict):
                    out[k] = _merge_json_objects(out[k], v)
                else:
                    out[k] = v
            else:
                out[k] = v
        return out
    if isinstance(acc, list) and isinstance(obj, list):
        return acc + obj
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
        return jsonify({"error": "Collector name required"}), 400
    if not file:
        return jsonify({"error": "ZIP file required (multipart/form-data with 'file')"}), 400

    try:
        merged = None
        with zipfile.ZipFile(file.stream) as zf:
            for name in zf.namelist():
                if name.lower().endswith('.json'):
                    with zf.open(name) as f:
                        try:
                            data = json.load(f)
                            merged = _merge_json_objects(merged, data)
                        except Exception:
                            # skip invalid JSON entries
                            continue
        if merged is None:
            return jsonify({"error": "No valid JSON files found in archive"}), 400

        result = plugin_manager.process_data(collector, merged, graph_engine)
        history_manager.save_state(graph_engine.get_full_graph(), f"Import ZIP via {collector}")
        return jsonify(result)
    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid ZIP file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/import-autodetect', methods=['POST'])
@log_performance("import_autodetect")
def import_autodetect():
    """Import data with automatic plugin detection"""
    try:
        data = request.json
        if not data:
            logger.error("Import autodetect: No JSON data received")
            return jsonify({"error": "No data received"}), 400
        
        import_data = data.get('data')
        
        if not import_data:
            logger.error("Import autodetect: No 'data' field in request")
            return jsonify({"error": "Data required"}), 400
        
        data_keys = list(import_data.keys())[:10] if isinstance(import_data, dict) else 'non-dict'
        logger.info(f"Import autodetect: Analyzing data structure (keys: {data_keys})")
        
        # Detect which plugin can handle this data
        detected_plugin = plugin_manager.detect_plugin(import_data)
        
        if not detected_plugin:
            logger.warning(
                "Import autodetect: Could not detect plugin for data format",
                extra={'data_keys': data_keys if isinstance(data_keys, list) else str(data_keys)}
            )
            return jsonify({"error": "Could not detect appropriate plugin for this data format"}), 400
        
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
        
        with zipfile.ZipFile(file.stream) as zf:
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

        merged_keys = list(merged.keys())[:20]
        logger.debug(f"Import ZIP autodetect: Merged data structure (keys: {merged_keys})")
        
        # Detect which plugin can handle this data
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
    
    if format_type == 'json':
        graph_data = graph_engine.get_full_graph()
        return jsonify(graph_data)
    else:
        return jsonify({"error": f"Format '{format_type}' not supported"}), 400

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all saved sessions"""
    limit = int(request.args.get('limit', 50))
    sessions = session_manager.list_sessions(limit)
    return jsonify(sessions)

@app.route('/api/sessions', methods=['POST'])
def save_session():
    """Save current graph as a session"""
    data = request.json
    session_name = data.get('name', 'Untitled Session')
    metadata = data.get('metadata', {})
    
    graph_data = graph_engine.get_full_graph()
    session = session_manager.save_session(session_name, graph_data, metadata)
    return jsonify(session)

@app.route('/api/sessions/<session_id>', methods=['GET'])
def load_session(session_id):
    """Load a saved session"""
    try:
        session_data = session_manager.load_session(session_id)
        return jsonify(session_data)
    except FileNotFoundError:
        return jsonify({"error": "Session not found"}), 404

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session"""
    if session_manager.delete_session(session_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/sessions/<session_id>/restore', methods=['POST'])
def restore_session(session_id):
    """Restore a session to the current graph"""
    try:
        session_data = session_manager.load_session(session_id)
        
        # Clear current graph
        graph_engine.clear()
        
        # Import session graph
        graph = session_data.get('graph', {})
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        # Rebuild graph
        for node in nodes:
            graph_engine.add_node(node['id'], node.get('type', 'Entity'), node)
        
        for edge in edges:
            graph_engine.add_edge(
                edge.get('source') or edge.get('source_id'),
                edge.get('target') or edge.get('target_id'),
                edge.get('type', 'RELATED_TO'),
                edge
            )
        
        return jsonify({"status": "restored", "session": session_data['name']})
    except FileNotFoundError:
        return jsonify({"error": "Session not found"}), 404

@app.route('/api/query', methods=['POST'])
def query_graph():
    """Advanced query with filters"""
    filters = request.json or {}
    result = query_builder.build_query(filters)
    return jsonify(result)

@app.route('/api/query/stats', methods=['POST'])
def query_stats():
    """Get statistics for a query"""
    filters = request.json or {}
    stats = query_builder.get_statistics_for_query(filters)
    return jsonify(stats)

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
    """Delete multiple nodes"""
    data = request.json
    node_ids = data.get('node_ids', [])
    
    if not node_ids:
        return jsonify({"error": "node_ids array is required"}), 400
    
    result = bulk_operations.bulk_delete_nodes(node_ids)
    history_manager.save_state(graph_engine.get_full_graph(), f"Bulk delete {len(node_ids)} nodes")
    return jsonify(result)

@app.route('/api/bulk/edges/delete', methods=['POST'])
def bulk_delete_edges():
    """Delete multiple edges"""
    data = request.json
    edge_specs = data.get('edges', [])
    
    if not edge_specs:
        return jsonify({"error": "edges array is required"}), 400
    
    result = bulk_operations.bulk_delete_edges(edge_specs)
    history_manager.save_state(graph_engine.get_full_graph(), f"Bulk delete {len(edge_specs)} edges")
    return jsonify(result)

@app.route('/api/bulk/nodes/update', methods=['POST'])
def bulk_update_nodes():
    """Update multiple nodes"""
    data = request.json
    updates = data.get('updates', [])
    
    if not updates:
        return jsonify({"error": "updates array is required"}), 400
    
    result = bulk_operations.bulk_update_nodes(updates)
    history_manager.save_state(graph_engine.get_full_graph(), f"Bulk update {len(updates)} nodes")
    return jsonify(result)

@app.route('/api/bulk/nodes/tag', methods=['POST'])
def bulk_tag_nodes():
    """Tag multiple nodes"""
    data = request.json
    node_ids = data.get('node_ids', [])
    tags = data.get('tags', [])
    operation = data.get('operation', 'add')
    
    if not node_ids or not tags:
        return jsonify({"error": "node_ids and tags are required"}), 400
    
    result = bulk_operations.bulk_tag_nodes(node_ids, tags, operation)
    history_manager.save_state(graph_engine.get_full_graph(), f"Bulk tag {len(node_ids)} nodes")
    return jsonify(result)

@app.route('/api/bulk/nodes/export', methods=['POST'])
def bulk_export_nodes():
    """Export multiple nodes"""
    data = request.json
    node_ids = data.get('node_ids', [])
    
    if not node_ids:
        return jsonify({"error": "node_ids array is required"}), 400
    
    nodes = bulk_operations.bulk_export_nodes(node_ids)
    return jsonify(nodes)

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

# History/Undo-Redo endpoints
@app.route('/api/history/undo', methods=['POST'])
def undo():
    """Undo last operation"""
    previous_state = history_manager.undo()
    if not previous_state:
        return jsonify({"error": "Nothing to undo"}), 400
    
    # Restore graph state
    graph_engine.clear()
    for node in previous_state.get('nodes', []):
        graph_engine.add_node(node['id'], node.get('type', 'Entity'), node)
    for edge in previous_state.get('edges', []):
        source = edge.get('source') or edge.get('source_id')
        target = edge.get('target') or edge.get('target_id')
        graph_engine.add_edge(source, target, edge.get('type', 'RELATED_TO'), edge)
    
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
    
    # Restore graph state
    graph_engine.clear()
    for node in next_state.get('nodes', []):
        graph_engine.add_node(node['id'], node.get('type', 'Entity'), node)
    for edge in next_state.get('edges', []):
        source = edge.get('source') or edge.get('source_id')
        target = edge.get('target') or edge.get('target_id')
        graph_engine.add_edge(source, target, edge.get('type', 'RELATED_TO'), edge)
    
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

