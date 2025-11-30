<script>
  import { onMount, onDestroy } from 'svelte';
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onHistoryChange;

  let historyInfo = null;
  let loading = false;
  // Memory leak fix: Store interval reference for cleanup
  let historyInterval = null;

  onMount(() => {
    loadHistoryInfo();
    historyInterval = setInterval(loadHistoryInfo, 2000);
  });
  
  // Memory leak fix: Explicitly clean up interval on destroy
  onDestroy(() => {
    if (historyInterval) {
      clearInterval(historyInterval);
      historyInterval = null;
    }
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
        showNotification(`Undo failed: ${error.response?.data?.error || error.message}`, 'error');
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
        showNotification(`Redo failed: ${error.response?.data?.error || error.message}`, 'error');
      }
    } finally {
      loading = false;
    }
  }
</script>

<div style="display: flex; gap: 5px; align-items: center;">
  <Button
    disabled={!historyInfo?.can_undo || loading}
    title="Undo (Ctrl+Z)"
    style="flex: 1; padding: 8px 12px; margin: 0;"
    on:click={handleUndo}
  >
    ↶ Undo
  </Button>
  <Button
    disabled={!historyInfo?.can_redo || loading}
    title="Redo (Ctrl+Y)"
    style="flex: 1; padding: 8px 12px; margin: 0;"
    on:click={handleRedo}
  >
    ↷ Redo
  </Button>
</div>
{#if historyInfo}
  <small style="display: block; margin-top: 5px; color: var(--text-2); font-size: 11px;">
    {historyInfo.undo_count} undo, {historyInfo.redo_count} redo
  </small>
{/if}

<style>
  :global(.sidebar-section) :global(.uiv-btn.btn-primary) {
    padding: 8px 12px !important;
  }
</style>

