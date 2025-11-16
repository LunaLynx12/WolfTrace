import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function AnalyticsPanel() {
  const [stats, setStats] = useState(null);
  const [communities, setCommunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const [statsRes, commRes] = await Promise.all([
        axios.get(`${API_BASE}/analytics/stats`),
        axios.get(`${API_BASE}/analytics/communities`)
      ]);
      setStats(statsRes.data);
      setCommunities(commRes.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="analytics-panel">Loading analytics...</div>;
  }

  if (!stats || stats.error) {
    return (
      <div className="analytics-panel">
        <p>No analytics data available</p>
        <button onClick={loadStats} className="btn-primary">Refresh</button>
      </div>
    );
  }

  return (
    <div className="analytics-panel">
      <div className="analytics-tabs">
        <button
          className={activeTab === 'stats' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
        <button
          className={activeTab === 'communities' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('communities')}
        >
          Communities
        </button>
      </div>

      {activeTab === 'stats' && (
        <div className="analytics-content">
          <div className="stat-section">
            <h3>Basic Metrics</h3>
            <div className="stat-grid">
              <div className="stat-item">
                <span className="stat-label">Nodes</span>
                <span className="stat-value">{stats.basic?.nodes || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Edges</span>
                <span className="stat-value">{stats.basic?.edges || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Avg Degree</span>
                <span className="stat-value">{stats.basic?.average_degree || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Components</span>
                <span className="stat-value">{stats.basic?.connected_components || 0}</span>
              </div>
            </div>
          </div>

          {stats.top_nodes_by_degree && stats.top_nodes_by_degree.length > 0 && (
            <div className="stat-section">
              <h3>Top Nodes by Degree</h3>
              <div className="top-nodes-list">
                {stats.top_nodes_by_degree.map((item, idx) => (
                  <div key={idx} className="top-node-item">
                    <span>{item.id}</span>
                    <span className="centrality-value">{item.centrality.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.node_types && (
            <div className="stat-section">
              <h3>Node Types</h3>
              <div className="type-distribution">
                {Object.entries(stats.node_types).map(([type, count]) => (
                  <div key={type} className="type-item">
                    <span>{type}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'communities' && (
        <div className="analytics-content">
          <h3>Detected Communities</h3>
          {communities.length > 0 ? (
            <div className="communities-list">
              {communities.map((comm) => (
                <div key={comm.id} className="community-item">
                  <div className="community-header">
                    <strong>Community {comm.id + 1}</strong>
                    <span>{comm.size} nodes</span>
                  </div>
                  {comm.nodes && (
                    <div className="community-nodes">
                      {comm.nodes.slice(0, 5).map((node, idx) => (
                        <span key={idx} className="community-node">{node}</span>
                      ))}
                      {comm.nodes.length > 5 && <span>...</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No communities detected</p>
          )}
        </div>
      )}
    </div>
  );
}

export default AnalyticsPanel;

