<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onHistoryChange;

  let historyInfo = null;
  let loading = false;

  onMount(() => {
    loadHistoryInfo();
    const interval = setInterval(loadHistoryInfo, 2000);
    return () => clearInterval(interval);
  });

  async function loadHistoryInfo() {
    try {
      const response = await axios.get(`${API_BASE}/history/info`);
      historyInfo = response.data;
    } catch (error) {
      console.error('Failed to load history info:', error);
    }
  }

  async function handleUndo() {
    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/history/undo`);
      historyInfo = response.data.history_info;
      if (onHistoryChange) {
        onHistoryChange(response.data.graph);
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        alert(`Undo failed: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      loading = false;
    }
  }

  async function handleRedo() {
    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/history/redo`);
      historyInfo = response.data.history_info;
      if (onHistoryChange) {
        onHistoryChange(response.data.graph);
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        alert(`Redo failed: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="history-controls">
  <div style="display: flex; gap: 5px; align-items: center;">
    <button
      on:click={handleUndo}
      disabled={!historyInfo?.can_undo || loading}
      class="btn-secondary"
      style="flex: 1; padding: 8px; font-size: 12px;"
      title="Undo (Ctrl+Z)"
    >
      ↶ Undo
    </button>
    <button
      on:click={handleRedo}
      disabled={!historyInfo?.can_redo || loading}
      class="btn-secondary"
      style="flex: 1; padding: 8px; font-size: 12px;"
      title="Redo (Ctrl+Y)"
    >
      ↷ Redo
    </button>
  </div>
  {#if historyInfo}
    <small style="display: block; margin-top: 5px; color: #888; font-size: 11px;">
      {historyInfo.undo_count} undo, {historyInfo.redo_count} redo
    </small>
  {/if}
</div>

