<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onLoadSession;
  export let currentGraphData;

  let sessions = [];
  let showSaveDialog = false;
  let sessionName = '';
  let sessionDescription = '';
  let loading = false;

  onMount(() => {
    loadSessions();
  });

  async function loadSessions() {
    try {
      const response = await axios.get(`${API_BASE}/sessions`);
      sessions = response.data;
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }

  async function saveSession() {
    if (!sessionName.trim()) {
      alert('Please enter a session name');
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
      
      alert('Session saved successfully!');
      showSaveDialog = false;
      sessionName = '';
      sessionDescription = '';
      loadSessions();
    } catch (error) {
      alert(`Failed to save session: ${error.response?.data?.error || error.message}`);
    } finally {
      loading = false;
    }
  }

  async function loadSession(sessionId) {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}/restore`);
      if (onLoadSession) onLoadSession();
    } catch (error) {
      alert(`Failed to load session: ${error.message}`);
    }
  }

  async function deleteSession(sessionId) {
    if (!window.confirm('Delete this session?')) return;
    try {
      await axios.delete(`${API_BASE}/sessions/${sessionId}`);
      loadSessions();
    } catch (error) {
      alert(`Failed to delete session: ${error.message}`);
    }
  }
</script>

<div class="session-manager">
  <div class="session-header">
    <h3>Session Manager</h3>
    <button on:click={() => showSaveDialog = !showSaveDialog} class="btn-primary" style="font-size: 12px; padding: 5px 10px;">
      Save Session
    </button>
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
        <button on:click={saveSession} disabled={loading} class="btn-primary" style="flex: 1;">
          {loading ? 'Saving...' : 'Save'}
        </button>
        <button on:click={() => showSaveDialog = false} class="btn-secondary" style="flex: 1;">
          Cancel
        </button>
      </div>
    </div>
  {/if}

  <div class="sessions-list">
    {#if sessions.length === 0}
      <p style="color: #888; font-size: 12px;">No saved sessions</p>
    {:else}
      {#each sessions as session}
        <div class="session-item">
          <div class="session-info" on:click={() => loadSession(session.id)}>
            <strong>{session.name}</strong>
            <small>{session.metadata?.node_count || 0} nodes, {session.metadata?.edge_count || 0} edges</small>
            {#if session.metadata?.description}
              <small style="display: block; margin-top: 2px;">{session.metadata.description}</small>
            {/if}
          </div>
          <button on:click={() => deleteSession(session.id)} class="btn-close" style="padding: 2px 6px; font-size: 10px;">
            ×
          </button>
        </div>
      {/each}
    {/if}
  </div>
</div>

