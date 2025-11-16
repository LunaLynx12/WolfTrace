import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function GraphStatsWidget({ graphData, compact = false }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (graphData && graphData.nodes && graphData.nodes.length > 0) {
      loadStats();
    } else {
      setStats(null);
    }
  }, [graphData]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/analytics/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="graph-stats-widget" style={{ fontSize: '12px', color: '#888' }}>
        No graph data
      </div>
    );
  }

  if (compact) {
    return (
      <div className="graph-stats-widget compact">
        <div className="stat-mini">
          <span className="stat-label">Nodes:</span>
          <span className="stat-value">{graphData.nodes.length}</span>
        </div>
        <div className="stat-mini">
          <span className="stat-label">Edges:</span>
          <span className="stat-value">{graphData.links.length}</span>
        </div>
        {stats && stats.basic && (
          <>
            <div className="stat-mini">
              <span className="stat-label">Components:</span>
              <span className="stat-value">{stats.basic.connected_components || 0}</span>
            </div>
            <div className="stat-mini">
              <span className="stat-label">Avg Degree:</span>
              <span className="stat-value">{stats.basic.average_degree?.toFixed(1) || 0}</span>
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="graph-stats-widget">
      <h4 style={{ marginBottom: '10px', fontSize: '14px' }}>Graph Statistics</h4>
      {loading ? (
        <div style={{ color: '#888', fontSize: '12px' }}>Loading...</div>
      ) : (
        <>
          <div className="stat-grid-mini">
            <div className="stat-item-mini">
              <div className="stat-label">Nodes</div>
              <div className="stat-value">{graphData.nodes.length}</div>
            </div>
            <div className="stat-item-mini">
              <div className="stat-label">Edges</div>
              <div className="stat-value">{graphData.links.length}</div>
            </div>
            {stats && stats.basic && (
              <>
                <div className="stat-item-mini">
                  <div className="stat-label">Components</div>
                  <div className="stat-value">{stats.basic.connected_components || 0}</div>
                </div>
                <div className="stat-item-mini">
                  <div className="stat-label">Avg Degree</div>
                  <div className="stat-value">{stats.basic.average_degree?.toFixed(2) || 0}</div>
                </div>
              </>
            )}
          </div>
          {stats && stats.node_types && (
            <div style={{ marginTop: '10px' }}>
              <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '5px' }}>Node Types:</div>
              {Object.entries(stats.node_types).slice(0, 5).map(([type, count]) => (
                <div key={type} style={{ fontSize: '11px', color: '#888', marginBottom: '2px' }}>
                  {type}: {count}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default GraphStatsWidget;

