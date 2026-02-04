import pytest


def test_nodes_pagination_and_cache(graph_engine_fixture):
    ge = graph_engine_fixture
    for i in range(15):
        ge.add_node(f"n{i}", "Host", {"index": i})
    page1 = ge.get_nodes_paginated(limit=10)
    assert len(page1["items"]) == 10
    assert page1["next_cursor"] is not None
    page2 = ge.get_nodes_paginated(limit=10, cursor=page1["next_cursor"])
    assert len(page2["items"]) == 5
    # cache should serve identical result without changes
    cached = ge.get_nodes_paginated(limit=10)
    assert cached["items"] == page1["items"]


def test_edges_pagination(graph_engine_fixture):
    ge = graph_engine_fixture
    for i in range(5):
        ge.add_node(f"n{i}")
    for i in range(8):
        ge.add_edge(f"n{i%5}", f"n{(i+1)%5}", "REL", {"idx": i})
    page = ge.get_edges_paginated(limit=3)
    assert len(page["items"]) == 3
    assert page["next_cursor"] is not None


def test_paths_bounded_and_max(graph_engine_fixture):
    ge = graph_engine_fixture
    # build a small chain
    for i in range(6):
        ge.add_node(f"n{i}")
    for i in range(5):
        ge.add_edge(f"n{i}", f"n{i+1}")
    paths = ge.find_paths("n0", "n5", max_depth=6, max_paths=2)
    assert len(paths) == 1  # only one simple path
    # ensure depth cutoff works
    shallow = ge.find_paths("n0", "n5", max_depth=3)
    assert shallow == []


def test_cache_invalidation_on_add(graph_engine_fixture):
    ge = graph_engine_fixture
    ge.add_node("a")
    first = ge.get_nodes()
    ge.add_node("b")
    second = ge.get_nodes()
    assert len(first) + 1 == len(second)


def test_remove_node_and_edge_updates_indices(graph_engine_fixture):
    ge = graph_engine_fixture
    ge.add_node("s", "Host")
    ge.add_node("t", "Host")
    ge.add_edge("s", "t", "REL")
    assert "Host" in ge.node_index_by_type
    assert ("s", "t", "REL") in ge.edge_index_by_type.get("REL", set())
    removed = ge.remove_node("s")
    assert removed["deleted"] is True
    assert "s" not in ge.node_index_by_type.get("Host", set())
    assert ("s", "t", "REL") not in ge.edge_index_by_type.get("REL", set())
