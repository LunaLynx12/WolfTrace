<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let node;
  export let onNoteUpdate;

  let note = '';
  let saving = false;
  let notes = [];

  $: if (node) {
    const nodeNotes = node.notes || node._notes || [];
    notes = Array.isArray(nodeNotes) ? nodeNotes : [];
  }

  async function saveNote() {
    if (!note.trim() || !node) return;

    saving = true;
    try {
      const newNote = {
        id: Date.now(),
        text: note,
        timestamp: new Date().toISOString(),
        author: 'User'
      };

      const updatedNotes = [...notes, newNote];
      
      await axios.post(`${API_BASE}/bulk/nodes/update`, {
        updates: [{
          id: node.id,
          properties: {
            notes: updatedNotes,
            _notes: updatedNotes
          }
        }]
      });

      notes = updatedNotes;
      note = '';
      if (onNoteUpdate) onNoteUpdate(node.id, updatedNotes);
    } catch (error) {
      alert(`Failed to save note: ${error.message}`);
    } finally {
      saving = false;
    }
  }

  async function deleteNote(noteId) {
    if (!node) return;

    try {
      const updatedNotes = notes.filter(n => n.id !== noteId);
      
      await axios.post(`${API_BASE}/bulk/nodes/update`, {
        updates: [{
          id: node.id,
          properties: {
            notes: updatedNotes,
            _notes: updatedNotes
          }
        }]
      });

      notes = updatedNotes;
      if (onNoteUpdate) onNoteUpdate(node.id, updatedNotes);
    } catch (error) {
      alert(`Failed to delete note: ${error.message}`);
    }
  }
</script>

{#if !node}
  <div class="node-notes" style="padding: 10px; color: #888; font-size: 12px;">
    Select a node to add notes
  </div>
{:else}
  <div class="node-notes">
    <h4 style="font-size: 14px; margin-bottom: 10px;">Notes for {node.id}</h4>
    
    <div class="notes-list" style="max-height: 200px; overflow-y: auto; margin-bottom: 10px;">
      {#if notes.length === 0}
        <div style="color: #888; font-size: 12px; font-style: italic;">No notes yet</div>
      {:else}
        {#each notes as n}
          <div class="note-item" style="background: #333; padding: 8px; margin-bottom: 5px; border-radius: 4px; font-size: 12px;">
            <div style="color: #e0e0e0; margin-bottom: 5px;">{n.text}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <small style="color: #888; font-size: 10px;">
                {new Date(n.timestamp).toLocaleString()}
              </small>
              <button
                on:click={() => deleteNote(n.id)}
                class="btn-close"
                style="padding: 2px 6px; font-size: 10px;"
              >
                ×
              </button>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <textarea
      bind:value={note}
      placeholder="Add a note..."
      class="input-field"
      rows="3"
      style="resize: vertical; margin-bottom: 5px;"
    />
    <button
      on:click={saveNote}
      disabled={!note.trim() || saving}
      class="btn-primary"
      style="width: 100%; font-size: 12px; padding: 8px;"
    >
      {saving ? 'Saving...' : 'Add Note'}
    </button>
  </div>
{/if}

