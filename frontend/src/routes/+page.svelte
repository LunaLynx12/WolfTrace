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
  <div style="padding: 20px; text-align: center; color: #fff; background: #1a1a1a; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
    <div>
      <p>Loading WolfTrace...</p>
    </div>
  </div>
{/if}

