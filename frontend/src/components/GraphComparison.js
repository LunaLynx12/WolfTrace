import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function GraphComparison({ currentGraph, onLoadDiffGraph }) {
  const [session1, setSession1] = useState('');
  const [session2, setSession2] = useState('');
  const [graph1Data, setGraph1Data] = useState(null);
  const [graph2Data, setGraph2Data] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);

  React.useEffect(() => {
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

  const loadSession = async (sessionId, setter) => {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}`);
      setter({
        nodes: response.data.graph?.nodes || [],
        edges: response.data.graph?.edges || []
      });
    } catch (error) {
      alert(`Failed to load session: ${error.message}`);
    }
  };

  const compareGraphs = async () => {
    if (!graph1Data || !graph2Data) {
      alert('Please load both graphs to compare');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/compare`, {
        graph1: { nodes: graph1Data.nodes, edges: graph1Data.edges },
        graph2: { nodes: graph2Data.nodes, edges: graph2Data.edges }
      });
      setComparison(response.data);

      // Optionally load diff graph
      if (onLoadDiffGraph) {
        const diffResponse = await axios.post(`${API_BASE}/compare/diff-graph`, {
          graph1: { nodes: graph1Data.nodes, edges: graph1Data.edges },
          graph2: { nodes: graph2Data.nodes, edges: graph2Data.edges }
        });
        onLoadDiffGraph(diffResponse.data);
      }
    } catch (error) {
      alert(`Comparison failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const useCurrentGraph = (setter) => {
    setter({
      nodes: currentGraph.nodes || [],
      edges: currentGraph.links || []
    });
  };

  return (
    <div className="graph-comparison">
      <h3>Graph Comparison</h3>

      <div className="comparison-section">
        <div className="graph-selector">
          <h4>Graph 1</h4>
          <select
            value={session1}
            onChange={(e) => {
              setSession1(e.target.value);
              if (e.target.value) loadSession(e.target.value, setGraph1Data);
            }}
            className="input-field"
          >
            <option value="">Select session...</option>
            {sessions.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={() => useCurrentGraph(setGraph1Data)}
            className="btn-secondary"
            style={{ marginTop: '5px', fontSize: '12px' }}
          >
            Use Current Graph
          </button>
          {graph1Data && (
            <small style={{ display: 'block', marginTop: '5px', color: '#4CAF50' }}>
              Loaded: {graph1Data.nodes.length} nodes, {graph1Data.edges.length} edges
            </small>
          )}
        </div>

        <div className="graph-selector">
          <h4>Graph 2</h4>
          <select
            value={session2}
            onChange={(e) => {
              setSession2(e.target.value);
              if (e.target.value) loadSession(e.target.value, setGraph2Data);
            }}
            className="input-field"
          >
            <option value="">Select session...</option>
            {sessions.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={() => useCurrentGraph(setGraph2Data)}
            className="btn-secondary"
            style={{ marginTop: '5px', fontSize: '12px' }}
          >
            Use Current Graph
          </button>
          {graph2Data && (
            <small style={{ display: 'block', marginTop: '5px', color: '#4CAF50' }}>
              Loaded: {graph2Data.nodes.length} nodes, {graph2Data.edges.length} edges
            </small>
          )}
        </div>
      </div>

      <button
        onClick={compareGraphs}
        className="btn-primary"
        disabled={!graph1Data || !graph2Data || loading}
        style={{ width: '100%', marginTop: '15px' }}
      >
        {loading ? 'Comparing...' : 'Compare Graphs'}
      </button>

      {comparison && (
        <div className="comparison-results" style={{ marginTop: '20px' }}>
          <h4>Comparison Results</h4>
          
          <div className="stat-grid" style={{ marginTop: '10px' }}>
            <div className="stat-item">
              <div className="stat-label">Nodes Added</div>
              <div className="stat-value" style={{ color: '#4CAF50' }}>
                {comparison.stats?.nodes?.added || 0}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Nodes Removed</div>
              <div className="stat-value" style={{ color: '#f44336' }}>
                {comparison.stats?.nodes?.removed || 0}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Nodes Changed</div>
              <div className="stat-value" style={{ color: '#FF9800' }}>
                {comparison.stats?.nodes?.changed || 0}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Edges Added</div>
              <div className="stat-value" style={{ color: '#4CAF50' }}>
                {comparison.stats?.edges?.added || 0}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Edges Removed</div>
              <div className="stat-value" style={{ color: '#f44336' }}>
                {comparison.stats?.edges?.removed || 0}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Edges Changed</div>
              <div className="stat-value" style={{ color: '#FF9800' }}>
                {comparison.stats?.edges?.changed || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphComparison;

