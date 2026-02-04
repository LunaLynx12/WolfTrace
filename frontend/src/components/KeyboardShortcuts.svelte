<script>
  export let isOpen;
  export let onClose;
  import Button from './ui/Button.svelte';

  const shortcuts = [
    { keys: ['Ctrl', 'Z'], description: 'Undo last operation' },
    { keys: ['Ctrl', 'Y'], description: 'Redo last undone operation' },
    { keys: ['Ctrl', 'Shift', 'Z'], description: 'Redo (alternative)' },
    { keys: ['Ctrl', 'S'], description: 'Save session' },
    { keys: ['Esc'], description: 'Clear selection, focus mode, and highlights' },
    { keys: ['Ctrl', 'Click'], description: 'Multi-select nodes' },
    { keys: ['Click'], description: 'Select node / Center on node' },
    { keys: ['Scroll'], description: 'Zoom in/out' },
    { keys: ['Drag'], description: 'Pan graph' },
    { keys: ['↑'], description: 'Walk to neighbor (up)' },
    { keys: ['↓'], description: 'Walk to neighbor (down)' },
    { keys: ['←'], description: 'Walk to neighbor (left)' },
    { keys: ['→'], description: 'Walk to neighbor (right)' },
    { keys: ['Enter'], description: 'Focus: show selected node + 2-hop neighbors' },
    { keys: ['F'], description: 'Focus: show selected node + 2-hop neighbors' },
    { keys: ['E'], description: 'Expand 1 hop: show selected node + 1-hop neighbors' },
    { keys: ['P'], description: 'Paths to…: set source from selection, focus target input' },
  ];
</script>

{#if isOpen}
  <button
    type="button"
    class="shortcuts-modal-overlay"
    aria-label="Close shortcuts"
    on:click={onClose}
    style="all: unset"
  ></button>
  <div class="shortcuts-modal" role="dialog" aria-modal="true">
    <div class="shortcuts-header">
      <h2>Keyboard Shortcuts</h2>
      <Button variant="danger" size="sm" fullWidth={false} on:click={onClose} title="Close" style="padding: 4px 8px; min-width: auto;">
        ×
      </Button>
    </div>
    <div class="shortcuts-content">
      {#each shortcuts as shortcut}
        <div class="shortcut-item">
          <div class="shortcut-keys">
            {#each shortcut.keys as key, keyIdx}
              <kbd>{key}</kbd>
              {#if keyIdx < shortcut.keys.length - 1}
                <span> + </span>
              {/if}
            {/each}
          </div>
          <div class="shortcut-description">{shortcut.description}</div>
        </div>
      {/each}
    </div>
  </div>
{/if}

