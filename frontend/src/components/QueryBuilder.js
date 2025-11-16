import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function QueryBuilder({ onQueryResult }) {
  const [filters, setFilters] = useState({
    node_type: [],
    text_search: '',
    min_degree: '',
    max_degree: ''
  });
  const [queryResult, setQueryResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const executeQuery = async () => {
    setLoading(true);
    try {
      const queryFilters = {};
      
      if (filters.node_type.length > 0) {
        queryFilters.node_type = filters.node_type;
      }
      
      if (filters.text_search) {
        queryFilters.text_search = filters.text_search;
      }
      
      if (filters.min_degree || filters.max_degree) {
        if (filters.min_degree) queryFilters.min_degree = parseInt(filters.min_degree);
        if (filters.max_degree) queryFilters.max_degree = parseInt(filters.max_degree);
      }
      
      const response = await axios.post(`${API_BASE}/query`, queryFilters);
      setQueryResult(response.data);
      if (onQueryResult) {
        onQueryResult(response.data);
      }
    } catch (error) {
      alert(`Query failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleNodeType = (type) => {
    setFilters(prev => ({
      ...prev,
      node_type: prev.node_type.includes(type)
        ? prev.node_type.filter(t => t !== type)
        : [...prev.node_type, type]
    }));
  };

  return (
    <div className="query-builder">
      <h3>Advanced Query</h3>
      
      <div className="query-section">
        <label>Node Types</label>
        <div className="type-checkboxes">
          {['Entity', 'Host', 'User', 'Group', 'Computer', 'Resource', 'ec2'].map(type => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.node_type.includes(type)}
                onChange={() => toggleNodeType(type)}
              />
              {type}
            </label>
          ))}
        </div>
      </div>

      <div className="query-section">
        <label>Text Search</label>
        <input
          type="text"
          placeholder="Search in node properties..."
          value={filters.text_search}
          onChange={(e) => setFilters({ ...filters, text_search: e.target.value })}
          className="input-field"
        />
      </div>

      <div className="query-section">
        <label>Degree Range</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="number"
            placeholder="Min"
            value={filters.min_degree}
            onChange={(e) => setFilters({ ...filters, min_degree: e.target.value })}
            className="input-field"
            style={{ flex: 1 }}
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.max_degree}
            onChange={(e) => setFilters({ ...filters, max_degree: e.target.value })}
            className="input-field"
            style={{ flex: 1 }}
          />
        </div>
      </div>

      <button 
        onClick={executeQuery} 
        className="btn-primary"
        disabled={loading}
      >
        {loading ? 'Querying...' : 'Execute Query'}
      </button>

      {queryResult && (
        <div className="query-result">
          <strong>Results: {queryResult.count} nodes, {queryResult.edges?.length || 0} edges</strong>
          <button 
            onClick={() => {
              setQueryResult(null);
              if (onQueryResult) onQueryResult(null);
            }}
            className="btn-secondary"
            style={{ marginTop: '10px', fontSize: '12px' }}
          >
            Clear Filter
          </button>
        </div>
      )}
    </div>
  );
}

export default QueryBuilder;

