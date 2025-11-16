<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  export let variant = 'primary'; // 'primary' | 'secondary' | 'danger' | 'export' | 'close'
  export let size = 'md'; // 'sm' | 'md'
  export let type = 'button';
  export let fullWidth = true;
  export let disabled = false;
  export let title = '';
  // allow inline style/class and event forwarding
  export let style = '';
  export let ariaPressed = undefined;
  export let ariaExpanded = undefined;
  export let active = false;

  // Map variants to palette-driven colors (inspired by provided UIverse style)
  function colorsFor(v) {
    switch (v) {
      case 'secondary':
        return {
          bg: 'transparent',
          color: 'var(--text-0)',
          hoverBg: 'var(--bg-3)',
          hoverColor: 'var(--text-0)',
          ring: 'rgba(223, 208, 184, 0.25)'
        };
      case 'danger':
        return {
          bg: 'rgba(244, 67, 54, 0.10)',
          color: 'var(--danger)',
          hoverBg: 'var(--danger)',
          hoverColor: '#fff',
          ring: 'rgba(244, 67, 54, 0.25)'
        };
      case 'close':
        return {
          bg: 'rgba(244, 67, 54, 0.10)',
          color: 'var(--text-0)',
          hoverBg: 'var(--danger)',
          hoverColor: '#fff',
          ring: 'rgba(244, 67, 54, 0.25)'
        };
      case 'export':
        return {
          bg: 'var(--accent)',
          color: 'var(--bg-0)',
          hoverBg: 'var(--brand)',
          hoverColor: '#fff',
          ring: 'rgba(148, 137, 121, 0.35)' // based on --brand
        };
      case 'primary':
      default:
        return {
          bg: 'var(--accent)',
          color: 'var(--bg-0)',
          hoverBg: 'var(--brand)',
          hoverColor: '#fff',
          ring: 'rgba(148, 137, 121, 0.35)'
        };
    }
  }
  const c = colorsFor(variant);
  const variantClass =
    variant === 'secondary' ? 'btn-secondary' :
    variant === 'danger' ? 'btn-danger' :
    variant === 'export' ? 'btn-export' :
    variant === 'close' ? 'btn-close' :
    'btn-primary';
  const sizeStyle = size === 'sm' ? 'padding: 4px 8px; font-size: 12px;' : '';
</script>

<button
  {type}
  class={`uiv-btn ${variantClass} ${active ? 'path-highlighted' : ''}`}
  disabled={disabled}
  title={title}
  aria-pressed={ariaPressed}
  aria-expanded={ariaExpanded}
  style={`--btn-bg:${c.bg}; --btn-color:${c.color}; --btn-hover-bg:${c.hoverBg}; --btn-hover-color:${c.hoverColor}; --btn-ring:${c.ring}; ${fullWidth ? '' : 'width:auto; flex:0 0 auto;'} ${sizeStyle} ${style}`}
  on:click={(e) => dispatch('click', e)}
>
  <slot />
</button>

<style>
  .uiv-btn {
    background-color: var(--btn-bg);
    color: var(--btn-color);
    border: none;
    cursor: pointer;
    border-radius: var(--radius-1);
    position: relative;
    /* Only animate colors/scale to avoid ring morphing */
    transition: background-color 0.2s ease, color 0.2s ease, transform 0.05s ease;
    box-shadow: none;
    overflow: visible;
  }
  .uiv-btn::after {
    content: "";
    position: absolute;
    left: -3px;
    right: -3px;
    top: -3px;
    bottom: -3px;
    border-radius: calc(var(--radius-1) + 4px);
    box-shadow: 0 0 0 3px var(--btn-ring);
    opacity: 0;
    transform: scale(0.9);
    transition: transform 0.18s ease, opacity 0.18s ease;
    pointer-events: none;
  }
  .uiv-btn:hover {
    background-color: var(--btn-hover-bg);
    color: var(--btn-hover-color);
    /* ring scales in smoothly via pseudo-element */
  }
  .uiv-btn:hover::after {
    opacity: 1;
    transform: scale(1);
  }
  .uiv-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    box-shadow: none;
  }
</style>

