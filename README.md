# WolfTrace - Modular Graph Visualization Tool

A flexible, modular graph visualization tool inspired by BloodHound, designed for cybersecurity analysis across multiple domains (not just Active Directory).

## Features

- 🔌 **Modular Plugin System** - Easily add new data collectors and parsers
- 📊 **Graph Visualization** - Interactive graph UI for relationship analysis
- 🔍 **Path Finding** - Discover attack paths and relationships
- 🎯 **Multi-Domain Support** - Works with any graph-based data (AD, cloud, network, etc.)
- 📦 **Easy Deployment** - Package as ZIP for distribution

## Architecture

```
WolfTrace/
├── backend/          # API server and graph engine
├── frontend/         # Web UI (SvelteKit)
├── plugins/          # Modular data collectors
├── config/           # Configuration files
└── data/            # Sample data and schemas
```

## Prerequisites

- **Python 3.8+** (for backend)
- **Bun** (for frontend) - [Install Bun](https://bun.sh/docs/installation)
- **pip** (Python package manager)

## Installation

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note for Linux/Mac users:** You may need to use `pip3` instead of `pip`, and `python3` instead of `python`.

### 2. Install Frontend Dependencies

```bash
cd frontend
bun install
```

## Running the Application

WolfTrace requires two servers to run: the backend API server and the frontend development server.

### Option 1: Run in Separate Terminals (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun run dev
```

**Note for Linux/Mac:** Use `python3` instead of `python` if needed.

### Option 2: Run Both in Background (Linux/Mac)

```bash
# Start backend in background
cd backend && python3 app.py > ../backend.log 2>&1 &

# Start frontend in background
cd frontend && bun run dev > ../frontend.log 2>&1 &

# View logs
tail -f backend.log frontend.log
```

### Option 3: Using Docker

```bash
docker-compose up
```

## Access the Application

Once both servers are running:
- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Health Check:** http://localhost:5000/api/health

## Usage Examples

### Import Network Data
1. Use the "network" plugin
2. Upload a JSON file with network topology (see `data/example_network.json`)
3. Visualize network connections and relationships

### Import Cloud Infrastructure
1. Use the "cloud" plugin
2. Upload cloud resource data (see `data/example_cloud.json`)
3. Map cloud resource relationships and dependencies

### Find Attack Paths
1. Import your data
2. Enter source and target node IDs
3. Click "Find Paths" to discover relationships

## Adding Custom Collectors

Create a new plugin in `plugins/` following the plugin interface. Each plugin must have a `process(data, graph_engine)` function.

Example plugin structure:
```
plugins/
  your-plugin/
    plugin.py      # Must have process(data, graph_engine) function
    metadata.json  # Plugin metadata
```

The `process` function receives:
- `data`: The data to process (can be JSON, text, etc.)
- `graph_engine`: The GraphEngine instance to add nodes/edges to

Example:
```python
def process(data, graph_engine):
    # Parse your data
    nodes = parse_data(data)
    
    # Add nodes and edges to graph
    for node in nodes:
        graph_engine.add_node(node['id'], node['type'], node.get('properties', {}))
    
    # Add edges
    for edge in edges:
        graph_engine.add_edge(edge['source'], edge['target'], edge.get('type', 'RELATED_TO'))
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/graph` - Get full graph
- `GET /api/nodes?type=Host` - Get nodes (optionally filtered)
- `GET /api/edges?type=CONNECTS_TO` - Get edges (optionally filtered)
- `POST /api/import` - Import data via plugin
- `POST /api/paths` - Find paths between nodes
- `GET /api/plugins` - List available plugins
- `POST /api/clear` - Clear graph

For a complete list of API endpoints, see the backend code in `backend/app.py`.

## Packaging for Distribution

To create a ZIP package for distribution, exclude the following directories:
- `node_modules/` or `.bun/` (frontend dependencies)
- `venv/` or `env/` (Python virtual environment)
- `__pycache__/` (Python cache)
- `.git/` (Git repository)
- `.svelte-kit/` (SvelteKit build cache)
- `frontend/build/` or `frontend/dist/` (build artifacts)

### Windows (PowerShell)
```powershell
Get-ChildItem -Path . -Recurse | Where-Object { 
    $_.FullName -notmatch 'node_modules|venv|__pycache__|\.git|\.svelte-kit|build|dist' 
} | Compress-Archive -DestinationPath WolfTrace.zip -Force
```

### Linux/Mac
```bash
zip -r WolfTrace.zip . -x "node_modules/*" "venv/*" "__pycache__/*" ".git/*" ".svelte-kit/*" "frontend/build/*" "frontend/dist/*"
```

## Troubleshooting

### Port Already in Use
If port 3000 or 5000 is already in use:
- **Backend:** Change port in `backend/app.py` (default: 5000)
- **Frontend:** Change port in `frontend/vite.config.js` (default: 3000)

### Python Not Found (Linux/Mac)
Use `python3` instead of `python`:
```bash
python3 app.py
```

### Module Not Found Errors
Ensure you're in the correct directory and have installed dependencies:
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && bun install
```

### CORS Errors
The frontend proxy is configured in `frontend/vite.config.js`. Ensure the backend is running on the correct port (default: 5000).

## Development

### Backend Development
- Backend uses Flask (Python)
- Main application: `backend/app.py`
- Graph engine: `backend/graph_engine.py`
- Plugins: `plugins/*/plugin.py`

### Frontend Development
- Frontend uses SvelteKit with Bun
- Main app: `frontend/src/routes/+page.svelte`
- Components: `frontend/src/components/*.svelte`
- Build with: `bun run build`
- Preview build: `bun run preview`

## License

MIT
