"""
Database Abstraction Layer for WolfTrace
Provides abstraction for different database backends (Neo4j, in-memory, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    IN_MEMORY = "in-memory"  # Default, current implementation
    NEO4J = "neo4j"
    NETWORKX = "networkx"  # NetworkX file-based


class DatabaseBackend(ABC):
    """Abstract base class for database backends"""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected"""
        pass
    
    @abstractmethod
    def add_node(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add a node to the database"""
        pass
    
    @abstractmethod
    def add_edge(self, source: str, target: str, edge_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add an edge to the database"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node from the database"""
        pass
    
    @abstractmethod
    def get_all_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes, optionally filtered by type"""
        pass
    
    @abstractmethod
    def get_all_edges(self, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all edges, optionally filtered by type"""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships"""
        pass
    
    @abstractmethod
    def delete_edge(self, source: str, target: str, edge_type: Optional[str] = None) -> bool:
        """Delete an edge"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the database"""
        pass
    
    @abstractmethod
    def get_full_graph(self) -> Dict[str, List]:
        """Get complete graph as nodes and edges lists"""
        pass
    
    @abstractmethod
    def transaction(self):
        """Return a transaction context manager"""
        pass


class InMemoryBackend(DatabaseBackend):
    """In-memory database backend using NetworkX (current implementation)"""
    
    def __init__(self, graph_engine):
        """
        Initialize in-memory backend
        
        Args:
            graph_engine: GraphEngine instance with NetworkX graph
        """
        self.graph_engine = graph_engine
        self._connected = True
    
    def connect(self) -> None:
        """In-memory backend is always connected"""
        self._connected = True
        logger.info("In-memory backend connected")
    
    def disconnect(self) -> None:
        """In-memory backend disconnect"""
        self._connected = False
        logger.info("In-memory backend disconnected")
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected
    
    def add_node(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add a node"""
        self.graph_engine.add_node(node_id, node_type, properties)
    
    def add_edge(self, source: str, target: str, edge_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add an edge"""
        self.graph_engine.add_edge(source, target, edge_type, properties)
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node"""
        if node_id in self.graph_engine.graph.nodes:
            node_data = dict(self.graph_engine.graph.nodes[node_id])
            node_data['id'] = node_id
            return node_data
        return None
    
    def get_all_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes"""
        return self.graph_engine.get_nodes(node_type)
    
    def get_all_edges(self, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all edges"""
        return self.graph_engine.get_edges(edge_type)
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node"""
        if node_id in self.graph_engine.graph.nodes:
            self.graph_engine.graph.remove_node(node_id)
            return True
        return False
    
    def delete_edge(self, source: str, target: str, edge_type: Optional[str] = None) -> bool:
        """Delete an edge"""
        try:
            if edge_type:
                if self.graph_engine.graph.has_edge(source, target, edge_type):
                    self.graph_engine.graph.remove_edge(source, target, edge_type)
                    return True
            else:
                if self.graph_engine.graph.has_edge(source, target):
                    for key in list(self.graph_engine.graph[source][target].keys()):
                        self.graph_engine.graph.remove_edge(source, target, key)
                    return True
        except (KeyError, TypeError):
            pass
        return False
    
    def clear(self) -> None:
        """Clear all data"""
        self.graph_engine.clear()
    
    def get_full_graph(self) -> Dict[str, List]:
        """Get full graph"""
        return self.graph_engine.get_full_graph()
    
    def transaction(self):
        """Return a no-op transaction context (in-memory doesn't need transactions)"""
        from contextlib import nullcontext
        return nullcontext()


class Neo4jBackend(DatabaseBackend):
    """Neo4j database backend for persistent graph storage"""
    
    def __init__(self, uri: str, username: str, password: str, *, pool_size: int = 10,
                 max_conn_lifetime: int = 3600, acquire_timeout: int = 30, max_retry_time: int = 15):
        """
        Initialize Neo4j backend
        
        Args:
            uri: Neo4j connection URI (e.g., "neo4j://localhost:7687")
            username: Neo4j username
            password: Neo4j password
            pool_size: Maximum connection pool size
            max_conn_lifetime: Max connection lifetime in seconds
            acquire_timeout: Timeout to acquire a connection from pool
            max_retry_time: Max retry time for transient errors
        """
        try:
            from neo4j import GraphDatabase, basic_auth
            self.GraphDatabase = GraphDatabase
            self.basic_auth = basic_auth
        except ImportError:
            raise ImportError("neo4j package not installed. Install with: pip install neo4j")
        
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._connected = False
        self.pool_size = pool_size
        self.max_conn_lifetime = max_conn_lifetime
        self.acquire_timeout = acquire_timeout
        self.max_retry_time = max_retry_time
    
    def connect(self) -> None:
        """Establish Neo4j connection"""
        try:
            self.driver = self.GraphDatabase.driver(
                self.uri,
                auth=self.basic_auth(self.username, self.password),
                max_connection_pool_size=self.pool_size,
                max_connection_lifetime=self.max_conn_lifetime,
                connection_acquisition_timeout=self.acquire_timeout,
                max_transaction_retry_time=self.max_retry_time
            )
            # Test connection
            self.ping()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Disconnected from Neo4j")
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j"""
        return self._connected

    def ping(self) -> bool:
        """Health check for Neo4j connection"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.warning(f"Neo4j ping failed: {str(e)}")
            return False

    def _ensure_connection(self) -> None:
        if not self._connected or not self.ping():
            logger.info("Reconnecting to Neo4j...")
            self.connect()

    def _run_with_reconnect(self, fn):
        try:
            return fn()
        except Exception as e:
            logger.warning(f"Neo4j operation failed, retrying once: {str(e)}")
            self._ensure_connection()
            return fn()
    
    def add_node(self, node_id: str, node_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add a node to Neo4j"""
        self._ensure_connection()
        properties = properties or {}
        properties['id'] = node_id
        node_type = node_type or 'Entity'

        def _op():
            with self.driver.session() as session:
                query = f"""
                MERGE (n:{node_type} {{id: $id}})
                SET n += $props
                """
                session.run(query, id=node_id, props=properties)
        self._run_with_reconnect(_op)
    
    def add_edge(self, source: str, target: str, edge_type: str = None, properties: Dict[str, Any] = None) -> None:
        """Add an edge to Neo4j"""
        self._ensure_connection()
        properties = properties or {}
        edge_type = edge_type or 'RELATED_TO'

        def _op():
            with self.driver.session() as session:
                query = f"""
                MATCH (a {{id: $source}})
                MATCH (b {{id: $target}})
                MERGE (a)-[r:{edge_type}]->(b)
                SET r += $props
                """
                session.run(query, source=source, target=target, props=properties)
        self._run_with_reconnect(_op)
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                result = session.run("MATCH (n {id: $id}) RETURN n", id=node_id)
                record = result.single()
                return dict(record['n']) if record else None
        return self._run_with_reconnect(_op)
    
    def get_all_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                if node_type:
                    query = f"MATCH (n:{node_type}) RETURN n"
                    result = session.run(query)
                else:
                    query = "MATCH (n) RETURN n"
                    result = session.run(query)
                return [dict(record['n']) for record in result]
        return self._run_with_reconnect(_op)
    
    def get_all_edges(self, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all edges from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                if edge_type:
                    query = f"MATCH (a)-[r:{edge_type}]->(b) RETURN a.id as source, b.id as target, type(r) as type, r"
                    result = session.run(query)
                else:
                    query = "MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, type(r) as type, r"
                    result = session.run(query)
                edges = []
                for record in result:
                    edge = dict(record['r'])
                    edge['source'] = record['source']
                    edge['target'] = record['target']
                    edge['type'] = record['type']
                    edges.append(edge)
                return edges
        return self._run_with_reconnect(_op)
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                result = session.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
                return result.summary.counters.nodes_deleted > 0
        return self._run_with_reconnect(_op)
    
    def delete_edge(self, source: str, target: str, edge_type: Optional[str] = None) -> bool:
        """Delete an edge from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                if edge_type:
                    query = f"MATCH (a {{id: $source}})-[r:{edge_type}]->(b {{id: $target}}) DELETE r"
                else:
                    query = "MATCH (a {id: $source})-[r]->(b {id: $target}) DELETE r"
                result = session.run(query, source=source, target=target)
                return result.summary.counters.relationships_deleted > 0
        return self._run_with_reconnect(_op)
    
    def clear(self) -> None:
        """Clear all data from Neo4j"""
        self._ensure_connection()
        def _op():
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.warning("Cleared all data from Neo4j")
        self._run_with_reconnect(_op)
    
    def get_full_graph(self) -> Dict[str, List]:
        """Get full graph from Neo4j"""
        return {
            'nodes': self.get_all_nodes(),
            'edges': self.get_all_edges()
        }
    
    def transaction(self):
        """Return a transaction context for Neo4j"""
        return self.driver.session()


class DatabaseFactory:
    """Factory for creating database backends"""
    
    @staticmethod
    def create_backend(backend_type: DatabaseType, **kwargs) -> DatabaseBackend:
        """
        Create a database backend
        
        Args:
            backend_type: Type of backend to create
            **kwargs: Backend-specific arguments
        
        Returns:
            DatabaseBackend instance
        """
        if backend_type == DatabaseType.IN_MEMORY:
            graph_engine = kwargs.get('graph_engine')
            if not graph_engine:
                raise ValueError("graph_engine required for in-memory backend")
            return InMemoryBackend(graph_engine)
        
        elif backend_type == DatabaseType.NEO4J:
            uri = kwargs.get('uri', 'neo4j://localhost:7687')
            username = kwargs.get('username', 'neo4j')
            password = kwargs.get('password')
            if not password:
                raise ValueError("password required for Neo4j backend")
            return Neo4jBackend(
                uri,
                username,
                password,
                pool_size=kwargs.get('pool_size', 10),
                max_conn_lifetime=kwargs.get('max_conn_lifetime', 3600),
                acquire_timeout=kwargs.get('acquire_timeout', 30),
                max_retry_time=kwargs.get('max_retry_time', 15)
            )
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
