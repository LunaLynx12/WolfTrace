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
    <div class="header-title">
      <span class="title-icon">⚡</span>
      <span class="title-text">FILTERS</span>
    </div>
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
      {enabledTypes.size === nodeTypes.length ? "ALL" : "NONE"}
    </button>
  </div>
  
  <div class="filter-list">
    {#if nodeTypes.length === 0}
      <p class="no-types">NO TYPES</p>
    {:else}
      {#each nodeTypes as type}
        <label class="type-toggle" class:checked={enabledTypes.has(type)}>
          <input
            type="checkbox"
            checked={enabledTypes.has(type)}
            on:change={() => handleToggle(type)}
            class="type-checkbox"
          />
          <span class="type-label">{type.toUpperCase()}</span>
          <span class="type-count">
            {graphData?.nodes?.filter(n => (n.type || 'default') === type).length || 0}
          </span>
        </label>
      {/each}
    {/if}
  </div>
</div>

<style>
  .node-type-filter {
    display: flex;
    flex-direction: column;
    background: rgba(15, 20, 28, 0.95);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    max-height: 60vh;
  }

  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(0, 0, 0, 0.2);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .title-icon {
    font-size: 14px;
    opacity: 0.7;
  }

  .title-text {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: var(--brand);
    text-transform: uppercase;
    font-family: 'Courier New', 'Monaco', monospace;
  }

  .toggle-all-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-1);
    padding: 4px 10px;
    border-radius: 2px;
    cursor: pointer;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    transition: all 0.15s ease;
    font-family: 'Courier New', 'Monaco', monospace;
  }

  .toggle-all-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--brand);
    color: var(--brand);
  }

  .filter-list {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 4px 0;
    max-height: calc(60vh - 45px);
  }

  .type-toggle {
    display: flex;
    align-items: center;
    padding: 6px 12px;
    cursor: pointer;
    transition: background-color 0.1s ease;
    user-select: none;
    border-left: 2px solid transparent;
  }

  .type-toggle:hover {
    background: rgba(255, 255, 255, 0.05);
    border-left-color: var(--brand);
  }

  .type-toggle.checked {
    background: rgba(148, 137, 121, 0.1);
    border-left-color: var(--brand);
  }

  .type-checkbox {
    margin-right: 10px;
    cursor: pointer;
    width: 14px;
    height: 14px;
    accent-color: var(--brand);
    flex-shrink: 0;
  }

  .type-label {
    flex: 1;
    color: var(--text-1);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.3px;
    font-family: 'Courier New', 'Monaco', monospace;
  }

  .type-count {
    color: var(--text-2);
    font-size: 10px;
    font-weight: 600;
    margin-left: 8px;
    padding: 2px 6px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 2px;
    min-width: 24px;
    text-align: center;
    font-family: 'Courier New', 'Monaco', monospace;
  }

  .no-types {
    padding: 20px;
    color: var(--text-2);
    font-size: 11px;
    text-align: center;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: 'Courier New', 'Monaco', monospace;
  }

  /* Custom scrollbar for Bloodhound vibe */
  .filter-list::-webkit-scrollbar {
    width: 6px;
  }

  .filter-list::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
  }

  .filter-list::-webkit-scrollbar-thumb {
    background: rgba(148, 137, 121, 0.4);
    border-radius: 3px;
  }

  .filter-list::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 137, 121, 0.6);
  }
</style>

