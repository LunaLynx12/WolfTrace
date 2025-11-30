<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let onTemplateApplied;

  let templates = [];
  let selectedTemplate = '';
  let variables = {};
  let loading = false;
  let templateDetails = null;
  let templatesLoaded = false;

  // Performance: Lazy load templates only when component becomes visible
  async function loadTemplates() {
    if (templatesLoaded) return; // Already loaded
    
    try {
      const response = await axios.get(`${API_BASE}/templates`);
      templates = response.data;
      templatesLoaded = true;
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  }

  // Load templates when component is first rendered (deferred)
  $: if (!templatesLoaded && templates.length === 0) {
    // Use requestIdleCallback or setTimeout to defer loading
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(() => loadTemplates());
    } else {
      setTimeout(() => loadTemplates(), 200);
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
      showNotification('Please select a template', 'error');
      return;
    }

    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/templates/${selectedTemplate}/apply`, {
        variables: variables
      });
      
      showNotification(`Template applied: ${response.data.nodes_added} nodes, ${response.data.edges_added} edges added`, 'success');
      if (onTemplateApplied) onTemplateApplied();
      variables = {};
    } catch (error) {
      showNotification(`Failed to apply template: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="graph-templates">
  <h3>Graph Templates</h3>

  <div style="margin-bottom: 15px;">
    <label for="gt-select-template">Select Template</label>
    <select
      id="gt-select-template"
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
    <fieldset style="border: none; padding: 0; margin: 0 0 15px 0;">
      <legend>Template Variables</legend>
      {#each templateDetails.variables as varName}
        <input
          type="text"
          placeholder={varName}
          bind:value={variables[varName]}
          class="input-field"
          style="margin-bottom: 5px;"
        />
      {/each}
    </fieldset>
  {/if}

  {#if templateDetails}
    <div style="margin-bottom: 15px; padding: 10px; background: #333; border-radius: 4px; font-size: 12px;">
      <strong>{templateDetails.name}</strong>
      {#if templateDetails.description}
        <p style="margin-top: 5px; color: #aaa;">{templateDetails.description}</p>
      {/if}
    </div>
  {/if}

  <Button
    on:click={applyTemplate}
    disabled={!selectedTemplate || loading}
  >
    {loading ? 'Applying...' : 'Apply Template'}
  </Button>
</div>

