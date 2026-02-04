
def test_health_endpoint(app_client):
    client, _ = app_client
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('status') == 'ok'


def test_nodes_edges_pagination_flow(app_client):
    client, ge = app_client
    for i in range(12):
        ge.add_node(f"n{i}", "Host")
    for i in range(6):
        ge.add_edge(f"n{i}", f"n{(i+1)%12}", "REL")

    first_page = client.get('/api/nodes?limit=5')
    assert first_page.status_code == 200
    body = first_page.get_json()
    assert len(body['items']) == 5
    assert body['next_cursor'] is not None

    second_page = client.get(f"/api/nodes?limit=5&cursor={body['next_cursor']}")
    assert second_page.status_code == 200
    body2 = second_page.get_json()
    assert len(body2['items']) <= 5

    edges_resp = client.get('/api/edges?limit=2')
    assert edges_resp.status_code == 200
    edges = edges_resp.get_json()
    assert len(edges['items']) == 2
    assert edges['next_cursor'] is not None


def test_paths_endpoint_returns_path(app_client):
    client, ge = app_client
    for i in range(4):
        ge.add_node(f"p{i}")
    for i in range(3):
        ge.add_edge(f"p{i}", f"p{i+1}")

    resp = client.post('/api/paths', json={
        'source': 'p0',
        'target': 'p3',
        'max_depth': 5,
        'max_paths': 3
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data[0][0] == 'p0' and data[0][-1] == 'p3'


def test_session_save_and_restore_flow(app_client):
    client, ge = app_client
    ge.add_node('s1', 'Host')
    ge.add_node('s2', 'Host')
    ge.add_edge('s1', 's2', 'REL')

    save_resp = client.post('/api/sessions', json={'name': 'test-session', 'metadata': {'env': 'dev'}})
    assert save_resp.status_code == 200
    session_info = save_resp.get_json()
    session_id = session_info['id']

    clear_resp = client.post('/api/clear')
    assert clear_resp.status_code == 200
    assert len(ge.graph.nodes) == 0

    restore_resp = client.post(f"/api/sessions/{session_id}/restore")
    assert restore_resp.status_code == 200
    assert len(ge.graph.nodes) == 2
    assert ge.graph.has_edge('s1', 's2')


def test_list_plugins_endpoint(app_client):
    client, _ = app_client
    resp = client.get('/api/plugins')
    assert resp.status_code == 200
    plugins = resp.get_json()
    assert len(plugins) > 0
    for plugin in plugins:
        assert 'name' in plugin
        assert 'version' in plugin


def test_import_with_invalid_plugin_returns_404(app_client):
    client, _ = app_client
    result = client.post('/api/import', json={
        'collector': 'nonexistent_plugin',
        'data': {}
    })
    assert result.status_code == 404
    data = result.get_json()
    assert 'PLUGIN_NOT_FOUND' in data.get('error_code', '')


def test_import_autodetect_returns_detected_plugin(app_client):
    client, ge = app_client
    # Send data that can be detected by one of the real plugins
    result = client.post('/api/import-autodetect', json={
        'data': {'users': [], 'roles': []}
    })
    assert result.status_code == 200
    data = result.get_json()
    # Should have detected a plugin (could be iam, compliance, etc.)
    assert data.get('detected_plugin') is not None
