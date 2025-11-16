import React, { useState } from 'react';

function NodeGrouping({ graphData, onGroupChange }) {
  const [groupBy, setGroupBy] = useState('none');
  const [customGroup, setCustomGroup] = useState('');

  const handleGroupBy = (groupType) => {
    setGroupBy(groupType);
    
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
  };

  return (
    <div className="node-grouping">
      <h3>Node Grouping</h3>
      <select
        value={groupBy}
        onChange={(e) => {
          setGroupBy(e.target.value);
          handleGroupBy(e.target.value);
        }}
        className="input-field"
      >
        <option value="none">No Grouping</option>
        <option value="type">Group by Type</option>
        <option value="firstLetter">Group by First Letter</option>
        <option value="custom">Custom Property</option>
      </select>

      {groupBy === 'custom' && (
        <input
          type="text"
          placeholder="Property name (e.g., 'os', 'domain')"
          value={customGroup}
          onChange={(e) => {
            setCustomGroup(e.target.value);
            handleGroupBy('custom');
          }}
          className="input-field"
          style={{ marginTop: '10px' }}
        />
      )}

      {groupBy !== 'none' && (
        <div className="group-info" style={{ marginTop: '10px', fontSize: '12px', color: '#888' }}>
          Grouping active: {groupBy}
        </div>
      )}
    </div>
  );
}

export default NodeGrouping;

