"""
Example: Using WolfTrace API programmatically
"""
import requests
import json

API_BASE = "http://localhost:5000/api"

# Example 1: Import web reconnaissance data
def import_web_data():
    # Real data is in real_data/WEB_DATA folder
    import os
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    metadata_file = project_root / 'real_data' / 'WEB_DATA' / 'metadata.json'
    
    if not metadata_file.exists():
        print(f"Real data not found at {metadata_file}")
        print("Please ensure real_data/WEB_DATA folder exists with metadata.json")
        return
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Use autodetect to automatically detect and process the data
    response = requests.post(
        f"{API_BASE}/import-autodetect",
        json={
            "data": metadata
        }
    )
    print("Import result:", response.json())

# Example 2: Find paths
def find_paths(source, target):
    response = requests.post(
        f"{API_BASE}/paths",
        json={
            "source": source,
            "target": target,
            "max_depth": 5
        }
    )
    paths = response.json()
    print(f"Found {len(paths)} path(s) from {source} to {target}")
    for i, path in enumerate(paths, 1):
        print(f"  Path {i}: {' -> '.join(path)}")

# Example 3: Get graph statistics
def get_graph_stats():
    response = requests.get(f"{API_BASE}/graph")
    graph = response.json()
    print(f"Graph contains {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")

# Example 4: List available plugins
def list_plugins():
    response = requests.get(f"{API_BASE}/plugins")
    plugins = response.json()
    print("Available plugins:")
    for plugin in plugins:
        print(f"  - {plugin['name']}: {plugin['description']}")

if __name__ == "__main__":
    print("WolfTrace API Examples\n")
    
    # List plugins
    list_plugins()
    print()
    
    # Import data
    print("Importing web reconnaissance data...")
    import_web_data()
    print()
    
    # Get stats
    get_graph_stats()
    print()
    
    # Find paths (adjust node IDs based on your data)
    # find_paths("192.168.1.1", "192.168.1.20")

