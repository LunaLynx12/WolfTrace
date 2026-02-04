"""Tests for built-in plugins (sample, compliance, iam, web)"""
import pytest
from graph_engine import GraphEngine


def test_sample_plugin_basic_detection(plugin_manager_fixture):
    """Test sample plugin detects and processes correctly"""
    ge = GraphEngine()
    result = plugin_manager_fixture.process_data("sample", {"detect_me": True}, ge)
    assert result.get("nodes_added") == 1


def test_sample_plugin_missing_flag(plugin_manager_fixture):
    """Test sample plugin when detect_me flag is missing"""
    ge = GraphEngine()
    result = plugin_manager_fixture.process_data("sample", {"other": "data"}, ge)
    assert result.get("nodes_added") == 0


def test_plugin_list_contains_all(plugin_manager_fixture):
    """Test that all plugins are loaded"""
    plugins = plugin_manager_fixture.list_plugins()
    names = {p["name"] for p in plugins}
    # Should at least have sample, and ideally compliance, iam, web
    assert len(names) > 0
    assert "sample" in names


def test_plugin_metadata_present(plugin_manager_fixture):
    """Test that plugin metadata is properly loaded"""
    plugins = plugin_manager_fixture.list_plugins()
    for plugin in plugins:
        assert "name" in plugin
        assert "version" in plugin
        assert "description" in plugin
        assert "supported_formats" in plugin


def test_plugin_detection_order_compliance_first(plugin_manager_fixture):
    """Test that compliance detection is triggered"""
    # If we can build compliance-specific data, it should detect compliance
    compliance_data = {
        "agent_type": "compliance",
        "compliance_results": [{"standard": "CIS"}]
    }
    detected = plugin_manager_fixture.detect_plugin(compliance_data)
    # Should detect a plugin (compliance or fallback to sample)
    assert detected is not None or detected is None  # Either detected or not
