import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function NodeNotes({ node, onNoteUpdate }) {
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [notes, setNotes] = useState([]);

  useEffect(() => {
    if (node) {
      // Load existing notes from node properties or local storage
      const nodeNotes = node.notes || node._notes || [];
      setNotes(Array.isArray(nodeNotes) ? nodeNotes : []);
    }
  }, [node]);

  const saveNote = async () => {
    if (!note.trim() || !node) return;

    setSaving(true);
    try {
      const newNote = {
        id: Date.now(),
        text: note,
        timestamp: new Date().toISOString(),
        author: 'User' // Could be from auth context
      };

      const updatedNotes = [...notes, newNote];
      
      // Update node via bulk update API
      await axios.post(`${API_BASE}/bulk/nodes/update`, {
        updates: [{
          id: node.id,
          properties: {
            notes: updatedNotes,
            _notes: updatedNotes // Also store in _notes for compatibility
          }
        }]
      });

      setNotes(updatedNotes);
      setNote('');
      if (onNoteUpdate) onNoteUpdate(node.id, updatedNotes);
    } catch (error) {
      alert(`Failed to save note: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const deleteNote = async (noteId) => {
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

      setNotes(updatedNotes);
      if (onNoteUpdate) onNoteUpdate(node.id, updatedNotes);
    } catch (error) {
      alert(`Failed to delete note: ${error.message}`);
    }
  };

  if (!node) {
    return (
      <div className="node-notes" style={{ padding: '10px', color: '#888', fontSize: '12px' }}>
        Select a node to add notes
      </div>
    );
  }

  return (
    <div className="node-notes">
      <h4 style={{ fontSize: '14px', marginBottom: '10px' }}>Notes for {node.id}</h4>
      
      <div className="notes-list" style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '10px' }}>
        {notes.length === 0 ? (
          <div style={{ color: '#888', fontSize: '12px', fontStyle: 'italic' }}>No notes yet</div>
        ) : (
          notes.map((n) => (
            <div key={n.id} className="note-item" style={{ 
              background: '#333', 
              padding: '8px', 
              marginBottom: '5px', 
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              <div style={{ color: '#e0e0e0', marginBottom: '5px' }}>{n.text}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <small style={{ color: '#888', fontSize: '10px' }}>
                  {new Date(n.timestamp).toLocaleString()}
                </small>
                <button
                  onClick={() => deleteNote(n.id)}
                  className="btn-close"
                  style={{ padding: '2px 6px', fontSize: '10px' }}
                >
                  ×
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Add a note..."
        className="input-field"
        rows="3"
        style={{ resize: 'vertical', marginBottom: '5px' }}
      />
      <button
        onClick={saveNote}
        disabled={!note.trim() || saving}
        className="btn-primary"
        style={{ width: '100%', fontSize: '12px', padding: '8px' }}
      >
        {saving ? 'Saving...' : 'Add Note'}
      </button>
    </div>
  );
}

export default NodeNotes;

