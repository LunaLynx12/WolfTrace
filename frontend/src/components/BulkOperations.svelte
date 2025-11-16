<script>
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let selectedNodes;
  export let onOperationComplete;

  let operation = 'delete';
  let tags = '';
  let loading = false;

  async function handleBulkDelete() {
    if (!selectedNodes || selectedNodes.length === 0) {
      alert('Please select nodes first');
      return;
    }

    if (!window.confirm(`Delete ${selectedNodes.length} nodes?`)) {
      return;
    }

    loading = true;
    try {
      await axios.post(`${API_BASE}/bulk/nodes/delete`, {
        node_ids: selectedNodes
      });
      alert(`Successfully deleted ${selectedNodes.length} nodes`);
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      alert(`Failed: ${error.response?.data?.error || error.message}`);
    } finally {
      loading = false;
    }
  }

  async function handleBulkTag() {
    if (!selectedNodes || selectedNodes.length === 0) {
      alert('Please select nodes first');
      return;
    }

    const tagList = tags.split(',').map(t => t.trim()).filter(t => t);
    if (tagList.length === 0) {
      alert('Please enter at least one tag');
      return;
    }

    loading = true;
    try {
      await axios.post(`${API_BASE}/bulk/nodes/tag`, {
        node_ids: selectedNodes,
        tags: tagList
      });
      alert(`Tagged ${selectedNodes.length} nodes`);
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      alert(`Failed: ${error.response?.data?.error || error.message}`);
    } finally {
      loading = false;
    }
  }
</script>

<div class="bulk-operations">
  <h3>Bulk Operations</h3>
  
  {#if !selectedNodes || selectedNodes.length === 0}
    <p style="color: #888; font-size: 12px;">Select nodes (Ctrl+Click) to perform bulk operations</p>
  {:else}
    <p style="color: #4CAF50; font-size: 12px; margin-bottom: 15px;">
      {selectedNodes.length} node(s) selected
    </p>

    <div style="margin-bottom: 15px;">
      <label>Operation</label>
      <select bind:value={operation} class="input-field">
        <option value="delete">Delete Nodes</option>
        <option value="tag">Add Tags</option>
      </select>
    </div>

    {#if operation === 'tag'}
      <div style="margin-bottom: 15px;">
        <label>Tags (comma-separated)</label>
        <input
          type="text"
          placeholder="tag1, tag2, tag3"
          bind:value={tags}
          class="input-field"
        />
      </div>
    {/if}

    <button
      on:click={operation === 'delete' ? handleBulkDelete : handleBulkTag}
      disabled={loading || (operation === 'tag' && !tags.trim())}
      class={operation === 'delete' ? 'btn-danger' : 'btn-primary'}
      style="width: 100%;"
    >
      {loading ? 'Processing...' : (operation === 'delete' ? `Delete ${selectedNodes.length} Nodes` : 'Add Tags')}
    </button>
  {/if}
</div>

