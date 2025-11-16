<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onQueryResult;

  let filters = {
    node_type: [],
    text_search: '',
    min_degree: '',
    max_degree: ''
  };
  let queryResult = null;
  let loading = false;
  let availableTypes = [];

  onMount(async () => {
    try {
      const response = await axios.get(`${API_BASE}/analytics/stats`);
      if (response.data.node_types) {
        availableTypes = Object.keys(response.data.node_types);
      }
    } catch (error) {
      console.error('Failed to load node types:', error);
    }
  });

  function toggleNodeType(type) {
    if (filters.node_type.includes(type)) {
      filters.node_type = filters.node_type.filter(t => t !== type);
    } else {
      filters.node_type = [...filters.node_type, type];
    }
  }

  async function executeQuery() {
    loading = true;
    try {
      const queryFilters = {};
      
      if (filters.node_type.length > 0) {
        queryFilters.node_type = filters.node_type;
      }
      
      if (filters.text_search) {
        queryFilters.text_search = filters.text_search;
      }
      
      if (filters.min_degree || filters.max_degree) {
        if (filters.min_degree) queryFilters.min_degree = parseInt(filters.min_degree);
        if (filters.max_degree) queryFilters.max_degree = parseInt(filters.max_degree);
      }
      
      const response = await axios.post(`${API_BASE}/query`, queryFilters);
      queryResult = response.data;
      if (onQueryResult) {
        onQueryResult(response.data);
      }
    } catch (error) {
      alert(`Query failed: ${error.response?.data?.error || error.message}`);
    } finally {
      loading = false;
    }
  }

  function clearQuery() {
    filters = {
      node_type: [],
      text_search: '',
      min_degree: '',
      max_degree: ''
    };
    queryResult = null;
    if (onQueryResult) {
      onQueryResult(null);
    }
  }
</script>

<div class="query-builder">
  <h3>Query Builder</h3>

  <div class="query-section">
    <label>Node Types</label>
    <div class="type-checkboxes">
      {#each availableTypes as type}
        <label class="checkbox-label">
          <input
            type="checkbox"
            checked={filters.node_type.includes(type)}
            on:change={() => toggleNodeType(type)}
          />
          {type}
        </label>
      {/each}
    </div>
  </div>

  <div class="query-section">
    <label>Text Search</label>
    <input
      type="text"
      placeholder="Search in node IDs and properties"
      bind:value={filters.text_search}
      class="input-field"
    />
  </div>

  <div class="query-section">
    <label>Degree Range</label>
    <div style="display: flex; gap: 5px;">
      <input
        type="number"
        placeholder="Min"
        bind:value={filters.min_degree}
        class="input-field"
        style="flex: 1;"
      />
      <input
        type="number"
        placeholder="Max"
        bind:value={filters.max_degree}
        class="input-field"
        style="flex: 1;"
      />
    </div>
  </div>

  <div style="display: flex; gap: 5px; margin-top: 15px;">
    <button on:click={executeQuery} disabled={loading} class="btn-primary" style="flex: 1;">
      {loading ? 'Querying...' : 'Execute Query'}
    </button>
    <button on:click={clearQuery} class="btn-secondary" style="flex: 1;">
      Clear
    </button>
  </div>

  {#if queryResult}
    <div class="query-result">
      <strong>Results:</strong> {queryResult.nodes?.length || 0} nodes, {queryResult.edges?.length || 0} edges
    </div>
  {/if}
</div>

