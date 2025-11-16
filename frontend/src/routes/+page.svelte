<script>
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import App from '../App.svelte';
  
  // Only render in browser to avoid SSR location errors
  let mounted = browser;
  
  onMount(() => {
    mounted = true;
  });
</script>

{#if browser && mounted}
  <App />
{:else}
  <div style="padding: 20px; text-align: center; color: var(--text-0); background: transparent; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
    <div class="graph-stats-widget" style="background: rgba(26, 32, 44, 0.7); backdrop-filter: blur(6px); border: 1px solid var(--border);">
      <p style="margin: 0;">Loading WolfTrace...</p>
    </div>
  </div>
{/if}

