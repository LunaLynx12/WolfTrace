<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  let stats = null;
  let communities = [];
  let loading = false;
  let activeTab = 'stats';
  // Performance: Cache Object.entries() to avoid recalculating on every render
  let nodeTypesEntries = [];

  onMount(() => {
    loadStats();
  });

  async function loadStats() {
    loading = true;
    try {
      // Performance: Only load stats on mount, communities will be lazy loaded
      const statsRes = await axios.get(`${API_BASE}/analytics/stats`);
      stats = statsRes.data;
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      loading = false;
    }
  }
  
  // Performance: Cache Object.entries() result in reactive statement
  $: if (stats && stats.node_types) {
    nodeTypesEntries = Object.entries(stats.node_types);
  } else {
    nodeTypesEntries = [];
  }

  // Performance: Lazy load communities only when tab is clicked
  async function loadCommunities() {
    if (communities.length > 0) return; // Already loaded
    
    try {
      const commRes = await axios.get(`${API_BASE}/analytics/communities`);
      communities = commRes.data;
    } catch (error) {
      console.error('Failed to load communities:', error);
    }
  }
</script>

{#if loading}
  <div class="analytics-panel">Loading analytics...</div>
{:else if !stats || stats.error}
  <div class="analytics-panel">
    <p>No analytics data available</p>
    <button on:click={loadStats} class="btn-primary">Refresh</button>
  </div>
{:else}
  <div class="analytics-panel">
    <div class="analytics-tabs">
      <button
        class="tab"
        class:tab-active={activeTab === 'stats'}
        on:click={() => activeTab = 'stats'}
      >
        Statistics
      </button>
      <button
        class="tab"
        class:tab-active={activeTab === 'communities'}
        on:click={() => {
          activeTab = 'communities';
          loadCommunities(); // Lazy load when tab is clicked
        }}
      >
        Communities
      </button>
    </div>

    {#if activeTab === 'stats'}
      <div class="analytics-content">
        <div class="stat-section">
          <h3>Basic Metrics</h3>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="stat-label">Nodes</span>
              <span class="stat-value">{stats.basic?.nodes || 0}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Edges</span>
              <span class="stat-value">{stats.basic?.edges || 0}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Degree</span>
              <span class="stat-value">{stats.basic?.average_degree || 0}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Components</span>
              <span class="stat-value">{stats.basic?.connected_components || 0}</span>
            </div>
          </div>
        </div>

        {#if stats.top_nodes_by_degree && stats.top_nodes_by_degree.length > 0}
          <div class="stat-section">
            <h3>Top Nodes by Degree</h3>
            <div class="top-nodes-list">
              {#each stats.top_nodes_by_degree as item}
                <div class="top-node-item">
                  <span>{item.id}</span>
                  <span class="centrality-value">{item.centrality.toFixed(4)}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if stats.node_types}
          <div class="stat-section">
            <h3>Node Types</h3>
            <div class="type-distribution">
              {#each nodeTypesEntries as [type, count]}
                <div class="type-item">
                  <span>{type}</span>
                  <span>{count}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    {#if activeTab === 'communities'}
      <div class="analytics-content">
        <h3>Detected Communities</h3>
        {#if communities.length > 0}
          <div class="communities-list">
            {#each communities as comm}
              <div class="community-item">
                <div class="community-header">
                  <strong>Community {comm.id + 1}</strong>
                  <span>{comm.size} nodes</span>
                </div>
                {#if comm.nodes}
                  <div class="community-nodes">
                    {#each comm.nodes.slice(0, 5) as node}
                      <span class="community-node">{node}</span>
                    {/each}
                    {#if comm.nodes.length > 5}
                      <span>...</span>
                    {/if}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <p>No communities detected</p>
        {/if}
      </div>
    {/if}
  </div>
{/if}

