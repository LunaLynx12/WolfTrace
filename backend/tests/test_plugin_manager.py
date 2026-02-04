import pytest

from graph_engine import GraphEngine


def test_list_plugins_includes_sample(plugin_manager_fixture):
    plugins = plugin_manager_fixture.list_plugins()
    names = {p["name"] for p in plugins}
    assert "sample" in names


def test_process_data_adds_node(plugin_manager_fixture):
    ge = GraphEngine()
    result = plugin_manager_fixture.process_data("sample", {"detect_me": True}, ge)
    assert result.get("nodes_added") == 1
    assert ge.graph.has_node("node-sample")


def test_detect_plugin_fallback(plugin_manager_fixture):
    detected = plugin_manager_fixture.detect_plugin({"detect_me": True})
    assert detected == "sample"


def test_missing_plugin_raises(plugin_manager_fixture):
    with pytest.raises(ValueError):
        plugin_manager_fixture.process_data("nope", {}, GraphEngine())
