<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  // currentGraph was unused and triggered a warning; keep for external reference if needed
  export const currentGraph = undefined;
  export let onLoadDiffGraph;

  let session1 = '';
  let session2 = '';
  let graph1Data = null;
  let graph2Data = null;
  let comparison = null;
  let loading = false;
  let sessions = [];
  let sessionsLoaded = false;

  // Performance: Lazy load sessions only when component becomes visible or when needed
  async function loadSessions() {
    if (sessionsLoaded) return; // Already loaded
    
    try {
      const response = await axios.get(`${API_BASE}/sessions`);
      sessions = response.data;
      sessionsLoaded = true;
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }

  // Load sessions when component is first rendered (deferred)
  $: if (!sessionsLoaded && sessions.length === 0) {
    // Use requestIdleCallback or setTimeout to defer loading
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(() => loadSessions());
    } else {
      setTimeout(() => loadSessions(), 200);
    }
  }

  async function loadSession(sessionId, setter) {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}`);
      setter({
        nodes: response.data.graph?.nodes || [],
        edges: response.data.graph?.edges || []
      });
    } catch (error) {
      showNotification(`Failed to load session: ${error.message}`, 'error');
    }
  }

  async function compareGraphs() {
    if (!graph1Data || !graph2Data) {
      showNotification('Please load both graphs to compare', 'error');
      return;
    }

    loading = true;
    try {
      // Performance: Load both API calls in parallel using Promise.all()
      const [compareResponse, diffResponse] = await Promise.all([
        axios.post(`${API_BASE}/compare`, {
          graph1: { nodes: graph1Data.nodes, edges: graph1Data.edges },
          graph2: { nodes: graph2Data.nodes, edges: graph2Data.edges }
        }),
        axios.post(`${API_BASE}/compare/diff-graph`, {
          graph1: { nodes: graph1Data.nodes, edges: graph1Data.edges },
          graph2: { nodes: graph2Data.nodes, edges: graph2Data.edges }
        })
      ]);
      
      comparison = compareResponse.data;
      
      if (onLoadDiffGraph) {
        onLoadDiffGraph({
          nodes: diffResponse.data.nodes || [],
          edges: diffResponse.data.edges || []
        });
      }
    } catch (error) {
      showNotification(`Comparison failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="graph-comparison">
  <h3>Graph Comparison</h3>

  <div style="margin-bottom: 15px;">
    <label for="gc-session1">Graph 1 (Session)</label>
    <select id="gc-session1" bind:value={session1} on:focus={() => loadSessions()} on:change={() => {
      loadSessions(); // Ensure sessions are loaded
      loadSession(session1, (d) => graph1Data = d);
    }} class="input-field">
      <option value="">Select session...</option>
      {#each sessions as session}
        <option value={session.id}>{session.name}</option>
      {/each}
    </select>
    {#if graph1Data}
      <small style="color: #4CAF50;">Loaded: {graph1Data.nodes.length} nodes</small>
    {/if}
  </div>

  <div style="margin-bottom: 15px;">
    <label for="gc-session2">Graph 2 (Session)</label>
    <select id="gc-session2" bind:value={session2} on:focus={() => loadSessions()} on:change={() => {
      loadSessions(); // Ensure sessions are loaded
      loadSession(session2, (d) => graph2Data = d);
    }} class="input-field">
      <option value="">Select session...</option>
      {#each sessions as session}
        <option value={session.id}>{session.name}</option>
      {/each}
    </select>
    {#if graph2Data}
      <small style="color: #4CAF50;">Loaded: {graph2Data.nodes.length} nodes</small>
    {/if}
  </div>

  <Button
    on:click={compareGraphs}
    disabled={!graph1Data || !graph2Data || loading}
  >
    {loading ? 'Comparing...' : 'Compare Graphs'}
  </Button>

  {#if comparison}
    <div style="margin-top: 15px; padding: 10px; background: #333; border-radius: 4px; font-size: 12px;">
      <strong>Comparison Results:</strong>
      <div style="margin-top: 5px;">
        <div>Added: {comparison.added_nodes || 0} nodes, {comparison.added_edges || 0} edges</div>
        <div>Removed: {comparison.removed_nodes || 0} nodes, {comparison.removed_edges || 0} edges</div>
        <div>Changed: {comparison.changed_nodes || 0} nodes</div>
      </div>
    </div>
  {/if}
</div>

