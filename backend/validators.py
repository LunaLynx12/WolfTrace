"""
Validation Utilities for WolfTrace Backend
Provides input validation, sanitization, and schema validation
"""
import re
from typing import Any, Dict, List, Optional
from jsonschema import validate as json_validate, ValidationError as JsonSchemaValidationError
from exceptions import (
    ValidationError,
    InvalidNodeIdError,
    InvalidEdgeIdError,
    SchemaValidationError,
    RequestTooLargeError
)


# Validation constants
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50 MB default
MAX_NODE_ID_LENGTH = 500
MAX_EDGE_TYPE_LENGTH = 100
INVALID_NODE_ID_CHARS = ['<', '>', '|', '\0', '\n', '\r', '\t']
INVALID_NODE_ID_PATTERN = re.compile(r'[<>|\x00\n\r\t]')


def validate_node_id(node_id: str) -> None:
    """
    Validate node ID for invalid characters and length
    
    Args:
        node_id: Node identifier to validate
        
    Raises:
        ValidationError: If node_id is invalid
    """
    if not node_id:
        raise ValidationError("Node ID cannot be empty", field="node_id")
    
    if not isinstance(node_id, str):
        raise ValidationError(
            f"Node ID must be a string, got {type(node_id).__name__}",
            field="node_id"
        )
    
    if len(node_id) > MAX_NODE_ID_LENGTH:
        raise ValidationError(
            f"Node ID exceeds maximum length of {MAX_NODE_ID_LENGTH} characters",
            field="node_id",
            details={"length": len(node_id), "max_length": MAX_NODE_ID_LENGTH}
        )
    
    # Check for invalid characters
    invalid_chars = []
    for char in INVALID_NODE_ID_CHARS:
        if char in node_id:
            invalid_chars.append(repr(char))
    
    if invalid_chars:
        raise InvalidNodeIdError(node_id, invalid_chars)


def validate_edge_type(edge_type: str) -> None:
    """
    Validate edge type
    
    Args:
        edge_type: Edge type to validate
        
    Raises:
        ValidationError: If edge_type is invalid
    """
    if not edge_type:
        raise ValidationError("Edge type cannot be empty", field="edge_type")
    
    if not isinstance(edge_type, str):
        raise ValidationError(
            f"Edge type must be a string, got {type(edge_type).__name__}",
            field="edge_type"
        )
    
    if len(edge_type) > MAX_EDGE_TYPE_LENGTH:
        raise ValidationError(
            f"Edge type exceeds maximum length of {MAX_EDGE_TYPE_LENGTH} characters",
            field="edge_type",
            details={"length": len(edge_type), "max_length": MAX_EDGE_TYPE_LENGTH}
        )


def validate_edge_spec(edge_spec: Dict[str, Any]) -> None:
    """
    Validate edge specification
    
    Args:
        edge_spec: Dictionary with 'source', 'target', and optionally 'type'
        
    Raises:
        ValidationError: If edge_spec is invalid
    """
    if not isinstance(edge_spec, dict):
        raise ValidationError("Edge specification must be a dictionary", field="edge_spec")
    
    source = edge_spec.get('source')
    target = edge_spec.get('target')
    
    if not source:
        raise ValidationError("Edge source is required", field="source")
    
    if not target:
        raise ValidationError("Edge target is required", field="target")
    
    validate_node_id(source)
    validate_node_id(target)
    
    if 'type' in edge_spec and edge_spec['type']:
        validate_edge_type(edge_spec['type'])


def validate_node_ids(node_ids: List[str]) -> None:
    """
    Validate a list of node IDs
    
    Args:
        node_ids: List of node IDs to validate
        
    Raises:
        ValidationError: If any node_id is invalid
    """
    if not isinstance(node_ids, list):
        raise ValidationError(
            f"Node IDs must be a list, got {type(node_ids).__name__}",
            field="node_ids"
        )
    
    if not node_ids:
        raise ValidationError("Node IDs list cannot be empty", field="node_ids")
    
    for i, node_id in enumerate(node_ids):
        try:
            validate_node_id(node_id)
        except ValidationError as e:
            e.details["index"] = i
            raise


def validate_json_schema(data: Any, schema: Dict) -> None:
    """
    Validate data against JSON schema
    
    Args:
        data: Data to validate
        schema: JSON schema to validate against
        
    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        json_validate(instance=data, schema=schema)
    except JsonSchemaValidationError as e:
        errors = [{"path": list(e.path), "message": e.message}]
        raise SchemaValidationError(
            f"Schema validation failed: {e.message}",
            schema_errors=errors
        )


def validate_request_size(size: int, max_size: int = MAX_REQUEST_SIZE) -> None:
    """
    Validate request payload size
    
    Args:
        size: Request size in bytes
        max_size: Maximum allowed size in bytes
        
    Raises:
        RequestTooLargeError: If size exceeds max_size
    """
    if size > max_size:
        raise RequestTooLargeError(size, max_size)


def sanitize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize node/edge properties to prevent injection
    
    Args:
        properties: Dictionary of properties
        
    Returns:
        Sanitized properties dictionary
    """
    if not isinstance(properties, dict):
        return {}
    
    sanitized = {}
    for key, value in properties.items():
        # Sanitize key
        if not isinstance(key, str):
            key = str(key)
        
        # Sanitize value based on type
        if isinstance(value, str):
            # Remove null bytes and control characters
            value = value.replace('\0', '').replace('\r', '').replace('\t', ' ')
        elif isinstance(value, dict):
            value = sanitize_properties(value)
        elif isinstance(value, list):
            value = [sanitize_properties(item) if isinstance(item, dict) else item for item in value]
        
        sanitized[key] = value
    
    return sanitized


# JSON Schemas for common endpoints
IMPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "collector": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "data": {
            "type": ["object", "array"]
        }
    },
    "required": ["collector", "data"]
}

IMPORT_AUTODETECT_SCHEMA = {
    "type": "object",
    "properties": {
        "data": {
            "type": ["object", "array"]
        }
    },
    "required": ["data"]
}

PATHS_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {
            "type": "string",
            "minLength": 1,
            "maxLength": MAX_NODE_ID_LENGTH
        },
        "target": {
            "type": "string",
            "minLength": 1,
            "maxLength": MAX_NODE_ID_LENGTH
        },
        "max_depth": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20
        }
    },
    "required": ["source", "target"]
}

BULK_DELETE_NODES_SCHEMA = {
    "type": "object",
    "properties": {
        "node_ids": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": MAX_NODE_ID_LENGTH
            },
            "minItems": 1,
            "maxItems": 10000
        }
    },
    "required": ["node_ids"]
}

BULK_DELETE_EDGES_SCHEMA = {
    "type": "object",
    "properties": {
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["source", "target"]
            },
            "minItems": 1,
            "maxItems": 10000
        }
    },
    "required": ["edges"]
}

BULK_UPDATE_NODES_SCHEMA = {
    "type": "object",
    "properties": {
        "updates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "properties": {"type": "object"}
                },
                "required": ["id", "properties"]
            },
            "minItems": 1,
            "maxItems": 10000
        }
    },
    "required": ["updates"]
}

SESSION_SAVE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "metadata": {
            "type": "object"
        }
    },
    "required": ["name"]
}

QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "node_type": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}}
            ]
        },
        "edge_type": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}}
            ]
        },
        "properties": {"type": "object"},
        "text_search": {"type": "string"},
        "min_degree": {"type": "integer", "minimum": 0},
        "max_degree": {"type": "integer", "minimum": 0},
        "date_range": {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"}
            }
        }
    }
}
