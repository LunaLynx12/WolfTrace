<script>
  import { onMount } from 'svelte';
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
        
        if (searchQuery) {
          const lowerQuery = searchQuery.toLowerCase();
          filtered = filtered.filter(node => {
            const idMatch = (node.id || '').toLowerCase().includes(lowerQuery);
            const propsMatch = Object.values(node).some(val => 
              typeof val === 'string' && val.toLowerCase().includes(lowerQuery)
            );
            return idMatch || propsMatch;
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

  function getUniqueNodeTypes() {
    if (!allNodes || allNodes.length === 0) return [];
    const types = new Set(allNodes.map(n => n.type).filter(Boolean));
    return Array.from(types).sort();
  }
</script>

<div class="search-container">
  <div style="display: flex; gap: 5px;">
    <input
      type="text"
      placeholder="Search nodes..."
      bind:value={query}
      on:focus={() => showResults = results.length > 0}
      class="search-input"
      style="flex: 1;"
    />
    <button
      on:click={() => showFilters = !showFilters}
      class="btn-secondary"
      style="padding: 8px 12px; font-size: 12px;"
      title="Toggle filters"
    >
      🔍
    </button>
  </div>

  {#if showFilters}
    <div class="search-filters" style="margin-top: 10px; padding: 10px; background: #333; border-radius: 4px;">
      <div style="margin-bottom: 10px;">
        <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">
          Node Type
        </label>
        <select
          bind:value={filters.nodeType}
          class="input-field"
          style="font-size: 12px;"
        >
          <option value="">All Types</option>
          {#each getUniqueNodeTypes() as type}
            <option value={type}>{type}</option>
          {/each}
        </select>
      </div>

      <div>
        <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">
          Has Property
        </label>
        <div style="display: flex; gap: 5px;">
          <input
            type="text"
            placeholder="Property name"
            bind:value={filters.hasProperty}
            on:input={() => filters.propertyValue = ''}
            class="input-field"
            style="flex: 1; font-size: 12px;"
          />
          {#if filters.hasProperty}
            <input
              type="text"
              placeholder="Value (optional)"
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
        <div
          class="search-result-item"
          on:click={() => handleSelect(node)}
        >
          <strong>{node.id}</strong>
          <span class="node-type-badge">{node.type}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if showResults && results.length === 0 && query.length > 2}
    <div class="search-results" style="padding: 10px; color: #888; font-size: 12px;">
      No results found
    </div>
  {/if}
</div>

