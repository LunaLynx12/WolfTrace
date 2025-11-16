<script>
  export let isOpen;
  export let onClose;

  const shortcuts = [
    { keys: ['Ctrl', 'Z'], description: 'Undo last operation' },
    { keys: ['Ctrl', 'Y'], description: 'Redo last undone operation' },
    { keys: ['Ctrl', 'Shift', 'Z'], description: 'Redo (alternative)' },
    { keys: ['Ctrl', 'S'], description: 'Save session' },
    { keys: ['Esc'], description: 'Clear selection and highlights' },
    { keys: ['Ctrl', 'Click'], description: 'Multi-select nodes' },
    { keys: ['Click'], description: 'Select node / Center on node' },
    { keys: ['Scroll'], description: 'Zoom in/out' },
    { keys: ['Drag'], description: 'Pan graph' },
  ];
</script>

{#if isOpen}
  <div class="shortcuts-modal-overlay" on:click={onClose} on:keydown={(e) => e.key === 'Escape' && onClose()}>
    <div class="shortcuts-modal" on:click|stopPropagation>
      <div class="shortcuts-header">
        <h2>Keyboard Shortcuts</h2>
        <button on:click={onClose} class="btn-close" style="padding: 5px 10px;">
          ×
        </button>
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
      <div class="shortcuts-footer">
        <button on:click={onClose} class="btn-primary">
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

