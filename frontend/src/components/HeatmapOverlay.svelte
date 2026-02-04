<script>
  export let enabled = false;
  export let metric = 'degree';
  export let range = { min: 0, max: 1 };
  export let onToggle = () => {};
  export let onMetricChange = () => {};

  const metrics = [
    { value: 'degree', label: 'Degree' },
    { value: 'betweenness', label: 'Betweenness (approx.)' },
    { value: 'risk_score', label: 'Risk score' },
    { value: 'path_count_high_value', label: 'Paths to high-value' }
  ];

  // Same vivid gradient as App: cyan -> yellow -> red (visible on dark backgrounds)
  function interpolate(t) {
    t = Math.max(0, Math.min(1, t));
    let r, g, b;
    if (t < 0.5) {
      const s = t * 2;
      r = Math.round(0 + 255 * s);
      g = Math.round(188 + (235 - 188) * s);
      b = Math.round(212 + (59 - 212) * s);
    } else {
      const s = (t - 0.5) * 2;
      r = 255;
      g = Math.round(235 + (68 - 235) * s);
      b = Math.round(59 + (68 - 59) * s);
    }
    return `rgb(${r},${g},${b})`;
  }

  const gradientStyle = `linear-gradient(to right, ${interpolate(0)}, ${interpolate(0.5)}, ${interpolate(1)})`;
</script>

<div class="heatmap-overlay" role="region" aria-label="Heatmap overlay">
  <div class="heatmap-header">
    <span class="heatmap-title">🔥 Heatmap</span>
    <label class="heatmap-toggle" title={enabled ? 'Turn heatmap off' : 'Color nodes by metric'}>
      <input type="checkbox" checked={enabled} on:change={() => onToggle()} />
      <span class="toggle-slider"></span>
    </label>
  </div>
  {#if enabled}
    <div class="heatmap-controls">
      <label class="heatmap-metric-label">Color by</label>
      <select
        class="heatmap-select"
        value={metric}
        on:change={(e) => onMetricChange(e.target.value)}
        aria-label="Heatmap metric"
      >
        {#each metrics as m}
          <option value={m.value}>{m.label}</option>
        {/each}
      </select>
    </div>
    <div class="heatmap-legend">
      <div class="heatmap-gradient" style="background: {gradientStyle};" role="img" aria-label="Low to high gradient"></div>
      <div class="heatmap-labels">
        <span class="heatmap-low">Low</span>
        <span class="heatmap-high">High</span>
      </div>
      <div class="heatmap-range">
        <span>{range.min}</span>
        <span>{range.max}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .heatmap-overlay {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 10;
    background: rgba(28, 33, 42, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
    padding: 12px 14px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 0, 0, 0.2);
    min-width: 180px;
  }
  .heatmap-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
  }
  .heatmap-title {
    font-size: 13px;
    font-weight: 700;
    color: #E8EAED;
    letter-spacing: 0.02em;
  }
  .heatmap-toggle {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 22px;
    flex-shrink: 0;
  }
  .heatmap-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #4a5059;
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;
  }
  .toggle-slider::before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 2px;
    bottom: 2px;
    background: #B8BFC6;
    border-radius: 50%;
    transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
  .heatmap-toggle input:checked + .toggle-slider {
    background: #2e7d32;
    border-color: #4caf50;
    box-shadow: 0 0 12px rgba(76, 175, 80, 0.4);
  }
  .heatmap-toggle input:checked + .toggle-slider::before {
    transform: translateX(18px);
    background: #fff;
  }
  .heatmap-controls {
    margin-bottom: 10px;
  }
  .heatmap-metric-label {
    display: block;
    font-size: 11px;
    color: #9aa0a6;
    margin-bottom: 5px;
    font-weight: 500;
  }
  .heatmap-select {
    width: 100%;
    padding: 8px 10px;
    font-size: 12px;
    background: #393E46;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    color: #E8EAED;
    cursor: pointer;
  }
  .heatmap-select:focus {
    outline: none;
    border-color: #948979;
    box-shadow: 0 0 0 2px rgba(148, 137, 121, 0.25);
  }
  .heatmap-legend {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .heatmap-gradient {
    height: 14px;
    border-radius: 6px;
    margin-bottom: 6px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .heatmap-labels {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 600;
    color: #9aa0a6;
  }
  .heatmap-range {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #B8BFC6;
    margin-top: 3px;
  }
</style>
