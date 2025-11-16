<script>
  export let active = false;
  export let onClick = undefined;
  export let title = '';
</script>

<button
  type="button"
  class="view-tab {active ? 'view-tab-active' : ''}"
  aria-pressed={active}
  aria-current={active ? 'page' : undefined}
  title={title}
  on:click={onClick}
>
  <slot />
  {#if active}
    <span class="sr-only">(current)</span>
  {/if}
</button>

<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>


