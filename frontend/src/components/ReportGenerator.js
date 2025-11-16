import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function ReportGenerator() {
  const [format, setFormat] = useState('html');
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      if (format === 'html') {
        const response = await axios.get(`${API_BASE}/report`, {
          params: { format: 'html', include_graph: 'false' },
          responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-report-${Date.now()}.html`;
        link.click();
        window.URL.revokeObjectURL(url);
      } else {
        const response = await axios.get(`${API_BASE}/report`, {
          params: { format: 'json', include_graph: 'false' }
        });
        
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-report-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
      }
      
      alert('Report generated successfully!');
    } catch (error) {
      alert(`Failed to generate report: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-generator">
      <h3>Generate Report</h3>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '15px' }}>
        Generate a comprehensive report of the current graph
      </p>

      <div className="report-section">
        <label>Format</label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="input-field"
        >
          <option value="html">HTML Report</option>
          <option value="json">JSON Report</option>
        </select>
      </div>

      <button
        onClick={generateReport}
        className="btn-primary"
        disabled={loading}
        style={{ width: '100%', marginTop: '10px' }}
      >
        {loading ? 'Generating...' : 'Generate Report'}
      </button>

      <p style={{ fontSize: '11px', color: '#666', marginTop: '10px' }}>
        Note: HTML reports can be printed to PDF using your browser's print function
      </p>
    </div>
  );
}

export default ReportGenerator;

