<script>
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  let format = 'html';
  let loading = false;

  async function generateReport() {
    loading = true;
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
      
      showNotification('Report generated successfully!', 'success');
    } catch (error) {
      showNotification(`Failed to generate report: ${error.message}`, 'error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="report-generator">
  <h3>Generate Report</h3>
  
  <div style="margin-bottom: 15px;">
    <label for="report-format">Report Format</label>
    <select id="report-format" bind:value={format} class="input-field">
      <option value="html">HTML Report</option>
      <option value="json">JSON Report</option>
    </select>
  </div>

  <Button
    on:click={generateReport}
    disabled={loading}
  >
    {loading ? 'Generating...' : 'Generate Report'}
  </Button>

  <p style="margin-top: 15px; color: #888; font-size: 12px;">
    Reports include graph statistics, node/edge counts, and analytics data.
  </p>
</div>

