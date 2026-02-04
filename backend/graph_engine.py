"""
Graph Engine - Handles graph operations and storage
Uses in-memory NetworkX graph storage with optional database persistence
"""
import logging
import networkx as nx
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple
import json
import time
import base64
from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:  # Avoid runtime import cycles
    from database import DatabaseBackend

logger = logging.getLogger(__name__)


class GraphEngine:
    def __init__(self, database_backend: Optional["DatabaseBackend"] = None, auto_sync: bool = True, cache_ttl: int = 10):
        """
        Initialize graph engine with in-memory NetworkX graph
        
        Args:
            database_backend: Optional persistence backend (e.g., Neo4j)
            auto_sync: If True, load persisted data on startup when backend is connected
            cache_ttl: Cache time-to-live in seconds for frequent queries
        """
        self.graph = nx.MultiDiGraph()  # Directed multigraph for relationships
        self.db_backend = database_backend
        self.cache_ttl = cache_ttl

        # Simple indices for fast lookups
        self.node_index_by_type: Dict[str, set] = {}
        self.edge_index_by_type: Dict[str, set] = {}

        # Lightweight caches for frequent queries
        self._cache = {
            'nodes': {},  # key -> (timestamp, data)
            'edges': {},
            'paths': {}
        }

        # Thread pool for heavy tasks (paths, analytics)
        self._executor = ThreadPoolExecutor(max_workers=4)

        if self._should_persist() and auto_sync:
            self.sync_from_backend()

    def set_backend(self, database_backend: Optional["DatabaseBackend"]) -> None:
        """Attach or replace the persistence backend"""
        self.db_backend = database_backend
        if self._should_persist():
            self.sync_from_backend()

    # Cache helpers
    def _cache_get(self, category: str, key: Any):
        entry = self._cache.get(category, {}).get(key)
        if not entry:
            return None
        timestamp, value = entry
        if (time.time() - timestamp) > self.cache_ttl:
            # Expired
            self._cache[category].pop(key, None)
            return None
        return value

    def _cache_set(self, category: str, key: Any, value: Any) -> None:
        self._cache.setdefault(category, {})[key] = (time.time(), value)

    def _invalidate_cache(self, categories: Optional[List[str]] = None) -> None:
        targets = categories or list(self._cache.keys())
        for cat in targets:
            self._cache.get(cat, {}).clear()

    def _should_persist(self) -> bool:
        """Check whether persistence backend is available and connected"""
        backend = getattr(self, "db_backend", None)
        if not backend:
            return False
        try:
            return hasattr(backend, "is_connected") and backend.is_connected() and backend.__class__.__name__ != "InMemoryBackend"
        except Exception:
            return False

    def _add_node_local(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add node to the in-memory graph only"""
        # Handle case where node_type is passed as a dict (backward compatibility)
        if isinstance(node_type, dict):
            properties = node_type
            node_type = properties.get('type', None)
        elif properties is None:
            properties = {}
        
        properties['id'] = node_id
        if node_type:
            properties['type'] = node_type
        
        # Check if node already exists and merge properties
        if self.graph.has_node(node_id):
            existing_data = self.graph.nodes[node_id]
            merged_properties = dict(existing_data)
            for key, value in properties.items():
                if key in merged_properties:
                    if isinstance(merged_properties[key], list) and isinstance(value, list):
                        merged_properties[key] = merged_properties[key] + value
                    elif isinstance(merged_properties[key], dict) and isinstance(value, dict):
                        merged_properties[key] = {**merged_properties[key], **value}
                    else:
                        merged_properties[key] = value
                else:
                    merged_properties[key] = value
            self.graph.add_node(node_id, **merged_properties)
        else:
            self.graph.add_node(node_id, **properties)
        # Update node index
        ntype = properties.get('type') or node_type or 'Entity'
        self.node_index_by_type.setdefault(ntype, set()).add(node_id)
        self._invalidate_cache(['nodes', 'paths'])

    def _persist_node(self, node_id: str, node_type: Optional[str], properties: Dict[str, Any]) -> None:
        """Persist node to backend when enabled"""
        if not self._should_persist():
            return
        try:
            self.db_backend.add_node(node_id, node_type, properties)
        except Exception as e:
            logger.warning(f"Failed to persist node {node_id}: {str(e)}")
    
    def add_node(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None):
        """Add a node to the graph and persist if enabled"""
        if properties is None:
            properties = {}
        self._add_node_local(node_id, node_type, properties)
        self._persist_node(node_id, node_type, properties)
    
    def add_edge(self, source: str, target: str, edge_type: str = None, properties: Dict[str, Any] = None):
        """Add an edge to the graph and persist if enabled"""
        if properties is None:
            properties = {}
        
        # Handle case where edge_type is passed as a dict (backward compatibility)
        if isinstance(edge_type, dict):
            properties = edge_type
            edge_type = properties.get('type', 'RELATED_TO')
        elif edge_type is None:
            edge_type = properties.get('type', 'RELATED_TO')
        
        properties['type'] = edge_type
        
        # For NetworkX MultiDiGraph, use edge_type as key for multi-edges
        self.graph.add_edge(source, target, key=edge_type, **properties)
        self._persist_edge(source, target, edge_type, properties)
        self.edge_index_by_type.setdefault(edge_type, set()).add((source, target, edge_type))
        self._invalidate_cache(['edges', 'paths'])
    
    def get_nodes(self, node_type: Optional[str] = None) -> List[Dict]:
        """Get all nodes, optionally filtered by type, with caching and indexing"""
        cache_key = node_type or '__all__'
        cached = self._cache_get('nodes', cache_key)
        if cached is not None:
            return cached
        nodes = []
        if node_type:
            node_ids = self.node_index_by_type.get(node_type, set())
            for node_id in node_ids:
                data = dict(self.graph.nodes[node_id])
                nodes.append({'id': node_id, **data})
        else:
            for node_id, data in self.graph.nodes(data=True):
                nodes.append({'id': node_id, **data})
        self._cache_set('nodes', cache_key, nodes)
        return nodes
    
    def get_edges(self, edge_type: Optional[str] = None) -> List[Dict]:
        """Get all edges, optionally filtered by type, with caching and indexing"""
        cache_key = edge_type or '__all__'
        cached = self._cache_get('edges', cache_key)
        if cached is not None:
            return cached
        edges = []
        if edge_type:
            tuples = self.edge_index_by_type.get(edge_type, set())
            for source, target, _ in tuples:
                data = dict(self.graph.get_edge_data(source, target, edge_type) or {})
                edges.append({'source': source, 'target': target, 'type': edge_type, **data})
        else:
            for source, target, key, data in self.graph.edges(keys=True, data=True):
                edges.append({'source': source, 'target': target, 'type': key, **data})
        self._cache_set('edges', cache_key, edges)
        return edges

    # Pagination utilities -------------------------------------------------
    def _decode_cursor(self, cursor: Optional[str]) -> int:
        if not cursor:
            return 0
        try:
            return int(base64.b64decode(cursor).decode('utf-8'))
        except Exception:
            return 0

    def _encode_cursor(self, offset: int) -> str:
        return base64.b64encode(str(offset).encode('utf-8')).decode('utf-8')

    def get_nodes_paginated(self, node_type: Optional[str] = None, limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Lazy-load nodes with cursor pagination"""
        offset = self._decode_cursor(cursor)
        # Use index for ordering
        if node_type:
            ids = sorted(list(self.node_index_by_type.get(node_type, [])))
        else:
            ids = sorted([nid for nid in self.graph.nodes])
        total = len(ids)
        slice_ids = ids[offset:offset + limit]
        items = []
        for node_id in slice_ids:
            data = dict(self.graph.nodes[node_id])
            items.append({'id': node_id, **data})
        next_cursor = None
        if offset + limit < total:
            next_cursor = self._encode_cursor(offset + limit)
        return {
            'items': items,
            'next_cursor': next_cursor,
            'total': total,
            'limit': limit
        }

    def get_edges_paginated(self, edge_type: Optional[str] = None, limit: int = 200, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Lazy-load edges with cursor pagination"""
        offset = self._decode_cursor(cursor)
        if edge_type:
            tuples = sorted(list(self.edge_index_by_type.get(edge_type, [])))
        else:
            tuples = sorted([(s, t, k) for s, t, k in self.graph.edges(keys=True)])
        total = len(tuples)
        slice_edges = tuples[offset:offset + limit]
        items = []
        for source, target, key in slice_edges:
            data = dict(self.graph.get_edge_data(source, target, key) or {})
            items.append({'source': source, 'target': target, 'type': key, **data})
        next_cursor = None
        if offset + limit < total:
            next_cursor = self._encode_cursor(offset + limit)
        return {
            'items': items,
            'next_cursor': next_cursor,
            'total': total,
            'limit': limit
        }
    
    def get_full_graph(self) -> Dict:
        """Get complete graph data with cached slices"""
        return {
            'nodes': self.get_nodes(),
            'edges': self.get_edges()
        }

    def remove_node(self, node_id: str) -> Dict[str, Any]:
        """Remove node locally and in persistence backend"""
        edges_removed = 0
        if self.graph.has_node(node_id):
            edges_removed = self.graph.out_degree(node_id) + self.graph.in_degree(node_id)
            # Update node index
            node_type = self.graph.nodes[node_id].get('type', 'Entity')
            if node_type in self.node_index_by_type:
                self.node_index_by_type[node_type].discard(node_id)
            self.graph.remove_node(node_id)
            # Purge edges from edge index
            for etype, edge_set in self.edge_index_by_type.items():
                self.edge_index_by_type[etype] = {e for e in edge_set if node_id not in (e[0], e[1])}
            if self._should_persist():
                try:
                    self.db_backend.delete_node(node_id)
                except Exception as e:
                    logger.warning(f"Failed to delete node {node_id} from backend: {str(e)}")
            self._invalidate_cache(['nodes', 'edges', 'paths'])
            return {'deleted': True, 'edges_removed': edges_removed}
        return {'deleted': False, 'edges_removed': 0}

    def remove_edge(self, source: str, target: str, edge_type: Optional[str] = None) -> bool:
        """Remove edge locally and in persistence backend"""
        removed = False
        try:
            if edge_type:
                if self.graph.has_edge(source, target, edge_type):
                    self.graph.remove_edge(source, target, edge_type)
                    removed = True
            else:
                if self.graph.has_edge(source, target):
                    for key in list(self.graph[source][target].keys()):
                        self.graph.remove_edge(source, target, key)
                        removed = True
        except (KeyError, TypeError):
            removed = False
        
        if removed and self._should_persist():
            try:
                self.db_backend.delete_edge(source, target, edge_type)
            except Exception as e:
                logger.warning(f"Failed to delete edge {source}->{target} from backend: {str(e)}")
        if removed:
            if edge_type:
                self.edge_index_by_type.get(edge_type, set()).discard((source, target, edge_type))
            else:
                # remove any edge types between nodes
                for etype, edge_set in self.edge_index_by_type.items():
                    self.edge_index_by_type[etype] = {e for e in edge_set if not (e[0] == source and e[1] == target)}
            self._invalidate_cache(['edges', 'paths'])
        return removed

    def sync_from_backend(self) -> Dict[str, int]:
        """Pull graph data from backend into the in-memory graph"""
        if not self._should_persist():
            return {'nodes': 0, 'edges': 0}
        try:
            data = self.db_backend.get_full_graph()
            self.graph.clear()
            self.node_index_by_type.clear()
            self.edge_index_by_type.clear()
            node_data = data.get('nodes', [])
            edge_data = data.get('edges', [])
            
            # Nodes can be list or dict
            if isinstance(node_data, dict):
                for node_id, props in node_data.items():
                    props = props or {}
                    self.graph.add_node(node_id, **props)
                    ntype = props.get('type', 'Entity')
                    self.node_index_by_type.setdefault(ntype, set()).add(node_id)
            else:
                for node in node_data:
                    node_id = node.get('id') or node.get('Id')
                    props = {k: v for k, v in node.items() if k not in ('id', 'Id')}
                    self.graph.add_node(node_id, **props)
                    ntype = props.get('type', 'Entity')
                    self.node_index_by_type.setdefault(ntype, set()).add(node_id)
            
            for edge in edge_data:
                source = edge.get('source')
                target = edge.get('target')
                edge_type = edge.get('type', 'RELATED_TO')
                props = {k: v for k, v in edge.items() if k not in ('source', 'target', 'type')}
                self.graph.add_edge(source, target, key=edge_type, **props)
                self.edge_index_by_type.setdefault(edge_type, set()).add((source, target, edge_type))
            
            self._invalidate_cache()
            return {'nodes': len(self.graph.nodes), 'edges': len(self.graph.edges)}
        except Exception as e:
            logger.error(f"Failed to sync from backend: {str(e)}")
            return {'nodes': 0, 'edges': 0}
    
    def find_paths(self, source: str, target: str, max_depth: int = 5, max_paths: int = 100) -> List[List[str]]:
        """Find paths using bounded BFS with optional caching"""
        cache_key = (source, target, max_depth, max_paths)
        cached = self._cache_get('paths', cache_key)
        if cached is not None:
            return cached

        if max_depth <= 0:
            return []

        paths: List[List[str]] = []
        queue: List[Tuple[List[str], int]] = [([source], 0)]
        visited_at_depth = {source: 0}

        while queue and len(paths) < max_paths:
            current_path, depth = queue.pop(0)
            last_node = current_path[-1]
            if depth >= max_depth:
                continue
            # Explore neighbors
            for _, neighbor, _ in self.graph.out_edges(last_node, keys=True):
                new_depth = depth + 1
                if neighbor in current_path:
                    continue  # avoid cycles
                new_path = current_path + [neighbor]
                if neighbor == target:
                    paths.append(new_path)
                    if len(paths) >= max_paths:
                        break
                else:
                    prev_depth = visited_at_depth.get(neighbor)
                    if prev_depth is None or new_depth < prev_depth:
                        visited_at_depth[neighbor] = new_depth
                        queue.append((new_path, new_depth))
        self._cache_set('paths', cache_key, paths)
        return paths

    # Background tasks -----------------------------------------------------
    def submit_background(self, func, *args, **kwargs):
        """Run heavy graph tasks in background thread pool"""
        return self._executor.submit(func, *args, **kwargs)
    
    def clear(self):
        """Clear all graph data (and backend if enabled)"""
        self.graph.clear()
        self.node_index_by_type.clear()
        self.edge_index_by_type.clear()
        self._invalidate_cache()
        if self._should_persist():
            try:
                self.db_backend.clear()
            except Exception as e:
                logger.warning(f"Failed to clear backend: {str(e)}")

    def _persist_edge(self, source: str, target: str, edge_type: str, properties: Dict[str, Any]) -> None:
        """Persist edge to backend when enabled"""
        if not self._should_persist():
            return
        try:
            self.db_backend.add_edge(source, target, edge_type, properties)
        except Exception as e:
            logger.warning(f"Failed to persist edge {source}->{target}: {str(e)}")

