<script>
  export let nodeTypes = [];

  // Local icon map (same semantics as main graph)
  const ICON_MAP = new Map([
    ['host', '\uf233'],           // server
    ['server', '\uf233'],
    ['ip', '\uf0e8'],             // network-wired
    ['address', '\uf0e8'],
    ['domain', '\uf0ac'],         // globe
    ['dns', '\uf0ac'],
    ['certificate', '\uf023'],    // lock
    ['cert', '\uf023'],
    ['technology', '\uf013'],     // cog
    ['tech', '\uf013'],
    ['waf', '\uf3ed'],            // shield
    ['firewall', '\uf3ed'],
    ['endpoint', '\uf0c1'],       // link
    ['url', '\uf0c1'],
    ['location', '\uf3c5'],       // location-dot
    ['geo', '\uf3c5'],
    ['organization', '\uf1ad'],   // building
    ['org', '\uf1ad'],
    ['service', '\uf233'],        // server
    ['port', '\uf1e6'],           // plug
    ['resource', '\uf0c2'],       // cloud
    ['ec2', '\uf0c2'],
    ['vpc', '\uf0c2'],
    ['security-group', '\uf0c2'],
    ['nameserver', '\uf1c0'],     // database
    ['ns', '\uf1c0'],
    ['entity', '\uf007'],         // user
    ['user', '\uf007'],
    ['cve', '\uf188'],            // bug
    ['vulnerability', '\uf188'],
    ['vuln', '\uf188'],
    ['finding', '\uf188'],
    ['default', '\uf111']         // circle
  ]);

  function iconForType(type) {
    if (!type) return ICON_MAP.get('default');
    const raw = type.toString();
    const t = raw.toLowerCase();
    if (ICON_MAP.has(t)) return ICON_MAP.get(t);
    if (t.includes('host') || t.includes('server')) return ICON_MAP.get('host');
    if (t.includes('port')) return ICON_MAP.get('port');
    if (t.includes('endpoint') || t.includes('url') || t.includes('http')) return ICON_MAP.get('endpoint');
    if (t.includes('ip')) return ICON_MAP.get('ip');
    if (t.includes('domain')) return ICON_MAP.get('domain');
    if (t.includes('cert')) return ICON_MAP.get('certificate');
    if (t.includes('waf') || t.includes('firewall')) return ICON_MAP.get('waf');
    if (t.includes('cve') || t.includes('vuln')) return ICON_MAP.get('cve');
    if (t.includes('user') || t.includes('account')) return ICON_MAP.get('user');
    return ICON_MAP.get('default');
  }

  const shortcuts = [
    { keys: ['↑', '↓', '←', '→'], description: 'Walk between neighbor nodes' },
    { keys: ['Enter'], description: 'Focus: selected node + 2 hops' },
    { keys: ['F'], description: 'Focus: selected node + 2 hops' },
    { keys: ['E'], description: 'Expand 1 hop: neighbors only' },
    { keys: ['P'], description: 'Paths: use selected as source' },
    { keys: ['Esc'], description: 'Clear selection & focus mode' },
    { keys: ['?'], description: 'Open full shortcuts help' }
  ];
</script>

{#if nodeTypes && nodeTypes.length}
  <div class="icon-legend" role="region" aria-label="Icon legend and shortcuts">
    <div class="legend-section">
      <div class="legend-title">Icons</div>
      <div class="legend-list">
        {#each nodeTypes as t}
          <div class="legend-row">
            <span class="legend-icon" aria-hidden="true">{iconForType(t)}</span>
            <span class="legend-type">{t}</span>
          </div>
        {/each}
      </div>
    </div>
    <div class="legend-section shortcuts">
      <div class="legend-title">Keys</div>
      <div class="legend-list">
        {#each shortcuts as s}
          <div class="legend-row shortcut-row">
            <span class="legend-keys">
              {#each s.keys as k, i}
                <kbd>{k}</kbd>{#if i < s.keys.length - 1}<span> </span>{/if}
              {/each}
            </span>
            <span class="legend-type">{s.description}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
{/if}

<style>
  .icon-legend {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10;
    background: rgba(22, 27, 34, 0.96);
    border-radius: 10px;
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6);
    min-width: 200px;
    max-width: 260px;
    font-size: 11px;
    color: #E8EAED;
  }

  .legend-section + .legend-section {
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .legend-title {
    font-weight: 600;
    margin-bottom: 6px;
    color: #f1f3f4;
    letter-spacing: 0.02em;
  }

  .legend-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .legend-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .legend-icon {
    width: 18px;
    text-align: center;
    font-family: "Font Awesome 6 Free", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-weight: 900;
    font-size: 13px;
    color: #ffd54f;
  }

  .legend-type {
    color: #cfd2dc;
  }

  .shortcuts .legend-type {
    color: #b0bec5;
  }

  .legend-keys {
    min-width: 70px;
    display: inline-flex;
    flex-wrap: wrap;
    gap: 2px;
  }

  kbd {
    display: inline-block;
    padding: 1px 4px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(33, 37, 43, 0.9);
    font-size: 10px;
  }
</style>

