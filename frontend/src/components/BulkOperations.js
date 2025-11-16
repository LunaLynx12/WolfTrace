import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function BulkOperations({ selectedNodes, onOperationComplete }) {
  const [operation, setOperation] = useState('delete');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);

  const handleBulkDelete = async () => {
    if (!selectedNodes || selectedNodes.length === 0) {
      alert('Please select nodes first');
      return;
    }

    if (!window.confirm(`Delete ${selectedNodes.length} nodes?`)) {
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE}/bulk/nodes/delete`, {
        node_ids: selectedNodes
      });
      alert(`Successfully deleted ${selectedNodes.length} nodes`);
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      alert(`Failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkTag = async () => {
    if (!selectedNodes || selectedNodes.length === 0) {
      alert('Please select nodes first');
      return;
    }

    const tagList = tags.split(',').map(t => t.trim()).filter(t => t);
    if (tagList.length === 0) {
      alert('Please enter at least one tag');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE}/bulk/nodes/tag`, {
        node_ids: selectedNodes,
        tags: tagList,
        operation: 'add'
      });
      alert(`Successfully tagged ${selectedNodes.length} nodes`);
      setTags('');
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      alert(`Failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkExport = async () => {
    if (!selectedNodes || selectedNodes.length === 0) {
      alert('Please select nodes first');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/bulk/nodes/export`, {
        node_ids: selectedNodes
      });
      
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `bulk-export-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(`Failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bulk-operations">
      <h3>Bulk Operations</h3>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '15px' }}>
        {selectedNodes?.length || 0} node(s) selected
      </p>

      <div className="bulk-section">
        <label>Operation</label>
        <select
          value={operation}
          onChange={(e) => setOperation(e.target.value)}
          className="input-field"
        >
          <option value="delete">Delete Nodes</option>
          <option value="tag">Tag Nodes</option>
          <option value="export">Export Nodes</option>
        </select>
      </div>

      {operation === 'tag' && (
        <div className="bulk-section">
          <label>Tags (comma-separated)</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="tag1, tag2, tag3"
            className="input-field"
          />
        </div>
      )}

      <button
        onClick={
          operation === 'delete' ? handleBulkDelete :
          operation === 'tag' ? handleBulkTag :
          handleBulkExport
        }
        className="btn-primary"
        disabled={loading || !selectedNodes || selectedNodes.length === 0}
        style={{ width: '100%', marginTop: '10px' }}
      >
        {loading ? 'Processing...' : 
         operation === 'delete' ? 'Delete Selected' :
         operation === 'tag' ? 'Tag Selected' :
         'Export Selected'}
      </button>
    </div>
  );
}

export default BulkOperations;

