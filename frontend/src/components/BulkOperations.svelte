<script>
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let selectedNodes;
  export let onOperationComplete;

  let operation = 'delete';
  let tags = '';
  let loading = false;

  async function handleBulkDelete() {
    if (!selectedNodes || selectedNodes.length === 0) {
      showNotification('Please select nodes first', 'error');
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
      showNotification(`Successfully deleted ${selectedNodes.length} nodes`, 'success');
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      showNotification(`Failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  async function handleBulkTag() {
    if (!selectedNodes || selectedNodes.length === 0) {
      showNotification('Please select nodes first', 'error');
      return;
    }

    const tagList = tags.split(',').map(t => t.trim()).filter(t => t);
    if (tagList.length === 0) {
      showNotification('Please enter at least one tag', 'error');
      return;
    }

    loading = true;
    try {
      await axios.post(`${API_BASE}/bulk/nodes/tag`, {
        node_ids: selectedNodes,
        tags: tagList
      });
      showNotification(`Tagged ${selectedNodes.length} nodes`, 'success');
      if (onOperationComplete) onOperationComplete();
    } catch (error) {
      showNotification(`Failed: ${error.response?.data?.error || error.message}`, 'error');
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
      <label for="bulkop-operation">Operation</label>
      <select id="bulkop-operation" bind:value={operation} class="input-field">
        <option value="delete">Delete Nodes</option>
        <option value="tag">Add Tags</option>
      </select>
    </div>

    {#if operation === 'tag'}
      <div style="margin-bottom: 15px;">
        <label for="bulkop-tags">Tags (comma-separated)</label>
        <input
          type="text"
          placeholder="tag1, tag2, tag3"
          id="bulkop-tags"
          bind:value={tags}
          class="input-field"
        />
      </div>
    {/if}

    <Button
      on:click={operation === 'delete' ? handleBulkDelete : handleBulkTag}
      disabled={loading || (operation === 'tag' && !tags.trim())}
      variant={operation === 'delete' ? 'danger' : 'primary'}
    >
      {loading ? 'Processing...' : (operation === 'delete' ? `Delete ${selectedNodes.length} Nodes` : 'Add Tags')}
    </Button>
  {/if}
</div>

