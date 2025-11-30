<script>
  export let graphData;
  export let onGroupChange;

  let groupBy = 'none';
  let customGroup = '';
  // Performance: Cache last grouping to avoid unnecessary recomputation
  let lastGroupingHash = '';

  $: if (groupBy !== 'none') {
    // Performance: Only recompute if grouping actually changed
    const hash = `${groupBy}-${customGroup}-${graphData?.nodes?.length || 0}`;
    if (hash !== lastGroupingHash) {
      lastGroupingHash = hash;
      handleGroupBy(groupBy);
    }
  } else {
    if (lastGroupingHash !== '') {
      lastGroupingHash = '';
      handleGroupBy('none');
    }
  }

  // Performance: Reuse groups object when possible to reduce memory allocation
  let cachedGroups = null;
  let cachedGroupType = null;
  
  function handleGroupBy(groupType) {
    if (groupType === 'none') {
      if (onGroupChange) onGroupChange(null);
      cachedGroups = null;
      cachedGroupType = null;
      return;
    }

    // Performance: Reuse groups object if grouping type hasn't changed
    // Only create new object if type changed or first time
    const groups = (cachedGroupType === groupType && cachedGroups) ? cachedGroups : {};
    
    // Clear groups if type changed
    if (cachedGroupType !== groupType) {
      Object.keys(groups).forEach(key => delete groups[key]);
      cachedGroupType = groupType;
    }
    
    graphData.nodes.forEach(node => {
      let groupKey = 'ungrouped';
      
      if (groupType === 'type') {
        groupKey = node.type || 'Unknown';
      } else if (groupType === 'firstLetter') {
        groupKey = (node.id || '').charAt(0).toUpperCase() || 'Other';
      } else if (groupType === 'custom' && customGroup) {
        groupKey = node[customGroup] || 'ungrouped';
      }
      
      // Performance: Reuse array if it exists
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(node.id);
    });
    
    // Cache for reuse
    cachedGroups = groups;

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

