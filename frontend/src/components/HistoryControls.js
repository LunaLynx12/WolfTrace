import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function HistoryControls({ onHistoryChange }) {
  const [historyInfo, setHistoryInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHistoryInfo();
  }, []);

  const loadHistoryInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE}/history/info`);
      setHistoryInfo(response.data);
    } catch (error) {
      console.error('Failed to load history info:', error);
    }
  };

  const handleUndo = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/history/undo`);
      setHistoryInfo(response.data.history_info);
      if (onHistoryChange) {
        onHistoryChange(response.data.graph);
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        alert(`Undo failed: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRedo = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/history/redo`);
      setHistoryInfo(response.data.history_info);
      if (onHistoryChange) {
        onHistoryChange(response.data.graph);
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        alert(`Redo failed: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // Refresh history info periodically
  useEffect(() => {
    const interval = setInterval(loadHistoryInfo, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="history-controls">
      <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
        <button
          onClick={handleUndo}
          disabled={!historyInfo?.can_undo || loading}
          className="btn-secondary"
          style={{ flex: 1, padding: '8px', fontSize: '12px' }}
          title="Undo (Ctrl+Z)"
        >
          ↶ Undo
        </button>
        <button
          onClick={handleRedo}
          disabled={!historyInfo?.can_redo || loading}
          className="btn-secondary"
          style={{ flex: 1, padding: '8px', fontSize: '12px' }}
          title="Redo (Ctrl+Y)"
        >
          ↷ Redo
        </button>
      </div>
      {historyInfo && (
        <small style={{ display: 'block', marginTop: '5px', color: '#888', fontSize: '11px' }}>
          {historyInfo.undo_count} undo, {historyInfo.redo_count} redo
        </small>
      )}
    </div>
  );
}

export default HistoryControls;

