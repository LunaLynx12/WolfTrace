"""
Validation and Error Handling Tests
Tests for validators and exception classes
"""
import sys
import pytest
from pathlib import Path

# Ensure backend root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exceptions import (
    ValidationError,
    NodeNotFoundError,
    InvalidNodeIdError,
    RequestTooLargeError
)
from validators import (
    validate_node_id,
    validate_node_ids,
    validate_edge_spec,
    validate_request_size,
    sanitize_properties,
    MAX_REQUEST_SIZE
)


def test_node_id_valid():
    """Test that valid node IDs are accepted"""
    validate_node_id("host-192.168.1.1")
    validate_node_id("user:john.doe@example.com")
    validate_node_id("server_001")


def test_node_id_empty():
    """Test that empty node IDs are rejected"""
    with pytest.raises(ValidationError):
        validate_node_id("")


def test_node_id_too_long():
    """Test that overly long node IDs are rejected"""
    with pytest.raises(ValidationError):
        validate_node_id("a" * 501)


def test_node_id_special_chars():
    """Test that node IDs with invalid characters are rejected"""
    with pytest.raises(InvalidNodeIdError):
        validate_node_id("node<script>")


def test_node_id_null_byte():
    """Test that node IDs with null bytes are rejected"""
    with pytest.raises(InvalidNodeIdError):
        validate_node_id("node\x00id")


def test_edge_spec_valid():
    """Test that valid edge specs are accepted"""
    validate_edge_spec({
        'source': 'node1',
        'target': 'node2',
        'type': 'CONNECTS_TO'
    })


def test_edge_spec_missing_source():
    """Test that edge specs without source are rejected"""
    with pytest.raises(ValidationError):
        validate_edge_spec({'target': 'node2'})


def test_edge_spec_missing_target():
    """Test that edge specs without target are rejected"""
    with pytest.raises(ValidationError):
        validate_edge_spec({'source': 'node1'})


def test_request_size_valid():
    """Test that normal request sizes are accepted"""
    validate_request_size(1000, MAX_REQUEST_SIZE)


def test_request_size_too_large():
    """Test that oversized requests are rejected"""
    with pytest.raises(RequestTooLargeError):
        validate_request_size(MAX_REQUEST_SIZE + 1, MAX_REQUEST_SIZE)


def test_property_sanitization_null_bytes():
    """Test that null bytes are removed from properties"""
    props = {'name': 'test\x00name'}
    sanitized = sanitize_properties(props)
    assert '\x00' not in sanitized.get('name', '')


def test_property_sanitization_carriage_return():
    """Test that carriage returns are removed from properties"""
    props = {'description': 'test\rdescription'}
    sanitized = sanitize_properties(props)
    assert '\r' not in sanitized.get('description', '')


def test_property_sanitization_nested():
    """Test that null bytes are removed from nested properties"""
    props = {'nested': {'value': 'nested\x00value'}}
    sanitized = sanitize_properties(props)
    assert '\x00' not in sanitized.get('nested', {}).get('value', '')


def test_validation_error_serialization():
    """Test that ValidationError serializes correctly"""
    error = ValidationError("Invalid input", field="node_id")
    error_dict = error.to_dict()
    
    assert 'error' in error_dict
    assert error_dict['error_code'] == 'VALIDATION_ERROR'
    assert error_dict['details'].get('field') == 'node_id'


def test_node_not_found_error_serialization():
    """Test that NodeNotFoundError serializes correctly"""
    error = NodeNotFoundError("node123")
    error_dict = error.to_dict()
    
    assert error_dict['error_code'] == 'NODE_NOT_FOUND'
    assert error_dict['details'].get('node_id') == 'node123'
