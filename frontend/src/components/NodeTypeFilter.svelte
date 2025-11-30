<script>
  export let graphData = { nodes: [], links: [] };
  export let enabledTypes = new Set();
  export let onToggleType;

  // Extract unique node types from graph data
  $: nodeTypes = graphData?.nodes 
    ? [...new Set(graphData.nodes.map(n => n.type || 'default').filter(Boolean))]
        .sort()
    : [];

  function handleToggle(type) {
    if (onToggleType) {
      onToggleType(type);
    }
  }
</script>

<div class="node-type-filter">
  <div class="filter-header">
    <h3>Node Types</h3>
    <button
      type="button"
      class="toggle-all-btn"
      on:click={() => {
        if (enabledTypes.size === nodeTypes.length) {
          // Disable all
          nodeTypes.forEach(type => {
            if (enabledTypes.has(type)) handleToggle(type);
          });
        } else {
          // Enable all
          nodeTypes.forEach(type => {
            if (!enabledTypes.has(type)) handleToggle(type);
          });
        }
      }}
      title={enabledTypes.size === nodeTypes.length ? "Disable all" : "Enable all"}
    >
      {enabledTypes.size === nodeTypes.length ? "All" : "None"}
    </button>
  </div>
  
  <div class="filter-list">
    {#if nodeTypes.length === 0}
      <p class="no-types">No node types found</p>
    {:else}
      {#each nodeTypes as type}
        <label class="type-toggle">
          <input
            type="checkbox"
            checked={enabledTypes.has(type)}
            on:change={() => handleToggle(type)}
          />
          <span class="type-label">{type}</span>
          <span class="type-count">
            ({graphData?.nodes?.filter(n => (n.type || 'default') === type).length || 0})
          </span>
        </label>
      {/each}
    {/if}
  </div>
</div>

<style>
  .node-type-filter {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-overlay-1);
    backdrop-filter: blur(10px);
    border-left: 1px solid var(--border);
  }

  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-2);
    border-bottom: 1px solid var(--border);
  }

  .filter-header h3 {
    margin: 0;
    font-size: 16px;
    color: var(--brand);
  }

  .toggle-all-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-1);
    padding: 4px 12px;
    border-radius: var(--radius-1);
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s ease;
  }

  .toggle-all-btn:hover {
    background: var(--bg-overlay-2);
    border-color: var(--border-hover);
  }

  .filter-list {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-1);
  }

  .type-toggle {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    margin-bottom: 4px;
    border-radius: var(--radius-1);
    cursor: pointer;
    transition: background-color 0.15s ease;
    user-select: none;
  }

  .type-toggle:hover {
    background: var(--bg-overlay-2);
  }

  .type-toggle input[type="checkbox"] {
    margin-right: 10px;
    cursor: pointer;
    width: 16px;
    height: 16px;
    accent-color: var(--brand);
  }

  .type-label {
    flex: 1;
    color: var(--text-1);
    font-size: 13px;
  }

  .type-count {
    color: var(--text-2);
    font-size: 11px;
    margin-left: 8px;
  }

  .no-types {
    padding: var(--space-2);
    color: var(--text-2);
    font-size: 13px;
    text-align: center;
    margin: 0;
  }
</style>

