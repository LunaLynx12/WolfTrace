<script>
  export let graphData;
  export let onGroupChange;

  let groupBy = 'none';
  let customGroup = '';

  $: if (groupBy !== 'none') {
    handleGroupBy(groupBy);
  }

  function handleGroupBy(groupType) {
    if (groupType === 'none') {
      if (onGroupChange) onGroupChange(null);
      return;
    }

    const groups = {};
    
    graphData.nodes.forEach(node => {
      let groupKey = 'ungrouped';
      
      if (groupType === 'type') {
        groupKey = node.type || 'Unknown';
      } else if (groupType === 'firstLetter') {
        groupKey = (node.id || '').charAt(0).toUpperCase() || 'Other';
      } else if (groupType === 'custom' && customGroup) {
        groupKey = node[customGroup] || 'ungrouped';
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(node.id);
    });

    if (onGroupChange) {
      onGroupChange({
        type: groupType,
        groups: groups,
        groupCount: Object.keys(groups).length
      });
    }
  }
</script>

<div class="node-grouping">
  <h3>Node Grouping</h3>
  <select
    bind:value={groupBy}
    on:change={() => handleGroupBy(groupBy)}
    class="input-field"
  >
    <option value="none">No Grouping</option>
    <option value="type">Group by Type</option>
    <option value="firstLetter">Group by First Letter</option>
    <option value="custom">Custom Property</option>
  </select>

  {#if groupBy === 'custom'}
    <input
      type="text"
      placeholder="Property name (e.g., 'os', 'domain')"
      bind:value={customGroup}
      on:input={() => handleGroupBy('custom')}
      class="input-field"
      style="margin-top: 10px;"
    />
  {/if}

  {#if groupBy !== 'none'}
    <div class="group-info" style="margin-top: 10px; font-size: 12px; color: #888;">
      Grouping active: {groupBy}
    </div>
  {/if}
</div>

