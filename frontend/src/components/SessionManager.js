import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function SessionManager({ onLoadSession, currentGraphData }) {
  const [sessions, setSessions] = useState([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [sessionDescription, setSessionDescription] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/sessions`);
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const saveSession = async () => {
    if (!sessionName.trim()) {
      alert('Please enter a session name');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/sessions`, {
        name: sessionName,
        metadata: {
          description: sessionDescription,
          node_count: currentGraphData?.nodes?.length || 0,
          edge_count: currentGraphData?.links?.length || 0
        }
      });
      
      alert('Session saved successfully!');
      setShowSaveDialog(false);
      setSessionName('');
      setSessionDescription('');
      loadSessions();
    } catch (error) {
      alert(`Failed to save session: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadSession = async (sessionId) => {
    if (!window.confirm('This will replace the current graph. Continue?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/sessions/${sessionId}/restore`);
      alert('Session loaded successfully!');
      if (onLoadSession) {
        onLoadSession();
      }
    } catch (error) {
      alert(`Failed to load session: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this session?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/sessions/${sessionId}`);
      loadSessions();
    } catch (error) {
      alert(`Failed to delete session: ${error.message}`);
    }
  };

  return (
    <div className="session-manager">
      <div className="session-header">
        <h3>Sessions</h3>
        <button 
          onClick={() => setShowSaveDialog(true)} 
          className="btn-primary"
          style={{ padding: '5px 10px', fontSize: '12px' }}
        >
          Save Current
        </button>
      </div>

      {showSaveDialog && (
        <div className="save-dialog">
          <h4>Save Session</h4>
          <input
            type="text"
            placeholder="Session name"
            value={sessionName}
            onChange={(e) => setSessionName(e.target.value)}
            className="input-field"
          />
          <textarea
            placeholder="Description (optional)"
            value={sessionDescription}
            onChange={(e) => setSessionDescription(e.target.value)}
            className="input-field"
            rows="3"
          />
          <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
            <button onClick={saveSession} className="btn-primary" disabled={loading}>
              Save
            </button>
            <button 
              onClick={() => {
                setShowSaveDialog(false);
                setSessionName('');
                setSessionDescription('');
              }} 
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <p style={{ color: '#888', fontSize: '12px' }}>No saved sessions</p>
        ) : (
          sessions.map((session) => (
            <div 
              key={session.id} 
              className="session-item"
              onClick={() => loadSession(session.id)}
            >
              <div className="session-info">
                <strong>{session.name}</strong>
                <small>{new Date(session.created_at).toLocaleDateString()}</small>
                {session.node_count !== undefined && (
                  <small>{session.node_count} nodes, {session.edge_count} edges</small>
                )}
              </div>
              <button
                onClick={(e) => deleteSession(session.id, e)}
                className="btn-close"
                style={{ padding: '2px 6px', fontSize: '10px' }}
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default SessionManager;

