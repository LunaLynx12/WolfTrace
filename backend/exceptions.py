"""
Custom Exception Classes for WolfTrace Backend
Provides detailed error codes and messages for better error handling
"""


class WolfTraceException(Exception):
    """Base exception for WolfTrace errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for API response"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(WolfTraceException):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", error_details)


class NodeNotFoundError(WolfTraceException):
    """Raised when a node is not found"""
    def __init__(self, node_id: str):
        super().__init__(
            f"Node '{node_id}' not found",
            "NODE_NOT_FOUND",
            {"node_id": node_id}
        )


class EdgeNotFoundError(WolfTraceException):
    """Raised when an edge is not found"""
    def __init__(self, source: str, target: str):
        super().__init__(
            f"Edge from '{source}' to '{target}' not found",
            "EDGE_NOT_FOUND",
            {"source": source, "target": target}
        )


class PluginError(WolfTraceException):
    """Raised when plugin operations fail"""
    def __init__(self, plugin_name: str, message: str, details: dict = None):
        error_details = details or {}
        error_details["plugin"] = plugin_name
        super().__init__(
            f"Plugin '{plugin_name}' error: {message}",
            "PLUGIN_ERROR",
            error_details
        )


class PluginNotFoundError(WolfTraceException):
    """Raised when a plugin is not found"""
    def __init__(self, plugin_name: str):
        super().__init__(
            f"Plugin '{plugin_name}' not found",
            "PLUGIN_NOT_FOUND",
            {"plugin": plugin_name}
        )


class SessionError(WolfTraceException):
    """Raised when session operations fail"""
    def __init__(self, message: str, session_id: str = None, details: dict = None):
        error_details = details or {}
        if session_id:
            error_details["session_id"] = session_id
        super().__init__(message, "SESSION_ERROR", error_details)


class ImportError(WolfTraceException):
    """Raised when data import fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "IMPORT_ERROR", details)


class QueryError(WolfTraceException):
    """Raised when query execution fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "QUERY_ERROR", details)


class InvalidNodeIdError(ValidationError):
    """Raised when node ID contains invalid characters"""
    def __init__(self, node_id: str, invalid_chars: list):
        super().__init__(
            f"Node ID '{node_id}' contains invalid characters: {', '.join(invalid_chars)}",
            field="node_id",
            details={"node_id": node_id, "invalid_characters": invalid_chars}
        )


class InvalidEdgeIdError(ValidationError):
    """Raised when edge ID contains invalid characters"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, field="edge_id", details=details)


class RequestTooLargeError(WolfTraceException):
    """Raised when request payload exceeds size limit"""
    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"Request size {size} bytes exceeds maximum {max_size} bytes",
            "REQUEST_TOO_LARGE",
            {"size": size, "max_size": max_size}
        )


class SchemaValidationError(ValidationError):
    """Raised when JSON schema validation fails"""
    def __init__(self, message: str, schema_errors: list = None):
        super().__init__(
            message,
            field="request_body",
            details={"schema_errors": schema_errors or []}
        )
