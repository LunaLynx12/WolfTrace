import os
import sys
import importlib
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def _env_memory_backend():
    # Force memory backend for tests
    os.environ.setdefault("DB_BACKEND", "memory")
    yield


@pytest.fixture(scope="session")
def flask_app():
    import app as app_module
    # ensure fresh state
    importlib.reload(app_module)
    return app_module.app, app_module.graph_engine


@pytest.fixture()
def app_client(flask_app):
    app, graph_engine = flask_app
    graph_engine.clear()
    with app.test_client() as client:
        yield client, graph_engine


@pytest.fixture()
def graph_engine_fixture():
    from graph_engine import GraphEngine
    ge = GraphEngine()
    ge.clear()
    yield ge


@pytest.fixture()
def temp_plugins_dir(tmp_path):
    plugins_root = tmp_path / "plugins"
    sample = plugins_root / "sample"
    sample.mkdir(parents=True)
    # metadata
    (sample / "metadata.json").write_text(
        '{"name": "sample", "version": "1.0.0", "supported_formats": ["sample"]}'
    )
    # plugin implementation
    (sample / "plugin.py").write_text(
        """
import logging
logger = logging.getLogger(__name__)

def process(data, graph_engine):
    # simple handler that adds a node when flag present
    if isinstance(data, dict) and data.get('detect_me'):
        graph_engine.add_node('node-sample', 'Entity', {'name': 'sample'})
        return {'nodes_added': 1, 'edges_added': 0}
    return {'nodes_added': 0, 'edges_added': 0}
        """
    )
    return str(plugins_root)


@pytest.fixture()
def plugin_manager_fixture(temp_plugins_dir):
    from plugin_manager import PluginManager
    return PluginManager(plugins_dir=temp_plugins_dir)
