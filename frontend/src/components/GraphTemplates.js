import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function GraphTemplates({ onTemplateApplied }) {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [variables, setVariables] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const applyTemplate = async () => {
    if (!selectedTemplate) {
      alert('Please select a template');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/templates/${selectedTemplate}/apply`, {
        variables: variables
      });
      
      alert(`Template applied: ${response.data.nodes_added} nodes, ${response.data.edges_added} edges added`);
      if (onTemplateApplied) onTemplateApplied();
      setVariables({});
    } catch (error) {
      alert(`Failed to apply template: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplateDetails = async (templateId) => {
    try {
      const response = await axios.get(`${API_BASE}/templates/${templateId}`);
      const template = response.data;
      
      // Extract variables from template
      const templateVars = {};
      // Simple extraction - look for {variable} patterns
      const templateStr = JSON.stringify(template);
      const matches = templateStr.match(/\{(\w+)\}/g);
      if (matches) {
        matches.forEach(match => {
          const varName = match.replace(/[{}]/g, '');
          if (!templateVars[varName]) {
            templateVars[varName] = '';
          }
        });
      }
      setVariables(templateVars);
    } catch (error) {
      console.error('Failed to load template details:', error);
    }
  };

  return (
    <div className="graph-templates">
      <h3>Graph Templates</h3>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '15px' }}>
        Apply predefined graph structures
      </p>

      <div className="template-section">
        <label>Select Template</label>
        <select
          value={selectedTemplate}
          onChange={(e) => {
            setSelectedTemplate(e.target.value);
            if (e.target.value) loadTemplateDetails(e.target.value);
          }}
          className="input-field"
        >
          <option value="">Choose a template...</option>
          {templates.map(t => (
            <option key={t.id} value={t.id}>
              {t.name} ({t.node_count} nodes, {t.edge_count} edges)
            </option>
          ))}
        </select>
      </div>

      {selectedTemplate && Object.keys(variables).length > 0 && (
        <div className="template-variables" style={{ marginTop: '15px' }}>
          <label>Template Variables</label>
          {Object.keys(variables).map(varName => (
            <input
              key={varName}
              type="text"
              placeholder={varName}
              value={variables[varName] || ''}
              onChange={(e) => setVariables({ ...variables, [varName]: e.target.value })}
              className="input-field"
              style={{ marginTop: '5px' }}
            />
          ))}
        </div>
      )}

      {templates.length === 0 && (
        <p style={{ fontSize: '12px', color: '#888', marginTop: '10px' }}>
          No templates available. Create templates in data/templates/
        </p>
      )}

      <button
        onClick={applyTemplate}
        className="btn-primary"
        disabled={loading || !selectedTemplate}
        style={{ width: '100%', marginTop: '15px' }}
      >
        {loading ? 'Applying...' : 'Apply Template'}
      </button>
    </div>
  );
}

export default GraphTemplates;

