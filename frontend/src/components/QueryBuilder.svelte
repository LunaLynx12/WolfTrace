<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

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
  let typesLoaded = false;

  // Performance: Lazy load node types only when component becomes visible
  async function loadNodeTypes() {
    if (typesLoaded) return; // Already loaded
    
    try {
      const response = await axios.get(`${API_BASE}/analytics/stats`);
      if (response.data.node_types) {
        availableTypes = Object.keys(response.data.node_types);
        typesLoaded = true;
      }
    } catch (error) {
      console.error('Failed to load node types:', error);
    }
  }

  // Load types when component is first rendered (but not on mount to avoid blocking)
  $: if (!typesLoaded && availableTypes.length === 0) {
    // Use requestIdleCallback or setTimeout to defer loading
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(() => loadNodeTypes());
    } else {
      setTimeout(() => loadNodeTypes(), 100);
    }
  }

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
      showNotification(`Query failed: ${error.response?.data?.error || error.message}`, 'error');
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

  <fieldset class="query-section" style="border: none; padding: 0; margin: 0 0 12px 0;">
    <legend style="font-size: 14px; margin-bottom: 6px;">Node Types</legend>
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
  </fieldset>

  <div class="query-section">
    <label for="qb-text-search">Text Search</label>
    <input
      type="text"
      placeholder="Search in node IDs and properties"
      id="qb-text-search"
      bind:value={filters.text_search}
      class="input-field"
    />
  </div>

  <fieldset class="query-section" style="border: none; padding: 0; margin: 0;">
    <legend style="font-size: 14px; margin-bottom: 6px;">Degree Range</legend>
    <div style="display: flex; gap: 5px;">
      <input
        type="number"
        placeholder="Min"
        id="qb-min-degree"
        bind:value={filters.min_degree}
        class="input-field"
        style="flex: 1;"
        aria-label="Minimum degree"
      />
      <input
        type="number"
        placeholder="Max"
        id="qb-max-degree"
        bind:value={filters.max_degree}
        class="input-field"
        style="flex: 1;"
        aria-label="Maximum degree"
      />
    </div>
  </fieldset>

  <div style="display: flex; gap: 8px; margin-top: 12px;">
    <Button on:click={executeQuery} disabled={loading} fullWidth={false} size="sm">
      <i class="bi bi-search" style="margin-right:8px;"></i>
      {loading ? 'Querying…' : 'Run Query'}
    </Button>
    <Button variant="secondary" on:click={clearQuery} fullWidth={false} size="sm">
      <i class="bi bi-arrow-counterclockwise" style="margin-right:8px;"></i>
      Reset
    </Button>
  </div>

  {#if queryResult}
    <div class="query-result">
      <strong>Results:</strong> {queryResult.nodes?.length || 0} nodes, {queryResult.edges?.length || 0} edges
    </div>
  {/if}
</div>

