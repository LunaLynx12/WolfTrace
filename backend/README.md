# WolfTrace Backend API

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, modular REST API for graph-based cybersecurity analysis and visualization. WolfTrace Backend provides a flexible framework for importing, analyzing, and visualizing complex relationship graphs across multiple domains including network topology, Active Directory, cloud infrastructure, and IAM systems.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Core Components](#core-components)
- [Plugin Development](#plugin-development)
- [Code Examples](#code-examples)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)

## Features

- 🔌 **Modular Plugin System** - Extensible architecture for custom data collectors
- 📊 **Graph Analytics** - Advanced graph algorithms and metrics (centrality, communities, paths)
- 🔍 **Intelligent Auto-Detection** - Automatic plugin detection based on data structure
- 📦 **Multiple Import Formats** - JSON, ZIP archives, and automatic format detection
- 🔄 **Session Management** - Save and restore graph states
- 📈 **Query Builder** - Advanced filtering and querying capabilities
- 🔀 **Graph Comparison** - Compare and diff multiple graph states
- 📝 **Report Generation** - Generate HTML and JSON reports
- ⏪ **History/Undo-Redo** - Full operation history with undo/redo support
- 🏷️ **Bulk Operations** - Efficient batch operations on nodes and edges
- 📋 **Graph Templates** - Reusable graph structure templates

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│                      (app.py)                            │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│ Graph Engine │   │ Plugin Manager  │  │  Analytics  │
│              │   │                  │  │             │
│ - NetworkX   │   │ - Auto-detect   │  │ - Stats     │
│ - Neo4j      │   │ - Load plugins  │  │ - Centrality│
└──────────────┘   └──────────────────┘  └─────────────┘
        │                   │
        └───────────────────┼───────────────────┐
                            │                   │
                   ┌────────▼────────┐  ┌───────▼────────┐
                   │ Query Builder  │  │ Session Mgr    │
                   │                 │  │                │
                   │ - Filters       │  │ - Save/Load    │
                   │ - Search        │  │ - Restore      │
                   └─────────────────┘  └────────────────┘
```

### Core Modules

| Module | Purpose | Key Responsibilities |
|--------|---------|---------------------|
| `graph_engine.py` | Graph storage and operations | Node/edge management, path finding, graph queries |
| `plugin_manager.py` | Plugin lifecycle management | Plugin loading, auto-detection, execution |
| `graph_analytics.py` | Graph analysis and metrics | Statistics, centrality, communities, neighbors |
| `query_builder.py` | Advanced querying | Filtering, search, date ranges, degree filtering |
| `session_manager.py` | Session persistence | Save/load/restore graph states |
| `graph_comparison.py` | Graph diffing | Compare graphs, find differences |
| `report_generator.py` | Report creation | Generate HTML/JSON reports |
| `bulk_operations.py` | Batch operations | Bulk delete/update/tag operations |
| `graph_templates.py` | Template management | Create graphs from templates |
| `history_manager.py` | Operation history | Undo/redo functionality |

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository** (if not already done):
```bash
git clone https://github.com/yourusername/WolfTrace.git
cd WolfTrace/backend
```

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables** (optional):
```bash
# Create .env file in backend directory
cat > .env << EOF
PORT=5000
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
EOF
```

5. **Run the server**:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Quick Start

### 1. Check API Health

```bash
curl http://localhost:5000/api/health
```

Response:
```json
{
  "status": "ok"
}
```

### 2. List Available Plugins

```bash
curl http://localhost:5000/api/plugins
```

### 3. Import Data

```bash
curl -X POST http://localhost:5000/api/import-autodetect \
  -H "Content-Type: application/json" \
  -d @data/examples/example_network.json
```

### 4. Get Graph Data

```bash
curl http://localhost:5000/api/graph
```

## API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc
- **OpenAPI Spec**: http://localhost:5000/openapi.json

### Key Endpoints

#### Graph Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph` | GET | Get full graph (nodes + edges) |
| `/api/nodes` | GET | Get all nodes (optionally filtered by type) |
| `/api/edges` | GET | Get all edges (optionally filtered by type) |
| `/api/paths` | POST | Find paths between two nodes |
| `/api/search` | GET | Search nodes by ID or properties |
| `/api/clear` | POST | Clear all graph data |

#### Data Import

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/import` | POST | Import data with specified plugin |
| `/api/import-autodetect` | POST | Import data with automatic plugin detection |
| `/api/import-zip` | POST | Import ZIP archive with specified plugin |
| `/api/import-zip-autodetect` | POST | Import ZIP archive with auto-detection |

#### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/stats` | GET | Get comprehensive graph statistics |
| `/api/analytics/communities` | GET | Find communities in the graph |
| `/api/analytics/neighbors` | GET | Get neighbors of a node |

#### Sessions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List all saved sessions |
| `/api/sessions` | POST | Save current graph as session |
| `/api/sessions/<id>` | GET | Load a specific session |
| `/api/sessions/<id>/restore` | POST | Restore session to current graph |

For complete API documentation, visit `/docs` or `/redoc` when the server is running.

## Core Components

### GraphEngine

The core graph storage and manipulation engine. Supports both in-memory NetworkX graphs and Neo4j databases.

**Key Methods:**

```python
from graph_engine import GraphEngine

# Initialize (default: in-memory NetworkX)
engine = GraphEngine()

# Add a node
engine.add_node(
    node_id="192.168.1.1",
    node_type="Host",
    properties={"hostname": "server1", "os": "Linux"}
)

# Add an edge
engine.add_edge(
    source="192.168.1.1",
    target="192.168.1.2",
    edge_type="CONNECTS_TO",
    properties={"port": 443, "protocol": "tcp"}
)

# Query nodes
nodes = engine.get_nodes(node_type="Host")

# Find paths
paths = engine.find_paths("192.168.1.1", "192.168.1.10", max_depth=5)

# Get full graph
graph_data = engine.get_full_graph()
```

**Neo4j Support:**

```python
# Use Neo4j instead of in-memory graph
engine = GraphEngine(use_neo4j=True)
# Requires NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in environment
```

### PluginManager

Manages plugin loading, execution, and automatic detection.

**Key Methods:**

```python
from plugin_manager import PluginManager
from pathlib import Path

# Initialize plugin manager
plugins_path = Path(__file__).parent / 'plugins'
pm = PluginManager(plugins_dir=str(plugins_path))

# List available plugins
plugins = pm.list_plugins()
# Returns: [{'name': 'network', 'version': '1.0.0', ...}, ...]

# Process data with specific plugin
result = pm.process_data('network', data_dict, graph_engine)

# Auto-detect plugin for data
detected_plugin = pm.detect_plugin(data_dict)
if detected_plugin:
    result = pm.process_data(detected_plugin, data_dict, graph_engine)
```

### GraphAnalytics

Provides graph analysis and metrics.

```python
from graph_analytics import GraphAnalytics

analytics = GraphAnalytics(graph_engine)

# Get comprehensive statistics
stats = analytics.get_statistics()
# Returns: {
#   'basic': {'nodes': 100, 'edges': 250, ...},
#   'node_types': {'Host': 50, 'User': 30, ...},
#   'top_nodes_by_degree': [...],
#   'is_connected': True,
#   ...
# }

# Find communities
communities = analytics.find_communities(max_communities=10)

# Get node neighbors
neighbors = analytics.get_node_neighbors('node_id', depth=2)
```

### QueryBuilder

Advanced querying and filtering capabilities.

```python
from query_builder import QueryBuilder

qb = QueryBuilder(graph_engine)

# Build complex query
filters = {
    'node_type': ['Host', 'Server'],
    'properties': {'os': 'Linux'},
    'text_search': 'production',
    'min_degree': 2,
    'max_degree': 10,
    'date_range': {
        'field': 'created_at',
        'start': '2024-01-01',
        'end': '2024-12-31'
    }
}

result = qb.build_query(filters)
# Returns: {'nodes': [...], 'edges': [...], 'count': 42}

# Get statistics for query
stats = qb.get_statistics_for_query(filters)
```

## Plugin Development

### Creating a Custom Plugin

Plugins are modular data processors that convert various data formats into graph structures. Each plugin is a directory containing:

```
plugins/
  your-plugin/
    plugin.py          # Required: Main plugin code
    metadata.json      # Required: Plugin metadata
```

### Plugin Structure

#### 1. Create Plugin Directory

```bash
mkdir -p plugins/your-plugin
cd plugins/your-plugin
```

#### 2. Create `metadata.json`

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "Processes your custom data format",
  "supported_formats": ["json", "csv"],
  "detection_hints": ["your_key", "your_indicator"],
  "priority": 3
}
```

#### 3. Create `plugin.py`

```python
"""
Your Plugin - Processes custom data format
"""
from typing import Dict, Any, List

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """
    Process data and add nodes/edges to graph
    
    Args:
        data: Input data (dict, list, string, etc.)
        graph_engine: GraphEngine instance to add nodes/edges to
    
    Returns:
        Dictionary with processing results:
        {
            'nodes_added': int,
            'edges_added': int,
            'status': 'success',
            ... (any additional metadata)
        }
    """
    nodes_added = 0
    edges_added = 0
    
    # Parse your data format
    if isinstance(data, dict):
        # Example: Process network hosts
        for host in data.get('hosts', []):
            host_id = host.get('ip') or host.get('hostname')
            host_type = host.get('type', 'Host')
            
            # Add node
            graph_engine.add_node(
                node_id=host_id,
                node_type=host_type,
                properties=host
            )
            nodes_added += 1
            
            # Add connections
            for connection in host.get('connections', []):
                target = connection.get('target')
                if target:
                    graph_engine.add_edge(
                        source=host_id,
                        target=target,
                        edge_type=connection.get('type', 'CONNECTS_TO'),
                        properties=connection
                    )
                    edges_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'status': 'success'
    }
```

### Plugin Auto-Detection

The plugin manager automatically detects which plugin to use based on data structure. You can improve detection by:

1. **Adding detection hints in metadata.json:**
```json
{
  "detection_hints": ["hosts", "servers", "network_topology"]
}
```

2. **Using specific data structures** that the detector recognizes:
   - IP addresses as keys → network plugin
   - `users` + `groups` → AD/IAM plugin
   - `resources` + `provider` → cloud plugin

### Example Plugin: Network Scanner

See `plugins/network/plugin.py` for a complete example of a network topology processor.

## Code Examples

### Example 1: Programmatic API Usage

```python
import requests
import json

API_BASE = "http://localhost:5000/api"

# 1. Import data with auto-detection
with open('network_data.json', 'r') as f:
    data = json.load(f)

response = requests.post(
    f"{API_BASE}/import-autodetect",
    json={"data": data}
)
result = response.json()
print(f"Added {result['nodes_added']} nodes, {result['edges_added']} edges")

# 2. Find paths between nodes
paths_response = requests.post(
    f"{API_BASE}/paths",
    json={
        "source": "192.168.1.1",
        "target": "192.168.1.100",
        "max_depth": 5
    }
)
paths = paths_response.json()
for i, path in enumerate(paths, 1):
    print(f"Path {i}: {' -> '.join(path)}")

# 3. Get graph statistics
stats_response = requests.get(f"{API_BASE}/analytics/stats")
stats = stats_response.json()
print(f"Graph has {stats['basic']['nodes']} nodes")
print(f"Top node by degree: {stats['top_nodes_by_degree'][0] if stats['top_nodes_by_degree'] else 'N/A'}")

# 4. Save session
session_response = requests.post(
    f"{API_BASE}/sessions",
    json={
        "name": "My Analysis Session",
        "metadata": {"description": "Network topology analysis"}
    }
)
session_id = session_response.json()['id']
print(f"Session saved: {session_id}")
```

### Example 2: Direct Backend Usage

```python
from graph_engine import GraphEngine
from plugin_manager import PluginManager
from graph_analytics import GraphAnalytics
from pathlib import Path

# Initialize components
engine = GraphEngine()
plugins_path = Path(__file__).parent / 'plugins'
pm = PluginManager(plugins_dir=str(plugins_path))
analytics = GraphAnalytics(engine)

# Load and process data
with open('data.json', 'r') as f:
    data = json.load(f)

# Auto-detect and process
plugin_name = pm.detect_plugin(data)
if plugin_name:
    result = pm.process_data(plugin_name, data, engine)
    print(f"Processed with {plugin_name}: {result}")

# Analyze graph
stats = analytics.get_statistics()
print(f"Graph metrics: {stats['basic']}")

# Find communities
communities = analytics.find_communities(max_communities=5)
for community in communities:
    print(f"Community {community['id']}: {community['size']} nodes")
```

### Example 3: Custom Plugin Integration

```python
from graph_engine import GraphEngine
from plugin_manager import PluginManager

# Initialize
engine = GraphEngine()
pm = PluginManager(plugins_dir='plugins')

# Your custom data
custom_data = {
    "devices": [
        {"id": "device1", "type": "Router", "ip": "10.0.0.1"},
        {"id": "device2", "type": "Switch", "ip": "10.0.0.2"}
    ],
    "connections": [
        {"from": "device1", "to": "device2", "type": "ETHERNET"}
    ]
}

# Process with your plugin
result = pm.process_data('your-plugin', custom_data, engine)
print(f"Added {result['nodes_added']} nodes")
```

### Example 4: Advanced Querying

```python
from query_builder import QueryBuilder

qb = QueryBuilder(graph_engine)

# Complex multi-filter query
filters = {
    'node_type': ['Host', 'Server'],
    'properties': {
        'os': 'Linux',
        'environment': 'production'
    },
    'text_search': 'web',
    'min_degree': 3,
    'date_range': {
        'field': 'last_seen',
        'start': '2024-01-01',
        'end': '2024-12-31'
    }
}

# Execute query
results = qb.build_query(filters)
print(f"Found {results['count']} matching nodes")

# Get statistics
stats = qb.get_statistics_for_query(filters)
print(f"Node types: {stats['node_types']}")
print(f"Edge types: {stats['edge_types']}")
```

### Example 5: Graph Comparison

```python
from graph_comparison import GraphComparison

comparison = GraphComparison(graph_engine)

# Get two graph states
graph1 = engine.get_full_graph()
# ... make some changes ...
graph2 = engine.get_full_graph()

# Compare
diff = comparison.compare_graphs(graph1, graph2)
print(f"Added: {diff['stats']['nodes']['added']} nodes")
print(f"Removed: {diff['stats']['nodes']['removed']} nodes")
print(f"Changed: {diff['stats']['nodes']['changed']} nodes")

# Get visualization graph
diff_graph = comparison.create_diff_graph(diff)
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Server Configuration
PORT=5000

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Logging
LOG_LEVEL=INFO
```

### Configuration Schema

See `config/schema.json` for the complete configuration schema.

## Development

### Project Structure

```
backend/
├── app.py                 # Main Flask application
├── graph_engine.py        # Core graph engine
├── plugin_manager.py      # Plugin management system
├── graph_analytics.py     # Analytics and metrics
├── query_builder.py       # Advanced querying
├── session_manager.py     # Session persistence
├── graph_comparison.py   # Graph diffing
├── report_generator.py   # Report generation
├── bulk_operations.py   # Batch operations
├── graph_templates.py   # Template management
├── history_manager.py   # Undo/redo
├── openapi_spec.py      # API documentation
├── plugins/             # Plugin directory
│   ├── network/
│   ├── ad/
│   └── ...
├── data/                # Data storage
│   ├── examples/        # Example data files
│   ├── sessions/        # Saved sessions
│   └── templates/       # Graph templates
├── config/              # Configuration files
└── examples/            # Code examples
```

### Running in Development

```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with auto-reload
python app.py
```

### Testing

```bash
# Run example script
python examples/api_example.py

# Test API endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/plugins
```

### Logging

Logs are written to:
- Console (stdout)
- File: `wolftrace.log`

Log format:
```
2024-11-29 17:30:45,123 - werkzeug - INFO - 127.0.0.1 - - [29/Nov/2024 17:30:45] "GET /api/health HTTP/1.1" 200 -
```

## Contributing

### Adding New Features

1. **New Endpoints**: Add routes in `app.py`
2. **New Plugins**: Create plugin directory in `plugins/`
3. **New Analytics**: Extend `GraphAnalytics` class
4. **New Query Types**: Extend `QueryBuilder` class

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where possible
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

### Testing Your Changes

1. Test locally with example data
2. Verify API endpoints work correctly
3. Check OpenAPI documentation updates
4. Test plugin auto-detection if adding new plugins

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Update documentation
6. Submit pull request

## API Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "metadata": { ... }
}
```

### Error Response

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Performance Considerations

- **In-Memory Graph**: Fast for graphs up to ~100K nodes
- **Neo4j**: Recommended for larger graphs (>100K nodes)
- **Pagination**: Use `/api/graph/paginated` for large graphs
- **Caching**: Plugin detection results are cached for performance

## Security Notes

- CORS is enabled by default (configure for production)
- No authentication by default (add middleware for production)
- Input validation should be added for production use
- Sanitize user inputs in custom plugins

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: `/docs` (Swagger UI) or `/redoc`
- **Issues**: GitHub Issues
- **Examples**: See `examples/` directory

---

**Built with ❤️ for cybersecurity professionals**

