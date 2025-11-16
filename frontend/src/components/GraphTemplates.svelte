<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onTemplateApplied;

  let templates = [];
  let selectedTemplate = '';
  let variables = {};
  let loading = false;
  let templateDetails = null;

  onMount(() => {
    loadTemplates();
  });

  async function loadTemplates() {
    try {
      const response = await axios.get(`${API_BASE}/templates`);
      templates = response.data;
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  }

  async function loadTemplateDetails(templateId) {
    try {
      const response = await axios.get(`${API_BASE}/templates/${templateId}`);
      templateDetails = response.data;
      if (templateDetails.variables) {
        variables = {};
        templateDetails.variables.forEach(v => {
          variables[v] = '';
        });
      }
    } catch (error) {
      console.error('Failed to load template details:', error);
    }
  }

  async function applyTemplate() {
    if (!selectedTemplate) {
      alert('Please select a template');
      return;
    }

    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/templates/${selectedTemplate}/apply`, {
        variables: variables
      });
      
      alert(`Template applied: ${response.data.nodes_added} nodes, ${response.data.edges_added} edges added`);
      if (onTemplateApplied) onTemplateApplied();
      variables = {};
    } catch (error) {
      alert(`Failed to apply template: ${error.response?.data?.error || error.message}`);
    } finally {
      loading = false;
    }
  }
</script>

<div class="graph-templates">
  <h3>Graph Templates</h3>

  <div style="margin-bottom: 15px;">
    <label>Select Template</label>
    <select
      bind:value={selectedTemplate}
      on:change={() => loadTemplateDetails(selectedTemplate)}
      class="input-field"
    >
      <option value="">Choose a template...</option>
      {#each templates as template}
        <option value={template.id}>{template.name}</option>
      {/each}
    </select>
  </div>

  {#if templateDetails && templateDetails.variables && templateDetails.variables.length > 0}
    <div style="margin-bottom: 15px;">
      <label>Template Variables</label>
      {#each templateDetails.variables as varName}
        <input
          type="text"
          placeholder={varName}
          bind:value={variables[varName]}
          class="input-field"
          style="margin-bottom: 5px;"
        />
      {/each}
    </div>
  {/if}

  {#if templateDetails}
    <div style="margin-bottom: 15px; padding: 10px; background: #333; border-radius: 4px; font-size: 12px;">
      <strong>{templateDetails.name}</strong>
      {#if templateDetails.description}
        <p style="margin-top: 5px; color: #aaa;">{templateDetails.description}</p>
      {/if}
    </div>
  {/if}

  <button
    on:click={applyTemplate}
    disabled={!selectedTemplate || loading}
    class="btn-primary"
    style="width: 100%;"
  >
    {loading ? 'Applying...' : 'Apply Template'}
  </button>
</div>

