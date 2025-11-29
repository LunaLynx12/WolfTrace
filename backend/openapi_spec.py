"""
OpenAPI 3.0 Specification for WolfTrace API
Comprehensive API documentation
"""

def generate_openapi_spec(base_url: str = "http://localhost:5000") -> dict:
    """Generate complete OpenAPI 3.0 specification"""
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "WolfTrace API",
            "version": "1.0.0",
            "description": "WolfTrace - Modular Graph Visualization API for cybersecurity analysis",
            "contact": {
                "name": "WolfTrace",
                "url": "https://github.com/LunaLynx12/WolfTrace"
            }
        },
        "servers": [
            {
                "url": base_url,
                "description": "Development server"
            }
        ],
        "tags": [
            {"name": "Health", "description": "Health check endpoints"},
            {"name": "Graph", "description": "Graph data operations"},
            {"name": "Import", "description": "Data import operations"},
            {"name": "Plugins", "description": "Plugin management"},
            {"name": "Analytics", "description": "Graph analytics and statistics"},
            {"name": "Sessions", "description": "Session management"},
            {"name": "Query", "description": "Advanced querying"},
            {"name": "Comparison", "description": "Graph comparison"},
            {"name": "Reports", "description": "Report generation"},
            {"name": "Bulk Operations", "description": "Bulk node/edge operations"},
            {"name": "Templates", "description": "Graph templates"},
            {"name": "History", "description": "Undo/Redo operations"}
        ],
        "paths": {
            "/api": {
                "get": {
                    "tags": ["Health"],
                    "summary": "API Root",
                    "description": "List all available API endpoints",
                    "responses": {
                        "200": {
                            "description": "List of endpoints",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "version": {"type": "string"},
                                            "endpoints": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health Check",
                    "description": "Check API health status",
                    "responses": {
                        "200": {
                            "description": "API is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/graph": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Get Full Graph",
                    "description": "Get complete graph data (nodes and edges)",
                    "responses": {
                        "200": {
                            "description": "Graph data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Node"}
                                            },
                                            "edges": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Edge"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/graph/paginated": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Get Paginated Graph",
                    "description": "Get graph data with pagination",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 1},
                            "description": "Page number"
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 100},
                            "description": "Items per page"
                        },
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Filter by node type"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated graph data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes": {"type": "array"},
                                            "edges": {"type": "array"},
                                            "pagination": {"$ref": "#/components/schemas/Pagination"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/nodes": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Get Nodes",
                    "description": "Get all nodes, optionally filtered by type",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Filter by node type"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of nodes",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Node"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/edges": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Get Edges",
                    "description": "Get all edges, optionally filtered by type",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Filter by edge type"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of edges",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Edge"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/paths": {
                "post": {
                    "tags": ["Graph"],
                    "summary": "Find Paths",
                    "description": "Find all paths between two nodes",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["source", "target"],
                                    "properties": {
                                        "source": {"type": "string", "description": "Source node ID"},
                                        "target": {"type": "string", "description": "Target node ID"},
                                        "max_depth": {"type": "integer", "default": 5, "description": "Maximum path depth"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "List of paths",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/search": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Search Nodes",
                    "description": "Search for nodes by ID or properties",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Search query"
                        },
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Filter by node type"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50},
                            "description": "Maximum results"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Node"}
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/clear": {
                "post": {
                    "tags": ["Graph"],
                    "summary": "Clear Graph",
                    "description": "Clear all nodes and edges from the graph",
                    "responses": {
                        "200": {
                            "description": "Graph cleared",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "cleared"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/export": {
                "get": {
                    "tags": ["Graph"],
                    "summary": "Export Graph",
                    "description": "Export graph data as JSON",
                    "parameters": [
                        {
                            "name": "format",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["json"], "default": "json"},
                            "description": "Export format"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Exported graph data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes": {"type": "array"},
                                            "edges": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/plugins": {
                "get": {
                    "tags": ["Plugins"],
                    "summary": "List Plugins",
                    "description": "Get list of all available plugins",
                    "responses": {
                        "200": {
                            "description": "List of plugins",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Plugin"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/import": {
                "post": {
                    "tags": ["Import"],
                    "summary": "Import Data",
                    "description": "Import data using a specific plugin",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["collector", "data"],
                                    "properties": {
                                        "collector": {
                                            "type": "string",
                                            "description": "Plugin/collector name"
                                        },
                                        "data": {
                                            "type": "object",
                                            "description": "Data to import"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Import successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ImportResult"}
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/import-autodetect": {
                "post": {
                    "tags": ["Import"],
                    "summary": "Import Data (Auto-detect)",
                    "description": "Import data with automatic plugin detection",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["data"],
                                    "properties": {
                                        "data": {
                                            "type": "object",
                                            "description": "Data to import (plugin will be auto-detected)"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Import successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {"$ref": "#/components/schemas/ImportResult"},
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "detected_plugin": {"type": "string"}
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/import-zip": {
                "post": {
                    "tags": ["Import"],
                    "summary": "Import ZIP Archive",
                    "description": "Import a ZIP archive containing JSON files",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["collector", "file"],
                                    "properties": {
                                        "collector": {
                                            "type": "string",
                                            "description": "Plugin/collector name"
                                        },
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "ZIP file containing JSON data"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Import successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ImportResult"}
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/import-zip-autodetect": {
                "post": {
                    "tags": ["Import"],
                    "summary": "Import ZIP Archive (Auto-detect)",
                    "description": "Import ZIP archive with automatic plugin detection",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "ZIP file containing JSON data"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Import successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {"$ref": "#/components/schemas/ImportResult"},
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "detected_plugin": {"type": "string"}
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/analytics/stats": {
                "get": {
                    "tags": ["Analytics"],
                    "summary": "Get Statistics",
                    "description": "Get comprehensive graph statistics and metrics",
                    "responses": {
                        "200": {
                            "description": "Graph statistics",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Statistics"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/analytics/communities": {
                "get": {
                    "tags": ["Analytics"],
                    "summary": "Find Communities",
                    "description": "Find communities in the graph using Louvain algorithm",
                    "parameters": [
                        {
                            "name": "max",
                            "in": "query",
                            "schema": {"type": "integer", "default": 10},
                            "description": "Maximum number of communities"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of communities",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "size": {"type": "integer"},
                                                "nodes": {"type": "array", "items": {"type": "string"}}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/analytics/neighbors": {
                "get": {
                    "tags": ["Analytics"],
                    "summary": "Get Node Neighbors",
                    "description": "Get neighbors of a node up to specified depth",
                    "parameters": [
                        {
                            "name": "node",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Node ID"
                        },
                        {
                            "name": "depth",
                            "in": "query",
                            "schema": {"type": "integer", "default": 1},
                            "description": "Neighbor depth"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Node neighbors",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "node": {"type": "string"},
                                            "depth_1": {"type": "array", "items": {"type": "string"}},
                                            "depth_2": {"type": "array", "items": {"type": "string"}},
                                            "total_neighbors": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/sessions": {
                "get": {
                    "tags": ["Sessions"],
                    "summary": "List Sessions",
                    "description": "List all saved sessions",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50},
                            "description": "Maximum number of sessions"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of sessions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Session"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Save Session",
                    "description": "Save current graph as a session",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "default": "Untitled Session"},
                                        "metadata": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Session saved",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Session"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/sessions/{session_id}": {
                "get": {
                    "tags": ["Sessions"],
                    "summary": "Get Session",
                    "description": "Load a saved session",
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Session ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Session data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Session"}
                                }
                            }
                        },
                        "404": {"$ref": "#/components/responses/NotFound"}
                    }
                },
                "delete": {
                    "tags": ["Sessions"],
                    "summary": "Delete Session",
                    "description": "Delete a saved session",
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Session ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Session deleted",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "deleted"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"$ref": "#/components/responses/NotFound"}
                    }
                }
            },
            "/api/sessions/{session_id}/restore": {
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Restore Session",
                    "description": "Restore a session to the current graph",
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Session ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Session restored",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "restored"},
                                            "session": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"$ref": "#/components/responses/NotFound"}
                    }
                }
            },
            "/api/query": {
                "post": {
                    "tags": ["Query"],
                    "summary": "Query Graph",
                    "description": "Advanced query with filters",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueryFilters"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Query results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes": {"type": "array"},
                                            "edges": {"type": "array"},
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/query/stats": {
                "post": {
                    "tags": ["Query"],
                    "summary": "Query Statistics",
                    "description": "Get statistics for a filtered query",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueryFilters"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Query statistics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "node_count": {"type": "integer"},
                                            "edge_count": {"type": "integer"},
                                            "node_types": {"type": "object"},
                                            "edge_types": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/compare": {
                "post": {
                    "tags": ["Comparison"],
                    "summary": "Compare Graphs",
                    "description": "Compare two graphs and find differences",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["graph1", "graph2"],
                                    "properties": {
                                        "graph1": {
                                            "type": "object",
                                            "properties": {
                                                "nodes": {"type": "array"},
                                                "edges": {"type": "array"}
                                            }
                                        },
                                        "graph2": {
                                            "type": "object",
                                            "properties": {
                                                "nodes": {"type": "array"},
                                                "edges": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Comparison results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "stats": {"type": "object"},
                                            "nodes": {"type": "object"},
                                            "edges": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/compare/diff-graph": {
                "post": {
                    "tags": ["Comparison"],
                    "summary": "Get Diff Graph",
                    "description": "Get visualization graph showing differences",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["graph1", "graph2"],
                                    "properties": {
                                        "graph1": {"type": "object"},
                                        "graph2": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Diff graph",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes": {"type": "array"},
                                            "edges": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/report": {
                "get": {
                    "tags": ["Reports"],
                    "summary": "Generate Report",
                    "description": "Generate report data in JSON or HTML format",
                    "parameters": [
                        {
                            "name": "include_graph",
                            "in": "query",
                            "schema": {"type": "boolean", "default": False},
                            "description": "Include full graph data"
                        },
                        {
                            "name": "format",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["json", "html"], "default": "json"},
                            "description": "Report format"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Report data",
                            "content": {
                                "application/json": {"schema": {"type": "object"}},
                                "text/html": {"schema": {"type": "string"}}
                            }
                        }
                    }
                }
            },
            "/api/bulk/nodes/delete": {
                "post": {
                    "tags": ["Bulk Operations"],
                    "summary": "Bulk Delete Nodes",
                    "description": "Delete multiple nodes and their associated edges",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["node_ids"],
                                    "properties": {
                                        "node_ids": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Deletion result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes_deleted": {"type": "integer"},
                                            "edges_removed": {"type": "integer"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/bulk/edges/delete": {
                "post": {
                    "tags": ["Bulk Operations"],
                    "summary": "Bulk Delete Edges",
                    "description": "Delete multiple edges",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["edges"],
                                    "properties": {
                                        "edges": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "source": {"type": "string"},
                                                    "target": {"type": "string"},
                                                    "type": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Deletion result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "edges_deleted": {"type": "integer"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/bulk/nodes/update": {
                "post": {
                    "tags": ["Bulk Operations"],
                    "summary": "Bulk Update Nodes",
                    "description": "Update properties of multiple nodes",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["updates"],
                                    "properties": {
                                        "updates": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "properties": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Update result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes_updated": {"type": "integer"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/bulk/nodes/tag": {
                "post": {
                    "tags": ["Bulk Operations"],
                    "summary": "Bulk Tag Nodes",
                    "description": "Add or remove tags from multiple nodes",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["node_ids", "tags"],
                                    "properties": {
                                        "node_ids": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "tags": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "operation": {
                                            "type": "string",
                                            "enum": ["add", "remove"],
                                            "default": "add"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tagging result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nodes_tagged": {"type": "integer"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/bulk/nodes/export": {
                "post": {
                    "tags": ["Bulk Operations"],
                    "summary": "Bulk Export Nodes",
                    "description": "Export data for multiple nodes",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["node_ids"],
                                    "properties": {
                                        "node_ids": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Exported nodes",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Node"}
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/templates": {
                "get": {
                    "tags": ["Templates"],
                    "summary": "List Templates",
                    "description": "List all available graph templates",
                    "responses": {
                        "200": {
                            "description": "List of templates",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Template"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Templates"],
                    "summary": "Save Template",
                    "description": "Save a new graph template",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Template"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Template saved",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "template_id": {"type": "string"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/templates/{template_id}": {
                "get": {
                    "tags": ["Templates"],
                    "summary": "Get Template",
                    "description": "Get a specific template",
                    "parameters": [
                        {
                            "name": "template_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Template ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Template data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Template"}
                                }
                            }
                        },
                        "404": {"$ref": "#/components/responses/NotFound"}
                    }
                }
            },
            "/api/templates/{template_id}/apply": {
                "post": {
                    "tags": ["Templates"],
                    "summary": "Apply Template",
                    "description": "Apply a template to the graph",
                    "parameters": [
                        {
                            "name": "template_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Template ID"
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "variables": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Template applied",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "template_id": {"type": "string"},
                                            "nodes_added": {"type": "integer"},
                                            "edges_added": {"type": "integer"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/history/undo": {
                "post": {
                    "tags": ["History"],
                    "summary": "Undo",
                    "description": "Undo last operation",
                    "responses": {
                        "200": {
                            "description": "Operation undone",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "graph": {"type": "object"},
                                            "history_info": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/history/redo": {
                "post": {
                    "tags": ["History"],
                    "summary": "Redo",
                    "description": "Redo last undone operation",
                    "responses": {
                        "200": {
                            "description": "Operation redone",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "graph": {"type": "object"},
                                            "history_info": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"}
                    }
                }
            },
            "/api/history/info": {
                "get": {
                    "tags": ["History"],
                    "summary": "Get History Info",
                    "description": "Get history information",
                    "responses": {
                        "200": {
                            "description": "History information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "undo_count": {"type": "integer"},
                                            "redo_count": {"type": "integer"},
                                            "can_undo": {"type": "boolean"},
                                            "can_redo": {"type": "boolean"},
                                            "current_operation": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/history/clear": {
                "post": {
                    "tags": ["History"],
                    "summary": "Clear History",
                    "description": "Clear all history",
                    "responses": {
                        "200": {
                            "description": "History cleared",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "cleared"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string"},
                        "properties": {"type": "object"}
                    },
                    "required": ["id"]
                },
                "Edge": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "type": {"type": "string"},
                        "properties": {"type": "object"}
                    },
                    "required": ["source", "target"]
                },
                "Plugin": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"},
                        "supported_formats": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "ImportResult": {
                    "type": "object",
                    "properties": {
                        "plugin": {"type": "string"},
                        "status": {"type": "string"},
                        "nodes_added": {"type": "integer"},
                        "edges_added": {"type": "integer"}
                    }
                },
                "Statistics": {
                    "type": "object",
                    "properties": {
                        "basic": {
                            "type": "object",
                            "properties": {
                                "nodes": {"type": "integer"},
                                "edges": {"type": "integer"},
                                "average_degree": {"type": "number"},
                                "connected_components": {"type": "integer"},
                                "largest_component_size": {"type": "integer"}
                            }
                        },
                        "node_types": {"type": "object"},
                        "edge_types": {"type": "object"},
                        "top_nodes_by_degree": {"type": "array"},
                        "top_nodes_by_betweenness": {"type": "array"},
                        "is_connected": {"type": "boolean"},
                        "is_dag": {"type": "boolean"}
                    }
                },
                "Session": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "created_at": {"type": "string"},
                        "metadata": {"type": "object"},
                        "graph": {
                            "type": "object",
                            "properties": {
                                "nodes": {"type": "array"},
                                "edges": {"type": "array"}
                            }
                        }
                    }
                },
                "QueryFilters": {
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "properties": {"type": "object"},
                        "edge_type": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "text_search": {"type": "string"},
                        "min_degree": {"type": "integer"},
                        "max_degree": {"type": "integer"},
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "start": {"type": "string"},
                                "end": {"type": "string"}
                            }
                        }
                    }
                },
                "Template": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "category": {"type": "string"},
                        "nodes": {"type": "array"},
                        "edges": {"type": "array"}
                    }
                },
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "per_page": {"type": "integer"},
                        "total": {"type": "integer"},
                        "total_pages": {"type": "integer"}
                    }
                }
            },
            "responses": {
                "BadRequest": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }

