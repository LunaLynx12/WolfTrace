<script>
  import { onMount, onDestroy } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onNodeSelect;
  export let onSearch;
  export let allNodes = [];

  let query = '';
  let results = [];
  let showResults = false;
  let filters = {
    nodeType: '',
    hasProperty: '',
    propertyValue: ''
  };
  let showFilters = false;
  let searchTimeout;
  
  // Memory leak fix: Clean up timeout on component destroy
  onDestroy(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
      searchTimeout = null;
    }
  });

  $: if (query.length > 2 || filters.nodeType || filters.hasProperty) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      searchNodes(query, filters);
    }, 300);
  } else {
    results = [];
  }

  async function searchNodes(searchQuery, searchFilters) {
    try {
      if (allNodes && allNodes.length > 0) {
        let filtered = allNodes;
        
        // Performance: Pre-compute lowercase query once
        const lowerQuery = searchQuery ? searchQuery.toLowerCase() : '';
        
        if (lowerQuery) {
          // Performance: More efficient filtering - check ID first (most common case)
          // Avoid Object.values() which creates new array on every check
          filtered = filtered.filter(node => {
            const nodeId = (node.id || '').toLowerCase();
            if (nodeId.includes(lowerQuery)) return true;
            
            // Only check properties if ID doesn't match - iterate keys directly
            // This avoids creating Object.values() array
            for (const key in node) {
              if (key === 'id') continue; // Already checked
              const val = node[key];
              if (typeof val === 'string' && val.toLowerCase().includes(lowerQuery)) {
                return true;
              }
            }
            return false;
          });
        }
        
        if (searchFilters.nodeType) {
          filtered = filtered.filter(node => node.type === searchFilters.nodeType);
        }
        
        if (searchFilters.hasProperty) {
          filtered = filtered.filter(node => {
            if (searchFilters.propertyValue) {
              return node[searchFilters.hasProperty] === searchFilters.propertyValue;
            }
            return searchFilters.hasProperty in node;
          });
        }
        
        results = filtered.slice(0, 20);
      } else {
        const response = await axios.get(`${API_BASE}/search`, {
          params: { 
            q: searchQuery, 
            type: searchFilters.nodeType || undefined,
            limit: 20 
          }
        });
        results = response.data;
      }
      showResults = true;
    } catch (error) {
      console.error('Search failed:', error);
    }
  }

  function handleSelect(node) {
    query = node.id;
    showResults = false;
    if (onNodeSelect) onNodeSelect(node);
    if (onSearch) onSearch(node);
  }

  // Performance: Cache unique node types to avoid recalculating on every render
  let uniqueTypes = [];
  $: uniqueTypes = (() => {
    if (!allNodes || allNodes.length === 0) return [];
    const types = new Set(allNodes.map(n => n.type).filter(Boolean));
    return Array.from(types).sort();
  })();
</script>

<div class="search-container">
  <div style="display: flex; gap: 5px;">
    <input
      type="text"
      placeholder="Search nodes..."
      id="searchbar-query-input"
      bind:value={query}
      on:focus={() => showResults = results.length > 0}
      class="search-input"
      style="flex: 1;"
    />
    <button
      type="button"
      class="bi bi-funnel icon-action"
      title="Toggle filters"
      on:click={() => (showFilters = !showFilters)}
      aria-label="Toggle filters"
    ></button>
  </div>

  {#if showFilters}
    <div class="search-filters" style="margin-top: 10px; padding: 10px; background: #333; border-radius: 4px;">
      <div style="margin-bottom: 10px;">
        <label for="searchbar-node-type" style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">
          Node Type
        </label>
        <select
          id="searchbar-node-type"
          bind:value={filters.nodeType}
          class="input-field"
          style="font-size: 12px;"
        >
          <option value="">All Types</option>
          {#each uniqueTypes as type}
            <option value={type}>{type}</option>
          {/each}
        </select>
      </div>

      <div>
        <label for="searchbar-has-prop" style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">
          Has Property
        </label>
        <div style="display: flex; gap: 5px;">
          <input
            type="text"
            placeholder="Property name"
            id="searchbar-has-prop"
            bind:value={filters.hasProperty}
            on:input={() => filters.propertyValue = ''}
            class="input-field"
            style="flex: 1; font-size: 12px;"
          />
          {#if filters.hasProperty}
            <input
              type="text"
              placeholder="Value (optional)"
              id="searchbar-prop-value"
              bind:value={filters.propertyValue}
              class="input-field"
              style="flex: 1; font-size: 12px;"
            />
          {/if}
        </div>
      </div>

      <button
        on:click={() => {
          filters = { nodeType: '', hasProperty: '', propertyValue: '' };
          query = '';
        }}
        class="btn-secondary"
        style="width: 100%; margin-top: 10px; font-size: 12px; padding: 5px;"
      >
        Clear Filters
      </button>
    </div>
  {/if}

  {#if showResults && results.length > 0}
    <div class="search-results">
      <div style="padding: 5px 10px; font-size: 11px; color: #888; border-bottom: 1px solid #444;">
        {results.length} result(s)
      </div>
      {#each results as node, idx}
        <button
          type="button"
          class="search-result-item"
          on:click={() => handleSelect(node)}
          style="width: 100%; text-align: left; background: none; border: none; cursor: pointer;"
        >
          <strong>{node.id}</strong>
          <span class="node-type-badge">{node.type}</span>
        </button>
      {/each}
    </div>
  {/if}

  {#if showResults && results.length === 0 && query.length > 2}
    <div class="search-results" style="padding: 10px; color: #888; font-size: 12px;">
      No results found
    </div>
  {/if}
</div>

