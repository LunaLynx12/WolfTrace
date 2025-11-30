<script>
  import { onMount, onDestroy } from 'svelte';
  import axios from 'axios';
  import SearchBar from './components/SearchBar.svelte';
  import AnalyticsPanel from './components/AnalyticsPanel.svelte';
  import ExportButton from './components/ExportButton.svelte';
  import SessionManager from './components/SessionManager.svelte';
  import QueryBuilder from './components/QueryBuilder.svelte';
  import GraphComparison from './components/GraphComparison.svelte';
  import BulkOperations from './components/BulkOperations.svelte';
  import ReportGenerator from './components/ReportGenerator.svelte';
  import GraphTemplates from './components/GraphTemplates.svelte';
  import HistoryControls from './components/HistoryControls.svelte';
  import NodeGrouping from './components/NodeGrouping.svelte';
  import KeyboardShortcuts from './components/KeyboardShortcuts.svelte';
  import GraphStatsWidget from './components/GraphStatsWidget.svelte';
  import Button from './components/ui/Button.svelte';
  import TabButton from './components/ui/TabButton.svelte';
  import NodeNotes from './components/NodeNotes.svelte';
  import { cacheManager } from './utils/cache.js';
  import { showNotification as showNotif } from './utils/notifications.js';
  import * as d3 from 'd3';
  import './App.css';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  let graphData = { nodes: [], links: [] };
  let selectedNode = null;
  let plugins = [];
  let loading = false;
  let pathResult = null;
  let sourceNode = '';
  let targetNode = '';
  let activeView = 'graph';
  let highlightedPath = null;
  let filteredNodes = null;
  let queryFilter = null;
  let selectedNodes = [];
  let diffGraph = null;
  let showShortcuts = false;
  let copiedNode = null;
  let nodeGrouping = null;
  let graphContainer;
  let graphInstance = null;
  let ForceGraphLib = null;
  let graphCollapsed = false;
  let graphFullscreen = false;
  let resizeObserver = null;
  let menuOpen = false;

  let initialLoaded = false;

  // Performance: Cache layout results to avoid recalculating
  let cachedLayoutData = null;
  let cachedLayoutHash = null;
  
  // Performance: Cache filtered graph data to avoid recalculating
  let cachedFilteredData = null;
  let cachedFilterHash = null;
  
  // Performance: Cache graph size to only update forces when it changes
  let lastGraphSize = 0;
  
  // Performance: Cache colors map outside function
  const NODE_COLORS = {
    'Entity': '#8B4513',      // Saddle brown
    'Host': '#8B0000',        // Dark red
    'IP': '#4B0082',          // Indigo
    'Domain': '#2F4F4F',      // Dark slate gray
    'ec2': '#B8860B',         // Dark goldenrod
    'Resource': '#800080',    // Purple
    'security-group': '#8B008B', // Dark magenta
    'vpc': '#006400',         // Dark green
    'Service': '#CD5C5C',     // Indian red
    'Technology': '#9370DB',  // Medium purple
    'Certificate': '#DAA520', // Goldenrod
    'WAF': '#DC143C',         // Crimson
    'Location': '#4682B4',    // Steel blue
    'Organization': '#556B2F', // Dark olive green
    'default': '#696969'      // Dim gray
  };
  
  // Performance: Cache icon map as Map for O(1) lookups
  const ICON_MAP = new Map([
    ['host', '\uf233'],           // fa-server (solid)
    ['server', '\uf233'],         // fa-server
    ['ip', '\uf0e8'],             // fa-network-wired
    ['address', '\uf0e8'],        // fa-network-wired
    ['domain', '\uf0ac'],         // fa-globe
    ['dns', '\uf0ac'],            // fa-globe
    ['certificate', '\uf023'],    // fa-lock
    ['cert', '\uf023'],           // fa-lock
    ['technology', '\uf013'],     // fa-cog (gear)
    ['tech', '\uf013'],           // fa-cog
    ['waf', '\uf3ed'],            // fa-shield-halved
    ['firewall', '\uf3ed'],       // fa-shield-halved
    ['endpoint', '\uf0c1'],       // fa-link
    ['url', '\uf0c1'],            // fa-link
    ['location', '\uf3c5'],       // fa-location-dot
    ['geo', '\uf3c5'],            // fa-location-dot
    ['organization', '\uf1ad'],  // fa-building
    ['org', '\uf1ad'],            // fa-building
    ['service', '\uf233'],        // fa-server
    ['port', '\uf1e6'],           // fa-plug
    ['resource', '\uf0c2'],       // fa-cloud
    ['ec2', '\uf0c2'],            // fa-cloud
    ['vpc', '\uf0c2'],            // fa-cloud
    ['security-group', '\uf0c2'], // fa-cloud
    ['nameserver', '\uf1c0'],     // fa-database
    ['ns', '\uf1c0'],             // fa-database
    ['entity', '\uf007'],         // fa-user
    ['user', '\uf007'],           // fa-user
    ['default', '\uf111']         // fa-circle
  ]);
  
  // Performance: Cache font strings to avoid repeated string concatenation
  const fontCache = new Map();
  function getFontString(size) {
    if (!fontCache.has(size)) {
      fontCache.set(size, `900 ${size}px "Font Awesome 6 Free"`);
    }
    return fontCache.get(size);
  }

  // Memory leak fix: Store keyboard shortcuts cleanup function
  let keyboardShortcutsCleanup = null;

  onMount(async () => {
    await loadPlugins();
    await initCache();
    if (!initialLoaded) {
      await loadGraph();
    }
    // initGraph will be called when graphContainer is available via reactive statement
    keyboardShortcutsCleanup = setupKeyboardShortcuts();
  });

  async function initGraph() {
    // Only initialize in browser environment
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    if (!ForceGraphLib) {
      // Lazy-load to avoid SSR importing force-graph (which touches window)
      const mod = await import('force-graph');
      ForceGraphLib = mod.default || mod;
    }
    if (graphContainer && !graphInstance && ForceGraphLib) {
      graphInstance = ForceGraphLib()(graphContainer)
        .nodeLabel(node => {
          // Performance: Cache label on node object to avoid repeated string concatenation
          if (!node.__label) {
            node.__label = `${node.id} (${node.type})`;
          }
          return node.__label;
        })
        .nodeColor(nodeColor)
        .linkLabel(link => {
          // Hide link labels for large graphs to improve performance
          const nodeCount = graphData?.nodes?.length || 0;
          if (nodeCount > 200) return '';
          return `${link.type || 'RELATED_TO'}`;
        })
        .linkColor(linkColor)
        .linkWidth(linkWidth)
        .linkDirectionalArrowLength(6) // Will be adjusted dynamically in updateGraph
        .linkDirectionalArrowRelPos(1)
        .linkCurvature(0) // Straight lines are faster to render
        .onNodeClick(handleNodeClick)
        .onNodeHover((node) => {
          if (typeof document !== 'undefined' && document.body) {
            document.body.style.cursor = node ? 'pointer' : 'default';
          }
        })
        .nodeVal(node => {
          // Performance: Use cached size if available, otherwise calculate and cache
          if (node.__size === undefined) {
            node.__size = Math.sqrt(Object.keys(node).length) * 3;
          }
          return node.__size;
        })
        // draw icons on top of each node circle
        .nodeCanvasObjectMode(() => 'after')
        .nodeCanvasObject((node, ctx, globalScale) => {
          // Skip icon rendering when zoomed out too far
          if (globalScale < 0.15) return;
          
          // Performance: Cache normalized node type on the node object
          if (!node.__typeNormalized) {
            node.__typeNormalized = (node.type || 'default').toString().toLowerCase();
          }
          const nodeType = node.__typeNormalized;
          
          // Get node size - use cached size
          const nodeSize = node.__size || 8;
          // Icon size should be proportional to node size, not zoom level
          const iconSize = Math.max(8, Math.min(16, nodeSize * 0.6));
          
          ctx.save();
          ctx.translate(node.x, node.y);
          
          // Get icon color - use white/light color for better visibility
          const nodeColorValue = nodeColor(node);
            ctx.fillStyle = '#ffffff';
          
          // Draw icon based on node type
          drawNodeIcon(ctx, nodeType, iconSize, nodeColorValue);
          
          ctx.restore();
        })
        .backgroundColor('rgba(0,0,0,0)')
        .cooldownTicks(100) // Will be adjusted dynamically in updateGraph
        .onEngineStop(() => {
          if (graphInstance) graphInstance.zoomToFit(400);
        })
        // Bloodweb-style forces - will be updated in updateGraph
        .d3Force('charge', d3.forceManyBody().strength(-300))
        .d3Force('link', d3.forceLink().id(d => d.id).distance(80).strength(0.5))
        .d3Force('center', d3.forceCenter(0, 0).strength(0.05));

      // ensure correct sizing
      queueMicrotask(() => updateGraphSize());

      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => updateGraphSize());
        resizeObserver.observe(graphContainer);
      }
      if (typeof window !== 'undefined') {
        window.addEventListener('resize', updateGraphSize);
      }

      updateGraph();
    }
  }

  // Performance: Debounce resize events (better than throttle for resize - waits for resize to finish)
  let resizeTimeout = null;
  function updateGraphSize() {
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
    }
    resizeTimeout = setTimeout(() => {
      if (graphInstance && graphContainer) {
    const w = graphContainer.clientWidth || 0;
    const h = graphContainer.clientHeight || 0;
    if (w > 0 && h > 0) {
      graphInstance.width(w).height(h);
    }
      }
      resizeTimeout = null;
    }, 150); // Debounce: wait 150ms after resize stops
  }

  function setupKeyboardShortcuts() {
    // Only set up in browser environment
    if (typeof window === 'undefined') return () => {};
    const handleKeyPress = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
      }
      if (e.key === 'Escape') {
        selectedNode = null;
        highlightedPath = null;
        selectedNodes = [];
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'c' && selectedNode) {
        e.preventDefault();
        copiedNode = selectedNode;
        showNotification('Node copied', 'success');
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'v' && copiedNode) {
        e.preventDefault();
        handlePasteNode();
      }
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showShortcuts = true;
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyPress);
      return () => window.removeEventListener('keydown', handleKeyPress);
    }
    return () => {};
  }

  async function initCache() {
    // Only run in browser environment
    if (typeof window === 'undefined' || typeof indexedDB === 'undefined') {
      return;
    }
    try {
      await cacheManager.init();
      const cachedGraph = await cacheManager.getGraph();
      if (cachedGraph && cachedGraph.nodes?.length > 0) {
        if (window.confirm('Load cached graph from previous session?')) {
          graphData = cachedGraph;
          initialLoaded = true;
          updateGraph();
        } else {
          initialLoaded = false;
        }
      }
    } catch (error) {
      console.error('Cache initialization failed:', error);
    }
  }

  async function loadGraph() {
    loading = true;
    try {
      const response = await axios.get(`${API_BASE}/graph`);
      const nodes = response.data.nodes || [];
      const edges = response.data.edges || [];
      // Performance: Remove console.log in production
      // console.log(`Loaded graph: ${nodes.length} nodes, ${edges.length} edges`);
      graphData = {
        nodes: nodes,
        links: edges
      };
      // Performance: Invalidate layout cache when new data is loaded
      cachedLayoutData = null;
      cachedLayoutHash = null;
      updateGraph();
      try {
        await cacheManager.saveGraph(graphData);
      } catch (cacheError) {
        console.error('Failed to cache graph:', cacheError);
      }
    } catch (error) {
      console.error('Failed to load graph:', error);
      showNotification('Failed to load graph: ' + error.message, 'error');
    } finally {
      loading = false;
    }
  }

  function calculateBloodwebLayout(data) {
    if (!data || !data.nodes || data.nodes.length === 0) return data;
    
    // Performance: Create a faster hash to check if layout needs recalculation
    // Use numeric hash instead of string concatenation for better performance
    let hash = data.nodes.length * 1000000 + data.links.length;
    data.nodes.forEach(n => {
      // Simple hash from node ID
      for (let i = 0; i < Math.min(n.id.length, 10); i++) {
        hash += n.id.charCodeAt(i) * (i + 1);
      }
    });
    const dataHash = hash.toString();
    
    // Performance: Return cached layout if data hasn't changed
    if (cachedLayoutData && cachedLayoutHash === dataHash) {
      return cachedLayoutData;
    }
    
    const nodeMap = new Map(data.nodes.map(n => [n.id, n]));
    const linkMap = new Map();
    
    // Build adjacency map (bidirectional for level calculation)
    data.links.forEach(link => {
      const source = typeof link.source === 'string' ? link.source : link.source.id;
      const target = typeof link.target === 'string' ? link.target : link.target.id;
      
      if (!linkMap.has(source)) linkMap.set(source, []);
      if (!linkMap.has(target)) linkMap.set(target, []);
      linkMap.get(source).push(target);
      linkMap.get(target).push(source);
    });
    
    // Find root: node with most connections
    let rootId = data.nodes[0]?.id;
    let maxConnections = 0;
    data.nodes.forEach(node => {
      const connections = linkMap.get(node.id)?.length || 0;
      if (connections > maxConnections) {
        maxConnections = connections;
        rootId = node.id;
      }
    });
    
    // Calculate levels using BFS
    // Performance: Use index pointer instead of shift() which is O(n)
    const levels = new Map();
    const visited = new Set();
    const queue = [{ id: rootId, level: 0 }];
    let queueIndex = 0;
    levels.set(rootId, 0);
    visited.add(rootId);
    
    while (queueIndex < queue.length) {
      const current = queue[queueIndex++];
      const neighbors = linkMap.get(current.id) || [];
      
      neighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          const level = current.level + 1;
          levels.set(neighborId, level);
          visited.add(neighborId);
          queue.push({ id: neighborId, level });
        }
      });
    }
    
    // Assign levels to all nodes
    // Performance: Iterate and track max instead of Math.max() on array
    let maxLevel = 0;
    levels.forEach(level => {
      if (level > maxLevel) maxLevel = level;
    });
    data.nodes.forEach(node => {
      if (!levels.has(node.id)) {
        levels.set(node.id, maxLevel + 1);
      }
      node.level = levels.get(node.id);
    });
    
    // Simple radial layout - don't fix positions, let forces handle it
    // Just set layout type and let the force simulation position nodes
    data.nodes.forEach(node => {
      node.layoutType = 'circle';
      // Don't set fx/fy - let forces position naturally
    });
    
    // Performance: Cache the layout result
    cachedLayoutData = data;
    cachedLayoutHash = dataHash;
    
    return data;
  }

  function updateGraph() {
    if (!graphInstance) {
      // console.warn('updateGraph called but graphInstance is not ready');
      return;
    }
    
    // Performance: Invalidate filter cache when graph data changes
    cachedFilteredData = null;
    cachedFilterHash = null;
    
    const data = getFilteredGraphData();
    
    // Bug fix: Clear link color cache and ID cache to prevent stale data
    if (data.links) {
      data.links.forEach(link => {
        delete link.__color;
        delete link.__sourceId;
        delete link.__targetId;
      });
    }
    
    // Ensure we have valid data structure
    if (!data || (!data.nodes && !data.links)) {
      // Performance: Gate console.warn behind debug flag
      if (import.meta.env.DEV) {
        console.warn('updateGraph called with invalid data:', data);
      }
      return;
    }
    
    // Ensure nodes and links are arrays
    const nodes = Array.isArray(data.nodes) ? data.nodes : [];
    const links = Array.isArray(data.links) ? data.links : [];
    
    const nodeCount = nodes.length;
    // Performance: Remove console.log in production
    // console.log(`Updating graph with ${nodeCount} nodes and ${links.length} links`);
    
    if (nodes.length === 0 && links.length === 0) {
      // Performance: Gate console.warn behind debug flag
      if (import.meta.env.DEV) {
        console.warn('updateGraph called with empty data');
      }
      // Still update to clear the graph
    }
    
    // Determine graph size for optimizations
    const isLargeGraph = nodeCount > 200;
    const isVeryLargeGraph = nodeCount > 500;
    
    // Performance: Always use shallow copy - deep cloning is too expensive
    // The layout function will handle mutations safely
    const dataToLayout = { nodes: [...nodes], links: [...links] };
    const layoutData = calculateBloodwebLayout(dataToLayout);
    
    // Performance: Remove console.log in production
    // console.log(`Graph data after layout: ${layoutData.nodes?.length || 0} nodes, ${layoutData.links?.length || 0} links`);
    
    // Ensure container has dimensions
    if (graphContainer) {
      const width = graphContainer.clientWidth || 800;
      const height = graphContainer.clientHeight || 600;
      if (width > 0 && height > 0) {
        graphInstance.width(width).height(height);
      }
    }
    
    graphInstance.graphData(layoutData);
    
    // Performance: Only update forces when graph size changes
    const currentGraphSize = nodeCount;
    const graphSizeChanged = currentGraphSize !== lastGraphSize;
    
    if (graphSizeChanged) {
      // Optimize cooldown ticks based on graph size
      if (isVeryLargeGraph) {
        graphInstance.cooldownTicks(50);
      } else if (isLargeGraph) {
        graphInstance.cooldownTicks(75);
      } else {
        graphInstance.cooldownTicks(100);
      }
      
      // Optimize arrow length for large graphs
      if (isVeryLargeGraph) {
        graphInstance.linkDirectionalArrowLength(4);
        // Performance: Disable link labels for very large graphs to reduce rendering overhead
        graphInstance.linkLabel(() => '');
      } else {
        graphInstance.linkDirectionalArrowLength(6);
        // Re-enable link labels for smaller graphs
        graphInstance.linkLabel(link => {
          return link.label || '';
        });
      }
      
      // Balanced force layout - optimized for large graphs
      graphInstance.d3Force('radial', d3.forceRadial()
        .strength(d => {
          const level = d.level || 0;
          // Reduce radial force strength for large graphs
          const baseStrength = isVeryLargeGraph ? 0.2 : (isLargeGraph ? 0.25 : 0.3);
          return baseStrength + (level * 0.05);
        })
        .radius(d => {
          const level = d.level || 0;
          return 80 + (level * 120);
        })
        .x(0)
        .y(0)
      )
      .d3Force('collision', d3.forceCollide()
        .radius(d => {
          // Performance: Use cached size
          const size = d.__size || 8;
          return size + 8;
        })
        .strength(isVeryLargeGraph ? 0.6 : (isLargeGraph ? 0.7 : 0.8)) // Reduce collision strength for large graphs
      )
      .d3Force('charge', d3.forceManyBody()
        .strength(d => {
          // Use Barnes-Hut approximation for large graphs (faster)
          if (isVeryLargeGraph) return -150;
          if (isLargeGraph) return -175;
          return -200;
        })
      )
      .d3Force('link', d3.forceLink().id(d => d.id).distance(d => {
        // Safety check: ensure source and target are node objects
        if (!d.source || !d.target || typeof d.source === 'string' || typeof d.target === 'string') {
          return 100; // Default distance
        }
        // Shorter links for same level, longer for different levels
        const sourceLevel = d.source.level || 0;
        const targetLevel = d.target.level || 0;
        const levelDiff = Math.abs(sourceLevel - targetLevel);
        return 60 + (levelDiff * 40);
      }).strength(isVeryLargeGraph ? 0.4 : (isLargeGraph ? 0.5 : 0.6))) // Reduce link strength for large graphs
      .d3Force('center', d3.forceCenter(0, 0).strength(0.05));
      
      // For very large graphs, reduce alpha decay to settle faster
      if (isVeryLargeGraph && graphInstance.d3Force) {
        graphInstance.d3Force().alphaDecay(0.0228); // Faster decay
      }
      
      lastGraphSize = currentGraphSize;
    }
    
    // Force a refresh
    graphInstance.refresh();
  }

  async function loadPlugins() {
    try {
      const response = await axios.get(`${API_BASE}/plugins`);
      plugins = response.data;
    } catch (error) {
      console.error('Failed to load plugins:', error);
    }
  }

  // Use imported showNotification function
  const showNotification = showNotif;
  
  // Make available globally for child components
  if (typeof window !== 'undefined') {
    window.showNotification = showNotification;
  }

  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    loading = true;
    try {
      // Clear the graph before importing new data
      await axios.post(`${API_BASE}/clear`);
      
      // Clear local state
      graphData = { nodes: [], links: [] };
      // Performance: Invalidate layout cache
      cachedLayoutData = null;
      cachedLayoutHash = null;
      pathResult = null;
      highlightedPath = null;
      selectedNode = null;
      selectedNodes = [];
      queryFilter = null;
      filteredNodes = null;
      
      // Clear cache
      try {
        await cacheManager.saveGraph({ nodes: [], links: [] });
      } catch (cacheError) {
        console.error('Failed to clear cache:', cacheError);
      }
      
      if (file.name.toLowerCase().endsWith('.zip') || file.type === 'application/zip' || file.type === 'application/x-zip-compressed') {
        const form = new FormData();
        form.append('file', file);
        const response = await axios.post(`${API_BASE}/import-zip-autodetect`, form, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const detectedPlugin = response.data.detected_plugin || 'unknown';
        showNotification(`Import successful: ${response.data.result?.message || 'ZIP imported'} (detected: ${detectedPlugin})`, 'success');
      } else {
        const text = await file.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          data = text;
        }
        const response = await axios.post(`${API_BASE}/import-autodetect`, {
          data: data
        });
        const detectedPlugin = response.data.detected_plugin || 'unknown';
        showNotification(`Import successful: ${response.data.result.message} (detected: ${detectedPlugin})`, 'success');
      }
      
      // Load the new graph data
      await loadGraph();
      // Give the graph a moment to initialize if needed
      if (!graphInstance && graphContainer) {
        await initGraph();
      }
      // Small delay to ensure graph instance is ready
      await new Promise(resolve => setTimeout(resolve, 100));
      updateGraph();
    } catch (error) {
      showNotification(`Import failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
      // Reset file input so same file can be imported again
      event.target.value = '';
    }
  }

  async function findPaths() {
    if (!sourceNode || !targetNode) {
      showNotification('Please enter both source and target nodes', 'error');
      return;
    }

    loading = true;
    try {
      const response = await axios.post(`${API_BASE}/paths`, {
        source: sourceNode,
        target: targetNode,
        max_depth: 5
      });
      pathResult = response.data;
      if (response.data.length > 0) {
        highlightedPath = response.data[0];
        showNotification(`Found ${response.data.length} path(s)`, 'success');
      } else {
        showNotification('No paths found', 'info');
      }
      updateGraph();
    } catch (error) {
      showNotification(`Path finding failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      loading = false;
    }
  }

  async function clearGraph() {
    if (typeof window !== 'undefined' && !window.confirm('Clear all graph data?')) {
      return;
    }
    try {
      await axios.post(`${API_BASE}/clear`);
      graphData = { nodes: [], links: [] };
      // Performance: Invalidate layout cache
      cachedLayoutData = null;
      cachedLayoutHash = null;
      pathResult = null;
      highlightedPath = null;
      updateGraph();
      showNotification('Graph cleared', 'success');
    } catch (error) {
      showNotification(`Failed to clear: ${error.message}`, 'error');
    }
  }

  function handleNodeClick(node, event) {
    selectedNode = node;
    
    if (event?.ctrlKey || event?.metaKey) {
      if (selectedNodes.includes(node.id)) {
        selectedNodes = selectedNodes.filter(id => id !== node.id);
      } else {
        selectedNodes = [...selectedNodes, node.id];
      }
    } else {
      selectedNodes = [node.id];
    }
    
    if (graphInstance && node.x !== undefined && node.y !== undefined) {
      graphInstance.centerAt(node.x, node.y, 600);
      graphInstance.zoom(2, 600);
    }
  }

  async function handleUndo() {
    try {
      const response = await axios.post(`${API_BASE}/history/undo`);
      if (response.data.graph) {
        graphData = {
          nodes: response.data.graph.nodes || [],
          links: response.data.graph.edges || []
        };
        // Performance: Invalidate layout cache
        cachedLayoutData = null;
        cachedLayoutHash = null;
        updateGraph();
        showNotification('Undone', 'success');
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        showNotification('Undo failed', 'error');
      }
    }
  }

  async function handleRedo() {
    try {
      const response = await axios.post(`${API_BASE}/history/redo`);
      if (response.data.graph) {
        graphData = {
          nodes: response.data.graph.nodes || [],
          links: response.data.graph.edges || []
        };
        // Performance: Invalidate layout cache
        cachedLayoutData = null;
        cachedLayoutHash = null;
        updateGraph();
        showNotification('Redone', 'success');
      }
    } catch (error) {
      if (error.response?.status !== 400) {
        showNotification('Redo failed', 'error');
      }
    }
  }

  function handleNodeSearch(node) {
    selectedNode = node;
    if (graphInstance) {
      const graphNode = graphData.nodes.find(n => n.id === node.id);
      if (graphNode && graphNode.x !== undefined && graphNode.y !== undefined) {
        graphInstance.centerAt(graphNode.x, graphNode.y, 600);
        graphInstance.zoom(2, 600);
      }
    }
  }

  async function handlePasteNode() {
    if (!copiedNode) return;

    try {
      const newNodeId = `${copiedNode.id}_copy_${Date.now()}`;
      const { id, x, y, vx, vy, fx, fy, ...properties } = copiedNode;
      
      await axios.post(`${API_BASE}/nodes`, {
        id: newNodeId,
        type: copiedNode.type || 'Entity',
        properties: {
          ...properties,
          copied_from: copiedNode.id
        }
      });

      showNotification('Node pasted', 'success');
      await loadGraph();
    } catch (error) {
      showNotification(`Paste failed: ${error.response?.data?.error || error.message}`, 'error');
    }
  }

  function drawNodeIcon(ctx, nodeType, size, nodeColorValue) {
    // Performance: Use Map.get() for O(1) lookup
    const iconChar = ICON_MAP.get(nodeType) || ICON_MAP.get('default');
    
    // Performance: Use cached font string
    ctx.font = getFontString(size);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    
    // Draw the icon
    ctx.fillText(iconChar, 0, 0);
  }

  function nodeColor(node) {
    // Performance: Use Set for O(1) lookups instead of Array.includes() O(n)
    if (selectedNodesSet && selectedNodesSet.has(node.id)) return '#FFD700';
    if (highlightedPathSet && highlightedPathSet.has(node.id)) return '#FFD700';
    if (diffGraph && node.change_type) {
      if (node.change_type === 'added') return '#4CAF50';
      if (node.change_type === 'removed') return '#f44336';
      if (node.change_type === 'changed') return '#FF9800';
    }
    
    // Performance: Use cached colors map (defined at top level)
    const baseColor = NODE_COLORS[node.type] || NODE_COLORS['default'];
    
    // Performance: Removed unused darkenFactor calculation (was calculated but never used)
    
    return baseColor;
  }
  
  // Performance: Cache Sets for O(1) lookups instead of Array.includes()
  let selectedNodesSet = new Set();
  let highlightedPathSet = null;
  
  // Update Sets when arrays change
  $: selectedNodesSet = new Set(selectedNodes);
  $: highlightedPathSet = highlightedPath ? new Set(highlightedPath) : null;

  // Performance: Cache path index map for faster lookups
  let highlightedPathIndexMap = null;
  $: if (highlightedPath) {
    highlightedPathIndexMap = new Map(highlightedPath.map((id, idx) => [id, idx]));
  } else {
    highlightedPathIndexMap = null;
  }

  function linkColor(link) {
    // Performance: Cache source/target IDs on link object to avoid repeated extraction
    if (!link.__sourceId || !link.__targetId) {
      link.__sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      link.__targetId = typeof link.target === 'string' ? link.target : link.target.id;
    }
    const sourceId = link.__sourceId;
    const targetId = link.__targetId;
    
    // Performance: Use Set for O(1) lookups and cached path indices
    if (highlightedPath && highlightedPathSet && highlightedPathIndexMap) {
      
      if (highlightedPathSet.has(sourceId) && highlightedPathSet.has(targetId)) {
        // Check if they're adjacent in the path using cached index map
        const sourceIdx = highlightedPathIndexMap.get(sourceId);
        const targetIdx = highlightedPathIndexMap.get(targetId);
        if (sourceIdx !== undefined && targetIdx !== undefined && Math.abs(sourceIdx - targetIdx) === 1) {
        return '#FFD700';
        }
      }
    }
    
    // Bloodweb-style links - darker, web-like
    // Performance: Cache level calculations on link object
    if (link.__color === undefined) {
    const sourceLevel = link.source?.level || 0;
    const targetLevel = link.target?.level || 0;
    const levelDiff = Math.abs(sourceLevel - targetLevel);
    
    // Darker links for connections between different levels (web-like)
    if (levelDiff > 0) {
        link.__color = `rgba(139, 0, 0, ${0.4 - levelDiff * 0.1})`; // Dark red, fading
      } else {
    // Lighter links for same-level connections
        link.__color = 'rgba(139, 69, 19, 0.3)'; // Saddle brown, subtle
      }
    }
    return link.__color;
  }

  function linkWidth(link) {
    // Performance: Use cached IDs from link object
    const sourceId = link.__sourceId || (typeof link.source === 'string' ? link.source : link.source.id);
    const targetId = link.__targetId || (typeof link.target === 'string' ? link.target : link.target.id);
    
    // Performance: Use Set for O(1) lookups and cached path indices
    if (highlightedPath && highlightedPathSet && highlightedPathIndexMap) {
      
      if (highlightedPathSet.has(sourceId) && highlightedPathSet.has(targetId)) {
        // Check if they're adjacent in the path using cached index map
        const sourceIdx = highlightedPathIndexMap.get(sourceId);
        const targetIdx = highlightedPathIndexMap.get(targetId);
        if (sourceIdx !== undefined && targetIdx !== undefined && Math.abs(sourceIdx - targetIdx) === 1) {
        return 4;
        }
      }
    }
    return 2;
  }

  function getFilteredGraphData() {
    // Performance: Create numeric hash instead of string template for better performance
    let hash = (queryFilter ? 1 : 0) * 1000000000;
    hash += (filteredNodes ? 1 : 0) * 100000000;
    hash += (filteredNodes?.length || 0) * 1000000;
    hash += (graphData.nodes?.length || 0) * 1000;
    hash += (graphData.links?.length || 0);
    const filterHash = hash.toString();
    
    // Performance: Return cached data if filters haven't changed
    if (cachedFilteredData && cachedFilterHash === filterHash) {
      return cachedFilteredData;
    }
    
    let result;
    if (queryFilter) {
      result = {
        nodes: queryFilter.nodes || [],
        links: queryFilter.edges || []
      };
    } else if (filteredNodes) {
      // Performance: Convert filteredNodes to Set for O(1) lookups
      const filteredSet = new Set(filteredNodes);
      result = {
        nodes: graphData.nodes.filter(n => filteredSet.has(n.id)),
        links: graphData.links.filter(l => {
          const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
          const targetId = typeof l.target === 'string' ? l.target : l.target.id;
          return filteredSet.has(sourceId) && filteredSet.has(targetId);
        })
      };
    } else {
      result = graphData;
    }
    
    // Performance: Cache the result
    cachedFilteredData = result;
    cachedFilterHash = filterHash;
    
    return result;
  }

  // Initialize graph when container is available
  $: if (graphContainer && !graphInstance && typeof window !== 'undefined') {
    (async () => {
      await initGraph();
      // If we have graph data, update the graph after initialization
      if (graphData && (graphData.nodes?.length > 0 || graphData.links?.length > 0)) {
        updateGraph();
      }
    })();
  }

  // Performance: Only update graph when data actually changes (not just reference)
  // Use hash-based change detection to catch when nodes/links are replaced with same-length arrays
  let lastGraphDataHash = '';
  $: if (graphInstance && graphData) {
    // Create hash from node IDs and link source/target pairs
    // This catches changes even when arrays have same length
    const nodeIds = (graphData.nodes || []).map(n => n.id).sort().join(',');
    const linkPairs = (graphData.links || []).map(l => {
      const sourceId = typeof l.source === 'string' ? l.source : (l.source?.id || '');
      const targetId = typeof l.target === 'string' ? l.target : (l.target?.id || '');
      return `${sourceId}-${targetId}`;
    }).sort().join(',');
    const hash = `${(graphData.nodes?.length || 0)}-${(graphData.links?.length || 0)}-${nodeIds}-${linkPairs}`;
    
    // Only update if hash changed or it's the first load
    if (hash !== lastGraphDataHash || lastGraphDataHash === '') {
      lastGraphDataHash = hash;
    updateGraph();
    }
  }

  // re-measure after collapsing/expanding
  $: if (graphCollapsed !== undefined) {
    if (typeof window !== 'undefined') {
      setTimeout(updateGraphSize, 50);
    }
  }

  onDestroy(() => {
    // Memory leak fix: Clean up keyboard shortcuts
    if (keyboardShortcutsCleanup) {
      keyboardShortcutsCleanup();
      keyboardShortcutsCleanup = null;
    }
    
    // Memory leak fix: Clean up resize timeout
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
      resizeTimeout = null;
    }
    
    if (resizeObserver) {
      try { resizeObserver.disconnect(); } catch {}
      resizeObserver = null;
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', updateGraphSize);
    }
  });
</script>

<div class="app" class:graph-collapsed={graphCollapsed} class:graph-fullscreen={graphFullscreen}>
  {#if !graphFullscreen && !graphCollapsed}
    <button
      type="button"
      class="hamburger-toggle"
      class:active={menuOpen}
      title="Menu"
      aria-label="Toggle menu"
      on:click={() => (menuOpen = !menuOpen)}
      on:keydown={(e) => e.key === 'Escape' && (menuOpen = false)}
    >
      <span></span>
      <span></span>
      <span></span>
    </button>
  {/if}
  
  <div class="sidebar" class:hidden={graphFullscreen} class:menu-open={menuOpen}>
    {#if !graphFullscreen && !graphCollapsed}
      <!-- Menu View - Always in DOM for animation -->
      <div class="sidebar-menu">
        <div class="sidebar-menu-header">
          <h2>Menu</h2>
        </div>
        <div class="view-menu" role="menu">
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'graph'}
            on:click={() => { activeView = 'graph'; menuOpen = false; }}
          >
            Graph
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'analytics'}
            on:click={() => { activeView = 'analytics'; menuOpen = false; }}
          >
            Analytics
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'query'}
            on:click={() => { activeView = 'query'; menuOpen = false; }}
          >
            Query
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'sessions'}
            on:click={() => { activeView = 'sessions'; menuOpen = false; }}
          >
            Sessions
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'compare'}
            on:click={() => { activeView = 'compare'; menuOpen = false; }}
          >
            Compare
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'bulk'}
            on:click={() => { activeView = 'bulk'; menuOpen = false; }}
          >
            Bulk
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'templates'}
            on:click={() => { activeView = 'templates'; menuOpen = false; }}
          >
            Templates
          </button>
          <button
            type="button"
            class="menu-item"
            class:active={activeView === 'report'}
            on:click={() => { activeView = 'report'; menuOpen = false; }}
          >
            Report
          </button>
        </div>
      </div>
    {/if}

    {#if !menuOpen || graphFullscreen || graphCollapsed}
      <!-- Normal Sidebar View -->
      <div class="sidebar-header">
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: var(--space-1);">
          <div>
            <h1>WolfTrace</h1>
            <p class="subtitle">Modular Graph Visualization</p>
          </div>
          <Button
            variant="secondary"
            ariaPressed={graphCollapsed}
            ariaExpanded={!graphCollapsed}
            title={graphCollapsed ? 'Expand Graph Area' : 'Collapse Graph Area'}
            on:click={() => (graphCollapsed = !graphCollapsed)}
            style="padding: 6px 10px; font-size: 12px; white-space: nowrap;"
            fullWidth={false}
          >
            {graphCollapsed ? 'Show Graph' : 'Hide Graph'}
          </Button>
        </div>

        {#if graphFullscreen || graphCollapsed}
          <div class="view-tabs" role="tablist" aria-label="Views">
            <TabButton active={activeView === 'graph'} onClick={() => activeView = 'graph'} title="Graph">Graph</TabButton>
            <TabButton active={activeView === 'analytics'} onClick={() => activeView = 'analytics'} title="Analytics">Analytics</TabButton>
            <TabButton active={activeView === 'query'} onClick={() => activeView = 'query'} title="Query">Query</TabButton>
            <TabButton active={activeView === 'sessions'} onClick={() => activeView = 'sessions'} title="Sessions">Sessions</TabButton>
            <TabButton active={activeView === 'compare'} onClick={() => activeView = 'compare'} title="Compare">Compare</TabButton>
            <TabButton active={activeView === 'bulk'} onClick={() => activeView = 'bulk'} title="Bulk">Bulk</TabButton>
            <TabButton active={activeView === 'templates'} onClick={() => activeView = 'templates'} title="Templates">Templates</TabButton>
            <TabButton active={activeView === 'report'} onClick={() => activeView = 'report'} title="Report">Report</TabButton>
          </div>
        {/if}
      </div>
    {/if}

    {#if !menuOpen || graphFullscreen || graphCollapsed}
      <div class="sidebar-section">
      <HistoryControls onHistoryChange={(graph) => {
        if (graph) {
          graphData = {
            nodes: graph.nodes || [],
            links: graph.edges || []
          };
          // Performance: Invalidate layout cache
          cachedLayoutData = null;
          cachedLayoutHash = null;
        } else {
          loadGraph();
        }
        updateGraph();
      }} />
    </div>

    {#if activeView === 'graph'}
      <div class="sidebar-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h2 style="margin: 0;">Search</h2>
          <button
            type="button"
            class="bi bi-keyboard icon-action"
            title="Keyboard shortcuts"
            on:click={() => (showShortcuts = true)}
            aria-label="Show keyboard shortcuts"
          ></button>
        </div>
        <SearchBar 
          onNodeSelect={(node) => selectedNode = node}
          onSearch={handleNodeSearch}
          allNodes={graphData.nodes}
        />
      </div>

      <div class="sidebar-section">
        <GraphStatsWidget graphData={graphData} compact={true} />
      </div>

      <div class="sidebar-section">
        <NodeGrouping 
          graphData={graphData}
          onGroupChange={(grouping) => {
            nodeGrouping = grouping;
          }}
        />
      </div>

      <div class="sidebar-section">
        <h2>Import Data</h2>
        <p style="color: var(--text-2); font-size: 12px; margin-bottom: 10px;">
          Choose a JSON or ZIP file to import. The system will automatically detect the appropriate format.
        </p>
        <Button
          style="padding: 8px 12px; width: 100%; margin: 0;"
          on:click={() => document.getElementById('file-import')?.click()}
          title="Choose JSON or ZIP to import (format will be auto-detected)"
        >
          Choose File to Import
        </Button>
        <input
          id="file-import"
          type="file"
          accept=".json,application/json,.zip,application/zip,application/x-zip-compressed"
          on:change={handleFileUpload}
          style="display: none;"
        />
      </div>

      <div class="sidebar-section">
        <h2>Path Finding</h2>
        <input
          type="text"
          placeholder="Source Node ID"
          bind:value={sourceNode}
          class="input-field"
        />
        <input
          type="text"
          placeholder="Target Node ID"
          bind:value={targetNode}
          class="input-field"
        />
        <Button on:click={findPaths}>Find Paths</Button>
        {#if pathResult && pathResult.length > 0}
          <div class="path-result">
            <strong>Found {pathResult.length} path(s):</strong>
            {#each pathResult as path, idx}
              <Button
                variant="secondary"
                fullWidth={true}
                style="margin-top: 8px; text-align: left;"
                active={highlightedPath === path}
                on:click={() => highlightedPath = path}
              >
                {path.join(' → ')}
              </Button>
            {/each}
          </div>
        {/if}
        {#if highlightedPath}
          <Button 
            variant="secondary"
            on:click={() => highlightedPath = null} 
            style="margin-top: 10px;"
          >
            Clear Highlight
          </Button>
        {/if}
      </div>

      <div class="sidebar-section">
        <h2>Graph Info</h2>
        <p>Nodes: {graphData.nodes.length}</p>
        <p>Edges: {graphData.links.length}</p>
        <ExportButton graphData={graphData} graphInstance={graphInstance} />
        <Button variant="danger" on:click={clearGraph} style="margin-top: 10px;">
          Clear Graph
        </Button>
      </div>

      {#if selectedNode}
        <div class="sidebar-section">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h2 style="margin: 0;">Selected Node</h2>
            <div style="display: flex; gap: 5px;">
              <Button
                variant="secondary"
                size="sm"
                on:click={() => {
                  copiedNode = selectedNode;
                  showNotification('Node copied', 'success');
                }}
                title="Copy (Ctrl+C)"
                fullWidth={false}
              >
                📋
              </Button>
              {#if copiedNode}
                <Button
                  variant="secondary"
                  size="sm"
                  on:click={handlePasteNode}
                  title="Paste (Ctrl+V)"
                  fullWidth={false}
                >
                  📄
                </Button>
              {/if}
              <Button 
                variant="close"
                size="sm"
                on:click={() => selectedNode = null} 
                fullWidth={false}
                title="Close"
              >
                ×
              </Button>
            </div>
          </div>
          <div class="node-details">
            <p><strong>ID:</strong> {selectedNode.id}</p>
            <p><strong>Type:</strong> {selectedNode.type}</p>
            {#each Object.entries(selectedNode).filter(([key]) => !['id', 'type', 'notes', '_notes'].includes(key)) as [key, value]}
              <p>
                <strong>{key}:</strong> {JSON.stringify(value)}
              </p>
            {/each}
          </div>
          <div style="margin-top: 15px;">
            <NodeNotes 
              node={selectedNode}
              onNoteUpdate={(nodeId, notes) => {
                if (selectedNode && selectedNode.id === nodeId) {
                  selectedNode = { ...selectedNode, notes, _notes: notes };
                }
                loadGraph();
              }}
            />
          </div>
        </div>
      {/if}
    {/if}

    {#if activeView === 'analytics'}
      <AnalyticsPanel />
    {/if}

    {#if activeView === 'query'}
      <QueryBuilder 
        onQueryResult={(result) => {
          if (result) {
            queryFilter = result;
            graphData = {
              nodes: result.nodes || [],
              links: result.edges || []
            };
          } else {
            queryFilter = null;
            loadGraph();
          }
          updateGraph();
        }}
      />
    {/if}

    {#if activeView === 'sessions'}
      <SessionManager 
        onLoadSession={loadGraph}
        currentGraphData={graphData}
      />
    {/if}

    {#if activeView === 'compare'}
      <GraphComparison
        currentGraph={graphData}
        onLoadDiffGraph={(diffData) => {
          diffGraph = diffData;
          graphData = {
            nodes: diffData.nodes || [],
            links: diffData.edges || []
          };
          updateGraph();
        }}
      />
    {/if}

    {#if activeView === 'bulk'}
      <BulkOperations
        selectedNodes={selectedNodes}
        onOperationComplete={loadGraph}
      />
    {/if}

    {#if activeView === 'templates'}
      <GraphTemplates
        onTemplateApplied={loadGraph}
      />
    {/if}

    {#if activeView === 'report'}
      <ReportGenerator />
    {/if}
    {/if}
  </div>

  <KeyboardShortcuts 
    isOpen={showShortcuts}
    onClose={() => showShortcuts = false}
  />

  <div class="graph-container" class:collapsed={graphCollapsed} class:fullscreen={graphFullscreen}>
    <div class="graph-inner">
      <div class="graph-toolbar">
        <Button
          variant="secondary"
          title={graphFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
          on:click={() => (graphFullscreen = !graphFullscreen)}
          style="padding: 6px 10px; font-size: 12px;"
          fullWidth={false}
        >
          {graphFullscreen ? '⤓ Exit Fullscreen' : '⤢ Fullscreen'}
        </Button>
      </div>
      <div style="position: absolute; top: 10px; right: 10px; z-index: 1000;">
        <GraphStatsWidget graphData={graphData} compact={true} />
      </div>
      {#if loading}
        <div class="loading">Loading...</div>
      {/if}
      <div
        class="graph-surface"
        bind:this={graphContainer}
        style="height: {graphCollapsed ? '0px' : '100%'}; opacity: {graphCollapsed ? 0 : 1};"
      >
        {#if !graphCollapsed && (graphData?.nodes?.length || 0) + (graphData?.links?.length || 0) === 0 && !loading}
          <div style="height: 100%; display: flex; align-items: center; justify-content: center; color: var(--text-2);">
            <div style="text-align: center;">
              <div style="font-size: 14px; margin-bottom: 6px;">No graph data yet</div>
              <div style="font-size: 12px;">Import data or run a query to get started</div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

