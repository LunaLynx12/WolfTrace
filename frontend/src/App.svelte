<script>
  import { onMount } from 'svelte';
  import ForceGraph from 'force-graph';
  import axios from 'axios';
  import SearchBar from './components/SearchBar.svelte';
  import AnalyticsPanel from './components/AnalyticsPanel.svelte';
  import ExportButton from './components/ExportButton.svelte';
  import SessionManager from './components/SessionManager.svelte';
  import QueryBuilder from './components/QueryBuilder.svelte';
  import GraphComparison from './components/GraphComparison.svelte';
  import BulkOperations from './components/BulkOperations.svelte';
  import ReportGenerator from './components/ReportGenerator.svelte';
  import GraphTemplates from './components/GraphTemplates.svelte';
  import HistoryControls from './components/HistoryControls.svelte';
  import NodeGrouping from './components/NodeGrouping.svelte';
  import KeyboardShortcuts from './components/KeyboardShortcuts.svelte';
  import GraphStatsWidget from './components/GraphStatsWidget.svelte';
  import NodeNotes from './components/NodeNotes.svelte';
  import { cacheManager } from './utils/cache.js';
  import './App.css';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  let graphData = { nodes: [], links: [] };
  let selectedNode = null;
  let plugins = [];
  let loading = false;
  let pathResult = null;
  let sourceNode = '';
  let targetNode = '';
  let activeView = 'graph';
  let highlightedPath = null;
  let filteredNodes = null;
  let queryFilter = null;
  let selectedNodes = [];
  let diffGraph = null;
  let showShortcuts = false;
  let copiedNode = null;
  let nodeGrouping = null;
  let graphContainer;
  let graphInstance = null;

  onMount(() => {
    loadGraph();
    loadPlugins();
    initCache();
    initGraph();
    setupKeyboardShortcuts();
  });

  function initGraph() {
    // Only initialize in browser environment
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    if (graphContainer && !graphInstance) {
      graphInstance = ForceGraph()(graphContainer)
        .nodeLabel(node => `${node.id} (${node.type})`)
        .nodeColor(nodeColor)
        .linkLabel(link => `${link.type || 'RELATED_TO'}`)
        .linkColor(linkColor)
        .linkWidth(linkWidth)
        .linkDirectionalArrowLength(6)
        .linkDirectionalArrowRelPos(1)
        .onNodeClick(handleNodeClick)
        .onNodeHover((node) => {
          if (typeof document !== 'undefined' && document.body) {
            document.body.style.cursor = node ? 'pointer' : 'default';
          }
        })
        .nodeVal(node => Math.sqrt(Object.keys(node).length) * 3)
        .backgroundColor('#1a1a1a')
        .cooldownTicks(100)
        .onEngineStop(() => {
          if (graphInstance) graphInstance.zoomToFit(400);
        });
      
      updateGraph();
    }
  }

  function setupKeyboardShortcuts() {
    // Only set up in browser environment
    if (typeof window === 'undefined') return () => {};
    const handleKeyPress = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
      }
      if (e.key === 'Escape') {
        selectedNode = null;
        highlightedPath = null;
        selectedNodes = [];
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'c' && selectedNode) {
        e.preventDefault();
        copiedNode = selectedNode;
        showNotification('Node copied', 'success');
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'v' && copiedNode) {
        e.preventDefault();
        handlePasteNode();
      }
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showShortcuts = true;
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyPress);
      return () => window.removeEventListener('keydown', handleKeyPress);
    }
    return () => {};
  }

  async function initCache() {
    // Only run in browser environment
    if (typeof window === 'undefined' || typeof indexedDB === 'undefined') {
      return;
    }
    try {
      await cacheManager.init();
      const cachedGraph = await cacheManager.getGraph();
      if (cachedGraph && cachedGraph.nodes?.length > 0) {
        if (window.confirm('Load cached graph from previous session?')) {
          graphData = cachedGraph;
          updateGraph();
        }
      }
    } catch (error) {
      console.error('Cache initialization failed:', error);
    }
  }

  async function loadGraph() {
    loading = true;
    try {
      const response = await axios.get(`${API_BASE}/graph`);
      graphData = {
        nodes: response.data.nodes || [],
        links: response.data.edges || []
      };
      updateGraph();
      try {
        await cacheManager.saveGraph(graphData);
      } catch (cacheError) {
        console.error('Failed to cache graph:', cacheError);
      }
    } catch (error) {
      showNotification('Failed to load graph: ' + error.message, 'error');
    } finally {
      loading = false;
    }
  }

  function updateGraph() {
    if (graphInstance) {
      const data = getFilteredGraphData();
      graphInstance.graphData(data);
    }
  }

  async function loadPlugins() {
    try {
      const response = await axios.get(`${API_BASE}/plugins`);
      plugins = response.data;
    } catch (error) {
      console.error('Failed to load plugins:', error);
    }
  }

  function showNotification(message, type = 'info') {
    if (typeof document === 'undefined' || !document.body) return;
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      background: ${type === 'error' ? '#f44336' : '#4CAF50'};
      color: white;
      border-radius: 4px;
      z-index: 10000;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  async function handleFileUpload(event, pluginName) {
    const file = event.target.files[0];
    if (!file) return;

    loading = true;
    try {
      const text = await file.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }

      const response = await axios.post(`${API_BASE}/import`, {
        collector: pluginName,
        data: data
      });

      showNotification(`Import successful: ${response.data.result.message}`, 'success');
      await loadGraph();
    } catch (error) {
      showNotification(`Import failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  async function findPaths() {
    if (!sourceNode || !targetNode) {
      showNotification('Please enter both source and target nodes', 'error');
      return;
    }

    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/paths`, {
        source: sourceNode,
        target: targetNode,
        max_depth: 5
      });
      pathResult = response.data;
      if (response.data.length > 0) {
        highlightedPath = response.data[0];
        showNotification(`Found ${response.data.length} path(s)`, 'success');
      } else {
        showNotification('No paths found', 'info');
      }
      updateGraph();
    } catch (error) {
      showNotification(`Path finding failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  async function clearGraph() {
    if (typeof window !== 'undefined' && !window.confirm('Clear all graph data?')) {
      return;
    }
    try {
      await axios.post(`${API_BASE}/clear`);
      graphData = { nodes: [], links: [] };
      pathResult = null;
      highlightedPath = null;
      updateGraph();
      showNotification('Graph cleared', 'success');
    } catch (error) {
      showNotification(`Failed to clear: ${error.message}`, 'error');
    }
  }

  function handleNodeClick(node, event) {
    selectedNode = node;
    
    if (event?.ctrlKey || event?.metaKey) {
      if (selectedNodes.includes(node.id)) {
        selectedNodes = selectedNodes.filter(id => id !== node.id);
      } else {
        selectedNodes = [...selectedNodes, node.id];
      }
    } else {
      selectedNodes = [node.id];
    }
    
    if (graphInstance && node.x !== undefined && node.y !== undefined) {
      graphInstance.centerAt(node.x, node.y, 1000);
      graphInstance.zoom(2, 1000);
    }
  }

  async function handleUndo() {
    try {
      const response = await axios.post(`${API_BASE}/history/undo`);
      if (response.data.graph) {
        graphData = {
          nodes: response.data.graph.nodes || [],
          links: response.data.graph.edges || []
        };
        updateGraph();
        showNotification('Undone', 'success');
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        showNotification('Undo failed', 'error');
      }
    }
  }

  async function handleRedo() {
    try {
      const response = await axios.post(`${API_BASE}/history/redo`);
      if (response.data.graph) {
        graphData = {
          nodes: response.data.graph.nodes || [],
          links: response.data.graph.edges || []
        };
        updateGraph();
        showNotification('Redone', 'success');
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        showNotification('Redo failed', 'error');
      }
    }
  }

  function handleNodeSearch(node) {
    selectedNode = node;
    if (graphInstance) {
      const graphNode = graphData.nodes.find(n => n.id === node.id);
      if (graphNode && graphNode.x !== undefined && graphNode.y !== undefined) {
        graphInstance.centerAt(graphNode.x, graphNode.y, 1000);
        graphInstance.zoom(2, 1000);
      }
    }
  }

  async function handlePasteNode() {
    if (!copiedNode) return;

    try {
      const newNodeId = `${copiedNode.id}_copy_${Date.now()}`;
      const { id, x, y, vx, vy, fx, fy, ...properties } = copiedNode;
      
      await axios.post(`${API_BASE}/nodes`, {
        id: newNodeId,
        type: copiedNode.type || 'Entity',
        properties: {
          ...properties,
          copied_from: copiedNode.id
        }
      });

      showNotification('Node pasted', 'success');
      await loadGraph();
    } catch (error) {
      showNotification(`Paste failed: ${error.response?.data?.error || error.message}`, 'error');
    }
  }

  function nodeColor(node) {
    if (selectedNodes.includes(node.id)) return '#FFD700';
    if (highlightedPath && highlightedPath.includes(node.id)) return '#FFD700';
    if (diffGraph && node.change_type) {
      if (node.change_type === 'added') return '#4CAF50';
      if (node.change_type === 'removed') return '#f44336';
      if (node.change_type === 'changed') return '#FF9800';
    }
    const colors = {
      'Entity': '#4CAF50',
      'Host': '#2196F3',
      'ec2': '#FF9800',
      'Resource': '#9C27B0',
      'security-group': '#E91E63',
      'vpc': '#00BCD4',
      'default': '#607D8B'
    };
    return colors[node.type] || colors['default'];
  }

  function linkColor(link) {
    if (highlightedPath) {
      const sourceIdx = highlightedPath.indexOf(link.source.id);
      const targetIdx = highlightedPath.indexOf(link.target.id);
      if (sourceIdx !== -1 && targetIdx !== -1 && Math.abs(sourceIdx - targetIdx) === 1) {
        return '#FFD700';
      }
    }
    return 'rgba(255,255,255,0.2)';
  }

  function linkWidth(link) {
    if (highlightedPath) {
      const sourceIdx = highlightedPath.indexOf(link.source.id);
      const targetIdx = highlightedPath.indexOf(link.target.id);
      if (sourceIdx !== -1 && targetIdx !== -1 && Math.abs(sourceIdx - targetIdx) === 1) {
        return 4;
      }
    }
    return 2;
  }

  function getFilteredGraphData() {
    if (queryFilter) {
      return {
        nodes: queryFilter.nodes || [],
        links: queryFilter.edges || []
      };
    }
    if (filteredNodes) {
      return {
        nodes: graphData.nodes.filter(n => filteredNodes.includes(n.id)),
        links: graphData.links.filter(l => 
          filteredNodes.includes(l.source.id || l.source) && 
          filteredNodes.includes(l.target.id || l.target)
        )
      };
    }
    return graphData;
  }

  $: if (graphInstance && graphData) {
    updateGraph();
  }
</script>

<div class="app">
  <div class="sidebar">
    <div class="sidebar-header">
      <h1>WolfTrace</h1>
      <p class="subtitle">Modular Graph Visualization</p>
    </div>

    <div class="view-tabs">
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'graph'}
        on:click={() => activeView = 'graph'}
      >
        Graph
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'analytics'}
        on:click={() => activeView = 'analytics'}
      >
        Analytics
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'query'}
        on:click={() => activeView = 'query'}
      >
        Query
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'sessions'}
        on:click={() => activeView = 'sessions'}
      >
        Sessions
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'compare'}
        on:click={() => activeView = 'compare'}
      >
        Compare
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'bulk'}
        on:click={() => activeView = 'bulk'}
      >
        Bulk
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'templates'}
        on:click={() => activeView = 'templates'}
      >
        Templates
      </button>
      <button
        class="view-tab"
        class:view-tab-active={activeView === 'report'}
        on:click={() => activeView = 'report'}
      >
        Report
      </button>
    </div>

    <div class="sidebar-section" style="padding: 10px 0; border-bottom: 1px solid #444;">
      <HistoryControls onHistoryChange={(graph) => {
        if (graph) {
          graphData = {
            nodes: graph.nodes || [],
            links: graph.edges || []
          };
        } else {
          loadGraph();
        }
        updateGraph();
      }} />
    </div>

    {#if activeView === 'graph'}
      <div class="sidebar-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h2 style="margin: 0;">Search</h2>
          <button
            on:click={() => showShortcuts = true}
            class="btn-secondary"
            style="padding: 5px 10px; font-size: 11px;"
            title="Keyboard shortcuts (?)"
          >
            ⌨️
          </button>
        </div>
        <SearchBar 
          onNodeSelect={(node) => selectedNode = node}
          onSearch={handleNodeSearch}
          allNodes={graphData.nodes}
        />
      </div>

      <div class="sidebar-section">
        <GraphStatsWidget graphData={graphData} compact={true} />
      </div>

      <div class="sidebar-section">
        <NodeGrouping 
          graphData={graphData}
          onGroupChange={(grouping) => {
            nodeGrouping = grouping;
          }}
        />
      </div>

      <div class="sidebar-section">
        <h2>Import Data</h2>
        {#each plugins as plugin}
          <div class="plugin-item">
            <label class="plugin-label">
              {plugin.name}
              <input
                type="file"
                on:change={(e) => handleFileUpload(e, plugin.name)}
                style="display: none;"
              />
            </label>
            <small>{plugin.description}</small>
          </div>
        {/each}
      </div>

      <div class="sidebar-section">
        <h2>Path Finding</h2>
        <input
          type="text"
          placeholder="Source Node ID"
          bind:value={sourceNode}
          class="input-field"
        />
        <input
          type="text"
          placeholder="Target Node ID"
          bind:value={targetNode}
          class="input-field"
        />
        <button on:click={findPaths} class="btn-primary">Find Paths</button>
        {#if pathResult && pathResult.length > 0}
          <div class="path-result">
            <strong>Found {pathResult.length} path(s):</strong>
            {#each pathResult as path, idx}
              <button 
                type="button"
                class="path-item"
                class:path-highlighted={highlightedPath === path}
                style="cursor: pointer; background: none; border: none; text-align: left; width: 100%; padding: 8px;"
                on:click={() => highlightedPath = path}
              >
                {path.join(' → ')}
              </button>
            {/each}
          </div>
        {/if}
        {#if highlightedPath}
          <button 
            on:click={() => highlightedPath = null} 
            class="btn-secondary"
            style="margin-top: 10px;"
          >
            Clear Highlight
          </button>
        {/if}
      </div>

      <div class="sidebar-section">
        <h2>Graph Info</h2>
        <p>Nodes: {graphData.nodes.length}</p>
        <p>Edges: {graphData.links.length}</p>
        <ExportButton graphData={graphData} graphInstance={graphInstance} />
        <button on:click={clearGraph} class="btn-danger" style="margin-top: 10px;">
          Clear Graph
        </button>
      </div>

      {#if selectedNode}
        <div class="sidebar-section">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h2 style="margin: 0;">Selected Node</h2>
            <div style="display: flex; gap: 5px;">
              <button
                on:click={() => {
                  copiedNode = selectedNode;
                  showNotification('Node copied', 'success');
                }}
                class="btn-secondary"
                style="padding: 2px 8px; font-size: 11px;"
                title="Copy (Ctrl+C)"
              >
                📋
              </button>
              {#if copiedNode}
                <button
                  on:click={handlePasteNode}
                  class="btn-secondary"
                  style="padding: 2px 8px; font-size: 11px;"
                  title="Paste (Ctrl+V)"
                >
                  📄
                </button>
              {/if}
              <button 
                on:click={() => selectedNode = null} 
                class="btn-close"
                style="padding: 2px 8px; font-size: 12px;"
              >
                ×
              </button>
            </div>
          </div>
          <div class="node-details">
            <p><strong>ID:</strong> {selectedNode.id}</p>
            <p><strong>Type:</strong> {selectedNode.type}</p>
            {#each Object.entries(selectedNode).filter(([key]) => !['id', 'type', 'notes', '_notes'].includes(key)) as [key, value]}
              <p>
                <strong>{key}:</strong> {JSON.stringify(value)}
              </p>
            {/each}
          </div>
          <div style="margin-top: 15px;">
            <NodeNotes 
              node={selectedNode}
              onNoteUpdate={(nodeId, notes) => {
                if (selectedNode && selectedNode.id === nodeId) {
                  selectedNode = { ...selectedNode, notes, _notes: notes };
                }
                loadGraph();
              }}
            />
          </div>
        </div>
      {/if}
    {/if}

    {#if activeView === 'analytics'}
      <AnalyticsPanel />
    {/if}

    {#if activeView === 'query'}
      <QueryBuilder 
        onQueryResult={(result) => {
          if (result) {
            queryFilter = result;
            graphData = {
              nodes: result.nodes || [],
              links: result.edges || []
            };
          } else {
            queryFilter = null;
            loadGraph();
          }
          updateGraph();
        }}
      />
    {/if}

    {#if activeView === 'sessions'}
      <SessionManager 
        onLoadSession={loadGraph}
        currentGraphData={graphData}
      />
    {/if}

    {#if activeView === 'compare'}
      <GraphComparison
        currentGraph={graphData}
        onLoadDiffGraph={(diffData) => {
          diffGraph = diffData;
          graphData = {
            nodes: diffData.nodes || [],
            links: diffData.edges || []
          };
          updateGraph();
        }}
      />
    {/if}

    {#if activeView === 'bulk'}
      <BulkOperations
        selectedNodes={selectedNodes}
        onOperationComplete={loadGraph}
      />
    {/if}

    {#if activeView === 'templates'}
      <GraphTemplates
        onTemplateApplied={loadGraph}
      />
    {/if}

    {#if activeView === 'report'}
      <ReportGenerator />
    {/if}
  </div>

  <KeyboardShortcuts 
    isOpen={showShortcuts}
    onClose={() => showShortcuts = false}
  />

  <div class="graph-container">
    <div style="position: absolute; top: 10px; right: 10px; z-index: 1000;">
      <GraphStatsWidget graphData={graphData} compact={true} />
    </div>
    {#if loading}
      <div class="loading">Loading...</div>
    {/if}
    <div bind:this={graphContainer}></div>
  </div>
</div>

