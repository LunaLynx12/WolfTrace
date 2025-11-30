<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let graphData;
  export let compact = false;

  let stats = null;
  let loading = false;
  // Performance: Cache hash to prevent unnecessary API calls
  let lastStatsHash = '';
  // Performance: Cache Object.entries() to avoid recalculating on every render
  let nodeTypesEntries = [];

  $: if (graphData && graphData.nodes && graphData.nodes.length > 0) {
    // Performance: Only load stats if data actually changed
    const hash = `${graphData.nodes.length}-${graphData.links.length}`;
    if (hash !== lastStatsHash) {
      lastStatsHash = hash;
      loadStats();
    }
  } else {
    stats = null;
    lastStatsHash = '';
    nodeTypesEntries = [];
  }
  
  // Performance: Cache Object.entries() result in reactive statement
  $: if (stats && stats.node_types) {
    nodeTypesEntries = Object.entries(stats.node_types).slice(0, 5);
  } else {
    nodeTypesEntries = [];
  }

  async function loadStats() {
    loading = true;
    try {
      const response = await axios.get(`${API_BASE}/analytics/stats`);
      stats = response.data;
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      loading = false;
    }
  }
</script>

{#if !graphData || !graphData.nodes || graphData.nodes.length === 0}
  <div class="graph-stats-widget" style="font-size: 12px; color: #888;">
    No graph data
  </div>
{:else if compact}
  <div class="graph-stats-widget compact">
    <div class="stat-mini">
      <span class="stat-label">Nodes: <span class="stat-value">{graphData.nodes.length}</span></span>
    </div>
    <div class="stat-mini">
      <span class="stat-label">Edges: <span class="stat-value">{graphData.links.length}</span></span>
    </div>
    {#if stats && stats.basic}
      <div class="stat-mini">
        <span class="stat-label">Components: <span class="stat-value">{stats.basic.connected_components || 0}</span></span>
      </div>
      <div class="stat-mini">
        <span class="stat-label">Avg Degree: <span class="stat-value">{stats.basic.average_degree?.toFixed(1) || 0}</span></span>
      </div>
    {/if}
  </div>
{:else}
  <div class="graph-stats-widget">
    <h4 style="margin-bottom: 10px; font-size: 14px;">Graph Statistics</h4>
    {#if loading}
      <div style="color: #888; font-size: 12px;">Loading...</div>
    {:else if stats}
      <div class="stat-grid-mini">
        <div class="stat-item-mini">
          <div class="stat-label">Nodes</div>
          <div class="stat-value">{graphData.nodes.length}</div>
        </div>
        <div class="stat-item-mini">
          <div class="stat-label">Edges</div>
          <div class="stat-value">{graphData.links.length}</div>
        </div>
        {#if stats.basic}
          <div class="stat-item-mini">
            <div class="stat-label">Components</div>
            <div class="stat-value">{stats.basic.connected_components || 0}</div>
          </div>
          <div class="stat-item-mini">
            <div class="stat-label">Avg Degree</div>
            <div class="stat-value">{stats.basic.average_degree?.toFixed(2) || 0}</div>
          </div>
        {/if}
      </div>
      {#if stats.node_types}
        <div style="margin-top: 10px;">
          <div style="font-size: 12px; color: #aaa; margin-bottom: 5px;">Node Types:</div>
          {#each nodeTypesEntries as [type, count]}
            <div style="font-size: 11px; color: #888; margin-bottom: 2px;">
              {type}: {count}
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
{/if}

