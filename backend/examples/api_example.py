"""
Example: Using WolfTrace API programmatically
"""
import requests
import json

API_BASE = "http://localhost:5000/api"

# Example 1: Import network data
def import_network_data():
    # Example data is now in backend/data/examples
    import os
    from pathlib import Path
    examples_dir = Path(__file__).resolve().parent
    data_file = examples_dir.parent / 'data' / 'examples' / 'example_network.json'
    with open(data_file, 'r') as f:
        network_data = json.load(f)
    
    response = requests.post(
        f"{API_BASE}/import",
        json={
            "collector": "network",
            "data": network_data
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
    print("Importing network data...")
    import_network_data()
    print()
    
    # Get stats
    get_graph_stats()
    print()
    
    # Find paths (adjust node IDs based on your data)
    # find_paths("192.168.1.1", "192.168.1.20")

