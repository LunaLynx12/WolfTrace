<script>
  import { onMount, onDestroy } from 'svelte';

  /** @type {import('force-graph').ForceGraphInstance} */
  export let graphInstance = null;
  /** @type {{ nodes: any[], links: any[] }} */
  export let graphData = { nodes: [], links: [] };
  /** @type {HTMLElement | null} */
  export let graphContainer = null;

  const MINIMAP_WIDTH = 180;
  const MINIMAP_HEIGHT = 120;
  const PADDING = 8;
  const VIEWPORT_STROKE = '#DFD0B8';
  const VIEWPORT_FILL = 'rgba(223, 208, 184, 0.15)';
  const NODE_FILL = 'rgba(148, 137, 121, 0.8)';
  const LINK_STROKE = 'rgba(148, 137, 121, 0.35)';

  let canvasEl;
  let zoomTransform = { k: 1, x: 0, y: 0 };
  let mainWidth = 800;
  let mainHeight = 600;
  let rafId = null;
  let zoomSubscribed = false;
  let dragging = false;

  function getBbox() {
    const nodes = graphData?.nodes?.filter((n) => n.x != null && n.y != null) ?? [];
    if (nodes.length === 0) return null;
    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
    for (const n of nodes) {
      if (n.x < xMin) xMin = n.x;
      if (n.x > xMax) xMax = n.x;
      if (n.y < yMin) yMin = n.y;
      if (n.y > yMax) yMax = n.y;
    }
    const pad = 40;
    const w = xMax - xMin || 1;
    const h = yMax - yMin || 1;
    return {
      xMin: xMin - pad,
      xMax: xMax + pad,
      yMin: yMin - pad,
      yMax: yMax + pad,
      width: w + 2 * pad,
      height: h + 2 * pad
    };
  }

  function graphToMinimap(gx, gy, bbox, scale, offsetX, offsetY) {
    return {
      x: (gx - bbox.xMin) * scale + offsetX,
      y: (gy - bbox.yMin) * scale + offsetY
    };
  }

  function minimapToGraph(mx, my, bbox, scale, offsetX, offsetY) {
    return {
      x: (mx - offsetX) / scale + bbox.xMin,
      y: (my - offsetY) / scale + bbox.yMin
    };
  }

  function getViewportGraphRect() {
    if (!graphInstance || !graphContainer) return null;
    const W = mainWidth;
    const H = mainHeight;
    const { k, x, y } = zoomTransform;
    // x,y from onZoom are center of viewport in graph coords (force-graph merges centerAt() into transform)
    return {
      left: x - W / (2 * k),
      top: y - H / (2 * k),
      width: W / k,
      height: H / k
    };
  }

  function draw() {
    if (!canvasEl) return;
    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;

    const dpr = Math.min(2, typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1);
    const w = MINIMAP_WIDTH;
    const h = MINIMAP_HEIGHT;
    const displayW = w;
    const displayH = h;
    if (canvasEl.width !== w * dpr || canvasEl.height !== h * dpr) {
      canvasEl.width = w * dpr;
      canvasEl.height = h * dpr;
      canvasEl.style.width = `${displayW}px`;
      canvasEl.style.height = `${displayH}px`;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const bbox = getBbox();
    if (!bbox) return;

    const scale = Math.min(
      (w - 2 * PADDING) / bbox.width,
      (h - 2 * PADDING) / bbox.height
    );
    const offsetX = PADDING + (w - 2 * PADDING - bbox.width * scale) / 2 + bbox.xMin * scale;
    const offsetY = PADDING + (h - 2 * PADDING - bbox.height * scale) / 2 + bbox.yMin * scale;

    // Links (thin lines)
    const links = graphData?.links ?? [];
    const nodeById = new Map((graphData?.nodes ?? []).map((n) => [n.id, n]));
    ctx.strokeStyle = LINK_STROKE;
    ctx.lineWidth = 0.8;
    for (const link of links) {
      const src = typeof link.source === 'object' ? link.source : nodeById.get(link.source);
      const tgt = typeof link.target === 'object' ? link.target : nodeById.get(link.target);
      if (src?.x == null || src?.y == null || tgt?.x == null || tgt?.y == null) continue;
      const a = graphToMinimap(src.x, src.y, bbox, scale, offsetX, offsetY);
      const b = graphToMinimap(tgt.x, tgt.y, bbox, scale, offsetX, offsetY);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }

    // Nodes
    ctx.fillStyle = NODE_FILL;
    const nodes = graphData?.nodes?.filter((n) => n.x != null && n.y != null) ?? [];
    const nodeR = Math.max(1, Math.min(2.5, 80 / Math.max(1, nodes.length)));
    for (const n of nodes) {
      const p = graphToMinimap(n.x, n.y, bbox, scale, offsetX, offsetY);
      ctx.beginPath();
      ctx.arc(p.x, p.y, nodeR, 0, Math.PI * 2);
      ctx.fill();
    }

    // Viewport box
    const vp = getViewportGraphRect();
    if (vp) {
      const tl = graphToMinimap(vp.left, vp.top, bbox, scale, offsetX, offsetY);
      const vpW = vp.width * scale;
      const vpH = vp.height * scale;
      ctx.fillStyle = VIEWPORT_FILL;
      ctx.strokeStyle = VIEWPORT_STROKE;
      ctx.lineWidth = 1.5;
      ctx.fillRect(tl.x, tl.y, vpW, vpH);
      ctx.strokeRect(tl.x, tl.y, vpW, vpH);
    }
  }

  function scheduleDraw() {
    if (rafId != null) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      draw();
    });
  }

  function onZoomTransform(transform) {
    zoomTransform = transform;
    scheduleDraw();
  }

  function handlePointerDown(e) {
    if (!graphInstance || !canvasEl) return;
    e.preventDefault();
    e.stopPropagation();
    dragging = true;
    const rect = canvasEl.getBoundingClientRect();
    const scaleX = canvasEl.width / rect.width;
    const scaleY = canvasEl.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;
    const bbox = getBbox();
    if (!bbox) return;
    const s = Math.min(
      (MINIMAP_WIDTH - 2 * PADDING) / bbox.width,
      (MINIMAP_HEIGHT - 2 * PADDING) / bbox.height
    );
    const ox = PADDING + (MINIMAP_WIDTH - 2 * PADDING - bbox.width * s) / 2 + bbox.xMin * s;
    const oy = PADDING + (MINIMAP_HEIGHT - 2 * PADDING - bbox.height * s) / 2 + bbox.yMin * s;
    const g = minimapToGraph(mx, my, bbox, s, ox, oy);
    graphInstance.centerAt(g.x, g.y, 0);
  }

  function handlePointerMove(e) {
    if (!dragging || !graphInstance || !canvasEl) return;
    e.preventDefault();
    const rect = canvasEl.getBoundingClientRect();
    const scaleX = canvasEl.width / rect.width;
    const scaleY = canvasEl.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;
    const bbox = getBbox();
    if (!bbox) return;
    const s = Math.min(
      (MINIMAP_WIDTH - 2 * PADDING) / bbox.width,
      (MINIMAP_HEIGHT - 2 * PADDING) / bbox.height
    );
    const ox = PADDING + (MINIMAP_WIDTH - 2 * PADDING - bbox.width * s) / 2 + bbox.xMin * s;
    const oy = PADDING + (MINIMAP_HEIGHT - 2 * PADDING - bbox.height * s) / 2 + bbox.yMin * s;
    const g = minimapToGraph(mx, my, bbox, s, ox, oy);
    graphInstance.centerAt(g.x, g.y, 0);
  }

  function handlePointerUp() {
    dragging = false;
  }

  $: if (graphData && canvasEl) scheduleDraw();

  onMount(() => {
    if (graphContainer) {
      mainWidth = graphContainer.clientWidth || 800;
      mainHeight = graphContainer.clientHeight || 600;
      const ro = new ResizeObserver(() => {
        if (graphContainer) {
          mainWidth = graphContainer.clientWidth || 800;
          mainHeight = graphContainer.clientHeight || 600;
          scheduleDraw();
        }
      });
      ro.observe(graphContainer);
      return () => ro.disconnect();
    }
  });

  $: if (graphInstance && canvasEl && !zoomSubscribed && typeof graphInstance.onZoom === 'function') {
    zoomSubscribed = true;
    graphInstance.onZoom(onZoomTransform);
    const k = graphInstance.zoom();
    const c = graphInstance.centerAt();
    if (typeof k === 'number' && c && typeof c.x === 'number' && typeof c.y === 'number') {
      zoomTransform = { k, x: c.x, y: c.y };
    }
    scheduleDraw();
  }

  onDestroy(() => {
    zoomSubscribed = false;
    if (rafId != null) cancelAnimationFrame(rafId);
  });
</script>

<svelte:window
  on:mousemove={handlePointerMove}
  on:mouseup={handlePointerUp}
  on:mouseleave={handlePointerUp}
/>

{#if graphInstance && (graphData?.nodes?.length ?? 0) > 0}
  <div
    class="minimap-wrap"
    role="presentation"
    aria-label="Graph minimap - click or drag to pan"
  >
    <canvas
      bind:this={canvasEl}
      class="minimap-canvas"
      width={MINIMAP_WIDTH}
      height={MINIMAP_HEIGHT}
      on:mousedown={handlePointerDown}
      on:pointerdown|preventDefault={handlePointerDown}
    ></canvas>
  </div>
{/if}

<style>
  .minimap-wrap {
    position: absolute;
    bottom: 12px;
    right: 12px;
    z-index: 10;
    border-radius: var(--radius-1, 8px);
    overflow: hidden;
    box-shadow: var(--shadow, 0 4px 20px rgba(0,0,0,0.3));
    border: 1px solid var(--border, rgba(255,255,255,0.08));
    background: var(--bg-overlay-4, rgba(27, 34, 51, 0.8));
    cursor: pointer;
  }
  .minimap-canvas {
    display: block;
    width: 180px;
    height: 120px;
    vertical-align: top;
  }
</style>
