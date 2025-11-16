import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function SearchBar({ onNodeSelect, onSearch, allNodes }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [filters, setFilters] = useState({
    nodeType: '',
    hasProperty: '',
    propertyValue: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (query.length > 2 || filters.nodeType || filters.hasProperty) {
      const timeoutId = setTimeout(() => {
        searchNodes(query, filters);
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setResults([]);
    }
  }, [query, filters]);

  const searchNodes = async (searchQuery, searchFilters) => {
    try {
      // Use local search if allNodes provided, otherwise use API
      if (allNodes && allNodes.length > 0) {
        let filtered = allNodes;
        
        // Text search
        if (searchQuery) {
          const lowerQuery = searchQuery.toLowerCase();
          filtered = filtered.filter(node => {
            const idMatch = (node.id || '').toLowerCase().includes(lowerQuery);
            const propsMatch = Object.values(node).some(val => 
              typeof val === 'string' && val.toLowerCase().includes(lowerQuery)
            );
            return idMatch || propsMatch;
          });
        }
        
        // Type filter
        if (searchFilters.nodeType) {
          filtered = filtered.filter(node => node.type === searchFilters.nodeType);
        }
        
        // Property filter
        if (searchFilters.hasProperty) {
          filtered = filtered.filter(node => {
            if (searchFilters.propertyValue) {
              return node[searchFilters.hasProperty] === searchFilters.propertyValue;
            }
            return searchFilters.hasProperty in node;
          });
        }
        
        setResults(filtered.slice(0, 20));
      } else {
        const response = await axios.get(`${API_BASE}/search`, {
          params: { 
            q: searchQuery, 
            type: searchFilters.nodeType || undefined,
            limit: 20 
          }
        });
        setResults(response.data);
      }
      setShowResults(true);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleSelect = (node) => {
    setQuery(node.id);
    setShowResults(false);
    if (onNodeSelect) onNodeSelect(node);
    if (onSearch) onSearch(node);
  };

  const getUniqueNodeTypes = () => {
    if (!allNodes || allNodes.length === 0) return [];
    const types = new Set(allNodes.map(n => n.type).filter(Boolean));
    return Array.from(types).sort();
  };

  return (
    <div className="search-container">
      <div style={{ display: 'flex', gap: '5px' }}>
        <input
          type="text"
          placeholder="Search nodes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowResults(results.length > 0)}
          className="search-input"
          style={{ flex: 1 }}
        />
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="btn-secondary"
          style={{ padding: '8px 12px', fontSize: '12px' }}
          title="Toggle filters"
        >
          🔍
        </button>
      </div>

      {showFilters && (
        <div className="search-filters" style={{ marginTop: '10px', padding: '10px', background: '#333', borderRadius: '4px' }}>
          <div style={{ marginBottom: '10px' }}>
            <label style={{ fontSize: '12px', color: '#aaa', display: 'block', marginBottom: '5px' }}>
              Node Type
            </label>
            <select
              value={filters.nodeType}
              onChange={(e) => setFilters({ ...filters, nodeType: e.target.value })}
              className="input-field"
              style={{ fontSize: '12px' }}
            >
              <option value="">All Types</option>
              {getUniqueNodeTypes().map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: '#aaa', display: 'block', marginBottom: '5px' }}>
              Has Property
            </label>
            <div style={{ display: 'flex', gap: '5px' }}>
              <input
                type="text"
                placeholder="Property name"
                value={filters.hasProperty}
                onChange={(e) => setFilters({ ...filters, hasProperty: e.target.value, propertyValue: '' })}
                className="input-field"
                style={{ flex: 1, fontSize: '12px' }}
              />
              {filters.hasProperty && (
                <input
                  type="text"
                  placeholder="Value (optional)"
                  value={filters.propertyValue}
                  onChange={(e) => setFilters({ ...filters, propertyValue: e.target.value })}
                  className="input-field"
                  style={{ flex: 1, fontSize: '12px' }}
                />
              )}
            </div>
          </div>

          <button
            onClick={() => {
              setFilters({ nodeType: '', hasProperty: '', propertyValue: '' });
              setQuery('');
            }}
            className="btn-secondary"
            style={{ width: '100%', marginTop: '10px', fontSize: '12px', padding: '5px' }}
          >
            Clear Filters
          </button>
        </div>
      )}

      {showResults && results.length > 0 && (
        <div className="search-results">
          <div style={{ padding: '5px 10px', fontSize: '11px', color: '#888', borderBottom: '1px solid #444' }}>
            {results.length} result(s)
          </div>
          {results.map((node, idx) => (
            <div
              key={idx}
              className="search-result-item"
              onClick={() => handleSelect(node)}
            >
              <strong>{node.id}</strong>
              <span className="node-type-badge">{node.type}</span>
            </div>
          ))}
        </div>
      )}

      {showResults && results.length === 0 && query.length > 2 && (
        <div className="search-results" style={{ padding: '10px', color: '#888', fontSize: '12px' }}>
          No results found
        </div>
      )}
    </div>
  );
}

export default SearchBar;


