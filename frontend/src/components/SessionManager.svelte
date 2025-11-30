<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onLoadSession;
  export let currentGraphData;

  let sessions = [];
  let showSaveDialog = false;
  let sessionName = '';
  let sessionDescription = '';
  let loading = false;
  let sessionsLoaded = false;

  // Performance: Lazy load sessions only when component becomes visible
  async function loadSessions() {
    if (sessionsLoaded) return; // Already loaded
    
    try {
      const response = await axios.get(`${API_BASE}/sessions`);
      sessions = response.data;
      sessionsLoaded = true;
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }

  // Load sessions when component is first rendered (deferred)
  $: if (!sessionsLoaded && sessions.length === 0) {
    // Use requestIdleCallback or setTimeout to defer loading
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(() => loadSessions());
    } else {
      setTimeout(() => loadSessions(), 200);
    }
  }

  async function saveSession() {
    if (!sessionName.trim()) {
      showNotification('Please enter a session name', 'error');
      return;
    }

    loading = true;
    try {
      await axios.post(`${API_BASE}/sessions`, {
        name: sessionName,
        metadata: {
          description: sessionDescription,
          node_count: currentGraphData?.nodes?.length || 0,
          edge_count: currentGraphData?.links?.length || 0
        }
      });
      
      showNotification('Session saved successfully!', 'success');
      showSaveDialog = false;
      sessionName = '';
      sessionDescription = '';
      loadSessions();
    } catch (error) {
      showNotification(`Failed to save session: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  async function loadSession(sessionId) {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}/restore`);
      if (onLoadSession) onLoadSession();
      showNotification('Session loaded', 'success');
    } catch (error) {
      showNotification(`Failed to load session: ${error.message}`, 'error');
    }
  }

  async function deleteSession(sessionId) {
    if (!window.confirm('Delete this session?')) return;
    try {
      await axios.delete(`${API_BASE}/sessions/${sessionId}`);
      showNotification('Session deleted', 'success');
      loadSessions();
    } catch (error) {
      showNotification(`Failed to delete session: ${error.message}`, 'error');
    }
  }
</script>

<div class="session-manager">
  <div class="session-header">
    <h3>Session Manager</h3>
    <Button on:click={() => showSaveDialog = !showSaveDialog} style="font-size: 12px; padding: 5px 10px; width: auto;">
      Save Session
    </Button>
  </div>

  {#if showSaveDialog}
    <div class="save-dialog">
      <h4>Save Current Session</h4>
      <input
        type="text"
        placeholder="Session name"
        bind:value={sessionName}
        class="input-field"
      />
      <textarea
        placeholder="Description (optional)"
        bind:value={sessionDescription}
        class="input-field"
        rows="3"
      />
      <div style="display: flex; gap: 5px;">
        <Button on:click={saveSession} disabled={loading} style="flex: 1;">
          {loading ? 'Saving...' : 'Save'}
        </Button>
        <Button variant="secondary" on:click={() => showSaveDialog = false} style="flex: 1;">
          Cancel
        </Button>
      </div>
    </div>
  {/if}

  <div class="sessions-list">
    {#if sessions.length === 0}
      <p style="color: #888; font-size: 12px;">No saved sessions</p>
    {:else}
      {#each sessions as session}
        <div class="session-item">
          <button type="button" class="session-info" on:click={() => loadSession(session.id)} style="all: unset; display: block; cursor: pointer;">
            <strong>{session.name}</strong>
            <small>{session.metadata?.node_count || 0} nodes, {session.metadata?.edge_count || 0} edges</small>
            {#if session.metadata?.description}
              <small style="display: block; margin-top: 2px;">{session.metadata.description}</small>
            {/if}
          </button>
          <Button variant="close" on:click={() => deleteSession(session.id)} style="padding: 2px 6px; font-size: 10px; width: auto;">
            ×
          </Button>
        </div>
      {/each}
    {/if}
  </div>
</div>

