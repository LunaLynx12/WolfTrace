# WolfTrace

<div align="center">

![WolfTrace Logo](https://img.shields.io/badge/WolfTrace-Graph%20Visualization-blue?style=for-the-badge)

**A powerful, modular graph visualization and analysis tool for cybersecurity professionals**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![SvelteKit](https://img.shields.io/badge/sveltekit-latest-orange.svg)](https://kit.svelte.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-success.svg)](https://github.com)

[Features](#-features) • [Installation](#-installation) • [Documentation](#-documentation) • [Contributing](#-contributing) • [License](#-license)

</div>

---

## 📖 Overview

**WolfTrace** is an open-source, modular graph visualization and analysis platform designed for cybersecurity professionals. Inspired by BloodHound but built for broader use cases, WolfTrace enables you to visualize and analyze complex relationship graphs across multiple domains including:

- 🌐 **Network Topology** - Map network connections, hosts, and services
- 🏢 **Active Directory** - Visualize AD relationships and attack paths
- ☁️ **Cloud Infrastructure** - Map cloud resources and dependencies
- 🔐 **IAM Systems** - Analyze identity and access management relationships
- 📊 **Custom Domains** - Extensible plugin system for any graph-based data

### Why WolfTrace?

- **🔌 Modular Architecture** - Extensible plugin system for custom data collectors
- **🎯 Multi-Domain Support** - Not limited to Active Directory
- **🚀 Easy to Use** - Intuitive web interface with powerful backend API
- **📈 Advanced Analytics** - Built-in graph algorithms and metrics
- **🔍 Intelligent Detection** - Automatic plugin detection based on data structure
- **💾 Session Management** - Save and restore analysis sessions
- **📝 Comprehensive Reports** - Generate detailed analysis reports

## ✨ Features

### Core Capabilities

- **🔌 Modular Plugin System** - Easily add new data collectors and parsers
- **📊 Interactive Graph Visualization** - Beautiful, interactive web-based graph UI
- **🔍 Path Finding** - Discover attack paths and relationships between nodes
- **📈 Graph Analytics** - Advanced metrics including centrality, communities, and more
- **🔄 Session Management** - Save and restore graph states
- **📝 Report Generation** - Generate HTML and JSON reports
- **⏪ Undo/Redo** - Full operation history with undo/redo support
- **🏷️ Bulk Operations** - Efficient batch operations on nodes and edges
- **📋 Graph Templates** - Reusable graph structure templates
- **🔀 Graph Comparison** - Compare and diff multiple graph states
- **🔎 Advanced Querying** - Powerful filtering and search capabilities

### Technical Features

- **RESTful API** - Comprehensive REST API with OpenAPI documentation
- **Auto-Detection** - Intelligent plugin detection based on data structure
- **Multiple Formats** - Support for JSON, ZIP archives, and more
- **Scalable** - Supports both in-memory (NetworkX) and Neo4j backends
- **Professional Logging** - Advanced logging with rotation and structured output
- **Type Safety** - Python type hints throughout the codebase

## 🏗️ Architecture

```
WolfTrace/
├── backend/              # Python Flask API Server
│   ├── plugins/          # Modular data collectors
│   ├── config/           # Configuration files
│   ├── data/             # Data storage
│   │   ├── examples/     # Sample data files
│   │   ├── sessions/     # Saved sessions
│   │   └── templates/    # Graph templates
│   ├── examples/         # Code examples
│   └── logs/             # Application logs
└── frontend/             # SvelteKit Web UI
    └── src/
        ├── components/   # React/Svelte components
        └── routes/       # Application routes
```

### Technology Stack

**Backend:**
- Python 3.8+
- Flask 3.0 - REST API framework
- NetworkX - Graph algorithms and storage
- Neo4j (optional) - Graph database support
- Flask-CORS - Cross-origin resource sharing

**Frontend:**
- SvelteKit - Modern web framework
- Bun - Fast JavaScript runtime
- D3.js / Cytoscape.js - Graph visualization

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Bun** - [Install Bun](https://bun.sh/docs/installation)
- **Git** (for cloning)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/WolfTrace.git
cd WolfTrace
```

2. **Install backend dependencies:**
```bash
cd backend
pip install -r requirements.txt
# Or on Linux/Mac: pip3 install -r requirements.txt
```

3. **Install frontend dependencies:**
```bash
cd ../frontend
bun install
```

### Running the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
python app.py
# Or: python3 app.py
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
bun run dev
```

**Access the application:**
- 🌐 **Frontend UI:** http://localhost:3000
- 🔌 **Backend API:** http://localhost:5000
- 📚 **API Docs:** http://localhost:5000/docs

## 📚 Documentation

### API Documentation

- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc
- **OpenAPI Spec:** http://localhost:5000/openapi.json

### Backend Documentation

Comprehensive backend documentation is available in [`backend/README.md`](backend/README.md), including:
- Architecture overview
- Core components
- Plugin development guide
- Code examples
- API reference

### Frontend Documentation

The frontend is a modern, interactive web application built with SvelteKit that provides a rich graph visualization interface.

#### Frontend Features

- **🎨 Interactive Graph Visualization** - Beautiful, responsive graph rendering with D3.js and Force Graph
- **🔍 Advanced Search** - Real-time node and edge search with filtering
- **📊 Analytics Panel** - View graph statistics, centrality metrics, and community detection
- **📝 Query Builder** - Build complex queries to filter and analyze graph data
- **💾 Session Management** - Save, load, and manage graph analysis sessions
- **📋 Graph Templates** - Use pre-built templates for common graph structures
- **🔄 History Controls** - Undo/redo functionality for graph operations
- **📈 Report Generation** - Export analysis reports in multiple formats
- **🔀 Graph Comparison** - Compare different graph states side-by-side
- **⚡ Bulk Operations** - Perform batch operations on nodes and edges
- **🏷️ Node Grouping** - Organize and group related nodes
- **📝 Node Notes** - Add annotations and notes to nodes
- **⌨️ Keyboard Shortcuts** - Power user shortcuts for faster navigation

#### Frontend Technology Stack

- **SvelteKit** - Modern full-stack framework with server-side rendering
- **D3.js** - Data visualization and graph layout algorithms
- **Force Graph** - Force-directed graph visualization library
- **Axios** - HTTP client for API communication
- **Vite** - Fast build tool and development server
- **TypeScript** - Type-safe JavaScript development

#### Frontend Structure

```
frontend/
├── src/
│   ├── components/          # Reusable Svelte components
│   │   ├── AnalyticsPanel.svelte
│   │   ├── GraphStatsWidget.svelte
│   │   ├── QueryBuilder.svelte
│   │   ├── SessionManager.svelte
│   │   ├── SearchBar.svelte
│   │   └── ...              # More components
│   ├── routes/              # SvelteKit routes
│   │   ├── +page.svelte     # Main page
│   │   └── +layout.svelte   # Layout wrapper
│   └── utils/               # Utility functions
│       └── cache.js         # Client-side caching
├── public/                  # Static assets
├── package.json             # Dependencies
└── vite.config.js          # Vite configuration
```

#### Frontend Development

**Installation:**
```bash
cd frontend
bun install
```

**Development Server:**
```bash
bun run dev
# Frontend will be available at http://localhost:3000
```

**Build for Production:**
```bash
bun run build
```

**Preview Production Build:**
```bash
bun run preview
```

**Type Checking:**
```bash
bun run check
```

#### Frontend Configuration

The frontend is configured to proxy API requests to the backend. Configuration is in `frontend/vite.config.js`:

```javascript
// API proxy configuration
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

#### Frontend Components Overview

- **Graph Visualization** - Main graph canvas with zoom, pan, and node interaction
- **Analytics Panel** - Displays graph metrics, centrality scores, and community information
- **Search Bar** - Real-time search with autocomplete and filtering
- **Query Builder** - Visual query builder for complex graph queries
- **Session Manager** - Save, load, and manage analysis sessions
- **History Controls** - Undo/redo for graph operations
- **Report Generator** - Generate and export analysis reports
- **Graph Comparison** - Compare multiple graph states
- **Bulk Operations** - Batch edit nodes and edges
- **Node Grouping** - Organize nodes into groups
- **Node Notes** - Add annotations to nodes
- **Keyboard Shortcuts** - Power user keyboard navigation

#### Frontend Development Guidelines

- **Component Structure:** Use Svelte components with `.svelte` extension
- **State Management:** Use Svelte stores for shared state
- **API Communication:** Use Axios for all backend API calls
- **Styling:** Use component-scoped CSS in `<style>` tags
- **Type Safety:** TypeScript support is available for type checking
- **Responsive Design:** Ensure components work on desktop and mobile

### Quick Examples

#### Import Data via API

```bash
curl -X POST http://localhost:5000/api/import-autodetect \
  -H "Content-Type: application/json" \
  -d @backend/data/examples/example_network.json
```

#### Find Paths Between Nodes

```bash
curl -X POST http://localhost:5000/api/paths \
  -H "Content-Type: application/json" \
  -d '{
    "source": "192.168.1.1",
    "target": "192.168.1.100",
    "max_depth": 5
  }'
```

#### Get Graph Statistics

```bash
curl http://localhost:5000/api/analytics/stats
```

For more examples, see [`backend/examples/api_example.py`](backend/examples/api_example.py)

## 🔌 Plugin Development

WolfTrace's power comes from its modular plugin system. Create custom plugins to process any data format.

### Creating a Plugin

1. **Create plugin directory:**
```bash
mkdir -p backend/plugins/your-plugin
cd backend/plugins/your-plugin
```

2. **Create `metadata.json`:**
```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "Processes your custom data format",
  "supported_formats": ["json"],
  "detection_hints": ["your_key", "your_indicator"]
}
```

3. **Create `plugin.py`:**
```python
from typing import Dict, Any

def process(data: Any, graph_engine) -> Dict[str, Any]:
    """Process data and add nodes/edges to graph"""
    nodes_added = 0
    edges_added = 0
    
    # Your processing logic here
    for item in data.get('items', []):
        graph_engine.add_node(
            node_id=item['id'],
            node_type=item.get('type', 'Entity'),
            properties=item
        )
        nodes_added += 1
    
    return {
        'nodes_added': nodes_added,
        'edges_added': edges_added,
        'status': 'success'
    }
```

4. **Restart the backend** - Your plugin will be automatically loaded!

See [`backend/README.md`](backend/README.md#plugin-development) for detailed plugin development guide.

## 🎯 Use Cases

### Network Security Analysis
- Map network topology from scan results
- Identify attack paths between hosts
- Analyze service dependencies
- Visualize network segmentation

### Active Directory Security
- Import BloodHound-compatible data
- Find privilege escalation paths
- Analyze group memberships
- Map domain relationships

### Cloud Security
- Visualize cloud resource relationships
- Map IAM permissions and roles
- Identify misconfigurations
- Track resource dependencies

### Custom Analysis
- Create plugins for any data format
- Build custom analysis workflows
- Integrate with existing tools
- Extend functionality as needed

## 🛠️ Development

### Project Structure

```
WolfTrace/
├── backend/              # Backend API server
│   ├── app.py           # Main Flask application
│   ├── graph_engine.py  # Core graph engine
│   ├── plugin_manager.py # Plugin management
│   ├── plugins/         # Plugin directory
│   └── README.md        # Backend documentation
├── frontend/            # Frontend web application
│   ├── src/            # Source code
│   └── package.json    # Dependencies
└── README.md           # This file
```

### Development Setup

1. **Clone and install dependencies** (see Installation above)

2. **Set up environment variables:**
```bash
cd backend
cat > .env << EOF
PORT=5000
LOG_LEVEL=DEBUG
NEO4J_URI=bolt://localhost:7687  # Optional
NEO4J_USER=neo4j                 # Optional
NEO4J_PASSWORD=your_password      # Optional
EOF
```

3. **Run in development mode:**
```bash
# Backend (with auto-reload)
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Frontend (with hot-reload)
cd frontend
bun run dev
```

### Code Style

- **Python:** Follow PEP 8, use type hints
- **JavaScript/TypeScript:** Follow standard conventions
- **Documentation:** Include docstrings for all functions
- **Testing:** Write tests for new features

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs** - Open an issue with detailed information
- 💡 **Suggest Features** - Share your ideas for improvements
- 📝 **Improve Documentation** - Help make docs better
- 🔌 **Create Plugins** - Add support for new data formats
- 🧪 **Write Tests** - Improve test coverage
- 🔧 **Fix Issues** - Submit pull requests

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear commit messages
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

### Development Guidelines

- Follow existing code style and patterns
- Add docstrings to new functions/classes
- Update relevant documentation
- Test your changes before submitting
- Keep commits focused and atomic

### Plugin Contributions

We especially welcome plugin contributions! See the [Plugin Development](#-plugin-development) section above.

## 📊 API Overview

### Key Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Graph** | `/api/graph` | GET | Get full graph data |
| **Graph** | `/api/nodes` | GET | Get nodes (filtered) |
| **Graph** | `/api/paths` | POST | Find paths between nodes |
| **Import** | `/api/import-autodetect` | POST | Import with auto-detection |
| **Analytics** | `/api/analytics/stats` | GET | Get graph statistics |
| **Sessions** | `/api/sessions` | GET/POST | Manage sessions |
| **Query** | `/api/query` | POST | Advanced queries |
| **Plugins** | `/api/plugins` | GET | List available plugins |

**Full API Documentation:** http://localhost:5000/docs

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Server Configuration
PORT=5000

# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_JSON=false          # Enable JSON structured logging

# Neo4j (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Logging

Logs are stored in `backend/logs/`:
- `wolftrace.log` - Application logs
- `errors.log` - Error logs only
- `access.log` - HTTP request logs

Logs are automatically rotated when they reach 10MB.

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Change backend port
export PORT=5001
python app.py

# Change frontend port (in frontend/vite.config.js)
```

**Module Not Found:**
```bash
# Ensure you're in the correct directory
cd backend
pip install -r requirements.txt
```

**Plugin Not Loading:**
- Check plugin directory structure
- Verify `plugin.py` has `process()` function
- Check `metadata.json` format
- Review backend logs in `backend/logs/`

**CORS Errors:**
- Ensure backend is running on correct port
- Check `frontend/vite.config.js` proxy configuration

## 📦 Available Plugins

WolfTrace comes with several built-in plugins:

- **network** - Network topology and scanning data
- **nmap** - Nmap XML scan results
- **ad** - Active Directory (BloodHound-compatible)
- **iam** - Identity and Access Management
- **cloud** - Cloud infrastructure
- **csv** - CSV data import

See [`backend/plugins/`](backend/plugins/) for plugin implementations.

## 🗺️ Roadmap

- [ ] Real-time graph updates via WebSockets
- [ ] Additional graph algorithms
- [ ] Export to more formats (PDF, PNG, SVG)
- [ ] Plugin marketplace
- [ ] Advanced visualization options
- [ ] Multi-user support
- [ ] Graph database persistence improvements

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [BloodHound](https://github.com/BloodHoundAD/BloodHound)
- Built with [Flask](https://flask.palletsprojects.com/) and [SvelteKit](https://kit.svelte.dev/)
- Graph algorithms powered by [NetworkX](https://networkx.org/)

## 📞 Support

- **Documentation:** See [`backend/README.md`](backend/README.md) for detailed API docs
- **Issues:** [GitHub Issues](https://github.com/yourusername/WolfTrace/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/WolfTrace/discussions)

## ⭐ Star History

If you find WolfTrace useful, please consider giving it a star! ⭐

---

<div align="center">

**Built with ❤️ for cybersecurity professionals**

[Report Bug](https://github.com/yourusername/WolfTrace/issues) • [Request Feature](https://github.com/yourusername/WolfTrace/issues) • [Contribute](https://github.com/yourusername/WolfTrace/pulls)

</div>
