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
  import NodeTypeFilter from './components/NodeTypeFilter.svelte';
  import Button from './components/ui/Button.svelte';
  import TabButton from './components/ui/TabButton.svelte';
  import NodeNotes from './components/NodeNotes.svelte';
  import { cacheManager } from './utils/cache.js';
  import { showNotification as showNotif } from './utils/notifications.js';
  import * as d3 from 'd3';
  import './App.css';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  let graphData = { nodes: [], links: [] };
  let preventAutoLoad = false; // Prevent reactive statement from auto-loading cached data
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
  let enabledNodeTypes = new Set(); // Track enabled node types for filtering
  let graphDataInitialized = false; // Track if we've initialized enabledNodeTypes for current graph
  let graphContainer;
  let graphInstance = null;
  let ForceGraphLib = null;
  let graphCollapsed = false;
  let graphFullscreen = false;
  let recenterTimeout = null; // Debounce recenter calls
  let isRecenterInProgress = false; // Prevent multiple recenters
  let isDragging = false; // Track if user is dragging a node
  let isScrolling = false; // Track if user is scrolling
  let scrollTimeout = null; // Track when scrolling stops
  let lastRecenterTime = 0; // Track last recenter to prevent rapid calls
  let resizeObserver = null;
  let menuOpen = false;

  let initialLoaded = false;
  let showCachedGraphDialog = false;
  let cachedGraphData = null;
  
  // Node popup (click to show)
  let popupNode = null;

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
        .onNodeHover((node, prevNode) => {
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

      // Add mouse/touch event listeners to detect dragging and scrolling
      if (graphContainer) {
        let mouseDown = false;
        let touchStart = false;
        
        // Mouse events
        graphContainer.addEventListener('mousedown', (e) => {
          mouseDown = true;
          isDragging = false; // Will be set to true if mouse moves
        });
        
        graphContainer.addEventListener('mousemove', (e) => {
          if (mouseDown) {
            isDragging = true;
            // Cancel any pending recenter when dragging
            if (recenterTimeout) {
              clearTimeout(recenterTimeout);
              recenterTimeout = null;
            }
          }
        });
        
        graphContainer.addEventListener('mouseup', () => {
          if (mouseDown && isDragging) {
            // Wait for drag to settle before allowing recenter
            setTimeout(() => {
              isDragging = false;
            }, 500);
          } else {
            isDragging = false;
          }
          mouseDown = false;
        });
        
        graphContainer.addEventListener('mouseleave', () => {
          mouseDown = false;
          if (isDragging) {
            setTimeout(() => {
              isDragging = false;
            }, 500);
          }
        });
        
        // Touch events
        graphContainer.addEventListener('touchstart', () => {
          touchStart = true;
          isDragging = false;
        });
        
        graphContainer.addEventListener('touchmove', () => {
          if (touchStart) {
            isDragging = true;
            if (recenterTimeout) {
              clearTimeout(recenterTimeout);
              recenterTimeout = null;
            }
          }
        });
        
        graphContainer.addEventListener('touchend', () => {
          if (touchStart && isDragging) {
            setTimeout(() => {
              isDragging = false;
            }, 500);
          } else {
            isDragging = false;
          }
          touchStart = false;
        });
        
        // Scroll detection (wheel events)
        graphContainer.addEventListener('wheel', () => {
          isScrolling = true;
          // Cancel any pending recenter when scrolling
          if (recenterTimeout) {
            clearTimeout(recenterTimeout);
            recenterTimeout = null;
          }
          // Clear existing scroll timeout
          if (scrollTimeout) {
            clearTimeout(scrollTimeout);
          }
          // Wait for scrolling to stop
          scrollTimeout = setTimeout(() => {
            isScrolling = false;
            scrollTimeout = null;
          }, 500); // Wait 500ms after last scroll event
        }, { passive: true });
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
        if (popupNode) {
          popupNode = null;
        } else {
          selectedNode = null;
          highlightedPath = null;
          selectedNodes = [];
        }
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
      // Clear graphData first to prevent any auto-loading
      graphData = { nodes: [], links: [] };
      preventAutoLoad = true;
      
      await cacheManager.init();
      const cachedGraph = await cacheManager.getGraph();
      if (cachedGraph && cachedGraph.nodes?.length > 0) {
        cachedGraphData = cachedGraph;
        showCachedGraphDialog = true;
        // Don't set initialLoaded here - wait for user decision
        // Keep preventAutoLoad = true until user decides
      } else {
        initialLoaded = false;
        preventAutoLoad = false; // Safe to allow auto-loading
      }
    } catch (error) {
      console.error('Cache initialization failed:', error);
      initialLoaded = false;
      preventAutoLoad = false; // Safe to allow auto-loading
    }
  }

  async function handleLoadCachedGraph() {
    if (cachedGraphData) {
      preventAutoLoad = false; // Allow updates now
      graphData = cachedGraphData;
      initialLoaded = true;
      showCachedGraphDialog = false;
      cachedGraphData = null;
      // Clear filtered data
      filteredNodes = null;
      queryFilter = null;
      selectedNode = null;
      selectedNodes = [];
      highlightedPath = null;
      // Performance: Invalidate layout cache
      cachedLayoutData = null;
      cachedLayoutHash = null;
      
      // Initialize enabledNodeTypes immediately after loading cached data
      if (graphData.nodes && graphData.nodes.length > 0 && !userHasCustomizedTypes) {
        const allTypes = new Set(graphData.nodes.map(n => n.type || 'default').filter(Boolean));
        enabledNodeTypes = new Set(allTypes);
        graphDataInitialized = true;
      }
      
      // Wait for graphInstance to be ready if it's not yet
      if (!graphInstance) {
        // Wait a bit for graph to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      updateGraph();
    }
  }

  async function handleCancelCachedGraph() {
    // Clear the cache when user cancels
    try {
      await cacheManager.saveGraph({ nodes: [], links: [] });
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
    showCachedGraphDialog = false;
    cachedGraphData = null;
    initialLoaded = false;
    preventAutoLoad = false; // Allow updates now
    // Ensure graphData is empty
    graphData = { nodes: [], links: [] };
    // Clear the graph display immediately
    if (graphInstance) {
      graphInstance.graphData({ nodes: [], links: [] });
    }
    // Clear backend graph as well
    try {
      await axios.post(`${API_BASE}/clear`);
    } catch (error) {
      console.error('Failed to clear backend graph:', error);
    }
    // Load fresh graph
    await loadGraph();
  }

  async function loadGraph() {
    loading = true;
    try {
      // Reset node type filter initialization FIRST, before clearing graphData
      // This prevents reactive statements from interfering
      graphDataInitialized = false;
      enabledNodeTypes = new Set();
      userHasCustomizedTypes = false; // Reset customization flag for new graph
      
      // Clear existing graph data
      graphData = { nodes: [], links: [] };
      // Performance: Invalidate layout cache when new data is loaded
      cachedLayoutData = null;
      cachedLayoutHash = null;
      // Clear filtered data
      filteredNodes = null;
      queryFilter = null;
      selectedNode = null;
      selectedNodes = [];
      highlightedPath = null;
      
      // Update graph to clear the display - ensure graphInstance is ready
      if (graphInstance) {
        // Force clear by setting empty data directly
        graphInstance.graphData({ nodes: [], links: [] });
      }
      
      const response = await axios.get(`${API_BASE}/graph`);
      const nodes = response.data.nodes || [];
      const edges = response.data.edges || [];
      
      // Initialize enabledNodeTypes BEFORE setting graphData to prevent race conditions
      // This ensures it's set before any reactive statements fire
      if (nodes.length > 0 && !userHasCustomizedTypes) {
        const allTypes = new Set(nodes.map(n => n.type || 'default').filter(Boolean));
        enabledNodeTypes = new Set(allTypes);
        graphDataInitialized = true;
      }
      
      // NOW set graphData - this will trigger reactive statements, but enabledNodeTypes is already set
      graphData = {
        nodes: nodes,
        links: edges
      };
      
      // Performance: Invalidate layout cache when new data is loaded
      cachedLayoutData = null;
      cachedLayoutHash = null;
      
      // Force hash reset to ensure reactive statement detects the change
      lastGraphDataHash = '';
      
      // Small delay to ensure state is settled, then force update
      // The reactive statement will also handle it, but we ensure it happens
      await new Promise(resolve => setTimeout(resolve, 10));
      if (graphInstance) {
        updateGraph();
      }
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
    
    // Force graph update by setting data
    // Create completely fresh objects to ensure force-graph recognizes them as new
    // This is critical for nodes that are being reactivated after being filtered out
    const freshNodes = layoutData.nodes.map(n => {
      // Create a completely new node object with all properties
      const newNode = { ...n };
      // Don't delete x, y as they might be needed for positioning
      // But clear force-graph internal tracking properties
      delete newNode.__index;
      return newNode;
    });
    
    const freshLinks = layoutData.links.map(l => {
      const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
      const targetId = typeof l.target === 'string' ? l.target : l.target.id;
      return {
        ...l,
        source: sourceId,
        target: targetId
      };
    });
    
    // Resolve source/target to node objects for force-graph
    const nodeMap = new Map(freshNodes.map(n => [n.id, n]));
    const resolvedLinks = freshLinks.map(l => ({
      ...l,
      source: nodeMap.get(l.source) || l.source,
      target: nodeMap.get(l.target) || l.target
    }));
    
    // Force a complete graph refresh by clearing first, then setting new data
    // This ensures force-graph recognizes all nodes as new
    const currentData = graphInstance.graphData();
    const currentNodes = currentData?.nodes?.length || 0;
    const currentLinks = currentData?.links?.length || 0;
    const needsFullRefresh = currentData && 
      (currentNodes !== freshNodes.length || 
       currentLinks !== resolvedLinks.length);
    
    if (needsFullRefresh) {
      // Clear the graph first to force a complete reset
      graphInstance.graphData({ nodes: [], links: [] });
      // Wait for the clear to process, then set new data
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          graphInstance.graphData({ nodes: freshNodes, links: resolvedLinks });
          // Restart simulation
          if (graphInstance.d3Force) {
            const force = graphInstance.d3Force();
            if (force && typeof force.alpha === 'function' && typeof force.restart === 'function') {
              force.alpha(1).restart();
            }
          }
        });
      });
    } else {
      // If size hasn't changed, just update the data
      graphInstance.graphData({ nodes: freshNodes, links: resolvedLinks });
      // Restart simulation to ensure nodes are positioned
      if (graphInstance.d3Force) {
        const force = graphInstance.d3Force();
        if (force && typeof force.alpha === 'function' && typeof force.restart === 'function') {
          force.alpha(1).restart();
        }
      }
    }
    
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
        const force = graphInstance.d3Force();
        if (force && typeof force.alphaDecay === 'function') {
          force.alphaDecay(0.0228); // Faster decay
        }
      }
      
      lastGraphSize = currentGraphSize;
    }
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
        const nodesAdded = response.data.nodes_added || 0;
        const edgesAdded = response.data.edges_added || 0;
        showNotification(
          `Import successful: ${nodesAdded} nodes, ${edgesAdded} edges (detected: ${detectedPlugin})`,
          'success'
        );
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
      // Reset node type filter for new data
      graphDataInitialized = false;
      enabledNodeTypes = new Set();
      // Give the graph a moment to initialize if needed
      if (!graphInstance && graphContainer) {
        await initGraph();
      }
      // Ensure graph updates with new data
      if (graphInstance) {
        updateGraph();
      }
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

  function recenterToNode(node, zoomLevel = 1.5) {
    if (!graphInstance || !node || node.x === undefined || node.y === undefined) {
      return;
    }
    
    // Prevent multiple recenters - check if one is in progress or was called recently
    const now = Date.now();
    if (isRecenterInProgress || (now - lastRecenterTime < 1500)) {
      return; // Skip if recenter is in progress or was called less than 1.5s ago
    }
    
    // Don't recenter if user is dragging or scrolling
    if (isDragging || isScrolling) {
      return;
    }
    
    // Cancel any pending recenter
    if (recenterTimeout) {
      clearTimeout(recenterTimeout);
    }
    
    // Debounce recenter with a longer delay to avoid conflicts with user interactions
    // This gives time for any drag/pan operations to complete
    recenterTimeout = setTimeout(() => {
      // Double-check conditions before recentering
      if (isDragging || isScrolling || isRecenterInProgress) {
        recenterTimeout = null;
        return;
      }
      
      if (graphInstance && node.x !== undefined && node.y !== undefined) {
        isRecenterInProgress = true;
        lastRecenterTime = Date.now();
        
        // Slower, smoother animation (1200ms instead of 600ms)
        graphInstance.centerAt(node.x, node.y, 1200);
        graphInstance.zoom(zoomLevel, 1200);
        
        // Reset flag after animation completes
        setTimeout(() => {
          isRecenterInProgress = false;
        }, 1300); // Slightly longer than animation duration
      }
      recenterTimeout = null;
    }, 500); // Longer delay to ensure any user interactions are complete
  }

  function handleNodeClick(node, event) {
    selectedNode = node;
    popupNode = node; // Show popup on click
    
    if (event?.ctrlKey || event?.metaKey) {
      if (selectedNodes.includes(node.id)) {
        selectedNodes = selectedNodes.filter(id => id !== node.id);
      } else {
        selectedNodes = [...selectedNodes, node.id];
      }
      // Don't recenter on multi-select
      return;
    } else {
      selectedNodes = [node.id];
    }
    
    // Recenter with debouncing
    recenterToNode(node);
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
    const graphNode = graphData.nodes.find(n => n.id === node.id);
    if (graphNode) {
      // Use the improved recenter function
      recenterToNode(graphNode, 1.8); // Slightly higher zoom for search results
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
    
    // Color links based on the target node color
    // Performance: Cache color calculation on link object
    if (link.__color === undefined) {
      // Get the target node (where the arrow points)
      const targetNode = typeof link.target === 'string' 
        ? graphData?.nodes?.find(n => n.id === link.target)
        : link.target;
      
      if (targetNode) {
        // Get the target node's color and apply opacity for better visibility
        const targetColor = nodeColor(targetNode);
        // Convert hex to rgba with opacity, or use the color as-is if it's already rgba
        if (targetColor.startsWith('#')) {
          // Convert hex to rgb
          const hex = targetColor.replace('#', '');
          const r = parseInt(hex.substring(0, 2), 16);
          const g = parseInt(hex.substring(2, 4), 16);
          const b = parseInt(hex.substring(4, 6), 16);
          link.__color = `rgba(${r}, ${g}, ${b}, 0.6)`;
        } else if (targetColor.startsWith('rgba')) {
          // Already rgba, just adjust opacity
          link.__color = targetColor.replace(/rgba\(([^)]+)\)/, (match, content) => {
            const parts = content.split(',').map(s => s.trim());
            if (parts.length === 4) {
              return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, 0.6)`;
            }
            return match;
          });
        } else if (targetColor.startsWith('rgb')) {
          // Convert rgb to rgba
          link.__color = targetColor.replace('rgb', 'rgba').replace(')', ', 0.6)');
        } else {
          // Fallback: use default with opacity
          link.__color = 'rgba(105, 105, 105, 0.6)';
        }
      } else {
        // Fallback to default color if target node not found
        link.__color = 'rgba(105, 105, 105, 0.6)'; // Dim gray with opacity
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
    hash += enabledNodeTypes.size * 100; // Include node type filter in hash
    // Add enabled types to hash
    const enabledTypesArray = [...enabledNodeTypes].sort();
    enabledTypesArray.forEach((type, idx) => {
      hash += type.charCodeAt(0) * (idx + 1);
    });
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
      // CRITICAL: Create a copy of graphData to avoid mutating the original
      // This ensures we always filter from the full dataset, not a previously filtered one
      result = {
        nodes: [...(graphData.nodes || [])],
        links: [...(graphData.links || [])]
      };
    }
    
    // Apply node type filter - always filter based on enabledNodeTypes
    // IMPORTANT: Only filter if types are explicitly initialized AND user has customized them
    // Otherwise, show all nodes by default
    if (result.nodes && result.nodes.length > 0) {
      // Only filter if:
      // 1. Types are initialized (we know what types exist)
      // 2. User has customized types (explicitly enabled/disabled some)
      // 3. There are enabled types (at least one is enabled)
      if (graphDataInitialized && userHasCustomizedTypes && enabledNodeTypes.size > 0) {
        // Filter nodes by enabled types
        const filteredNodeIds = new Set();
        result.nodes = result.nodes.filter(n => {
          const nodeType = n.type || 'default';
          const isEnabled = enabledNodeTypes.has(nodeType);
          if (isEnabled) {
            filteredNodeIds.add(n.id);
            return true;
          }
          return false;
        });
        
        // Filter links to only include those between visible nodes
        if (result.links && result.links.length > 0) {
          result.links = result.links.filter(l => {
            const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
            const targetId = typeof l.target === 'string' ? l.target : l.target.id;
            return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId);
          });
        }
      }
      // Otherwise, show all nodes (default behavior - no filtering)
    }
    
    // Performance: Cache the result
    cachedFilteredData = result;
    cachedFilterHash = filterHash;
    
    return result;
  }

  // Initialize enabled types when graph data loads (only once, not on every change)
  // Track the graph data to detect when it's actually a new/different graph
  let lastGraphDataInitHash = '';
  let userHasCustomizedTypes = false; // Track if user has manually toggled types
  
  // Backup initialization: Only run if loadGraph() didn't initialize (e.g., cached graph load)
  $: if (graphData?.nodes && graphData.nodes.length > 0 && !loading && !graphDataInitialized && !userHasCustomizedTypes) {
    // Create a simple hash from node count and first few node IDs to detect graph changes
    const nodeIds = graphData.nodes.slice(0, 5).map(n => n.id).join(',');
    const currentHash = `${graphData.nodes.length}-${nodeIds}`;
    
    // Only initialize if this is a completely new graph (different hash)
    if (currentHash !== lastGraphDataInitHash) {
      const allTypes = new Set(graphData.nodes.map(n => n.type || 'default').filter(Boolean));
      enabledNodeTypes = new Set(allTypes);
      graphDataInitialized = true;
      lastGraphDataInitHash = currentHash;
    }
  }
  
  // Safety: Re-initialize if somehow enabledNodeTypes is empty but we have data
  $: if (graphData?.nodes && graphData.nodes.length > 0 && !loading && graphDataInitialized && enabledNodeTypes.size === 0 && !userHasCustomizedTypes) {
    const allTypes = new Set(graphData.nodes.map(n => n.type || 'default').filter(Boolean));
    enabledNodeTypes = new Set(allTypes);
  }

  function toggleNodeType(type) {
    // Mark that user has customized types - this prevents reactive statement from resetting
    userHasCustomizedTypes = true;
    
    // Safety: If enabledNodeTypes is empty but we have graph data, initialize it first
    if (enabledNodeTypes.size === 0 && graphData?.nodes && graphData.nodes.length > 0 && graphDataInitialized) {
      const allTypes = new Set(graphData.nodes.map(n => n.type || 'default').filter(Boolean));
      enabledNodeTypes = new Set(allTypes);
    }
    
    const wasEnabled = enabledNodeTypes.has(type);
    const newSet = new Set(enabledNodeTypes);
    
    if (wasEnabled) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    
    // Update the Set - this must be a new Set object to trigger reactivity
    enabledNodeTypes = newSet;
    
    // Invalidate ALL caches to force complete update
    cachedFilteredData = null;
    cachedFilterHash = null;
    cachedLayoutData = null;
    cachedLayoutHash = null;
    // Reset lastGraphDataHash to force reactive update
    lastGraphDataHash = '';
    
    // Force graph update immediately
    if (graphInstance) {
      // Clear graph first to force complete reset
      graphInstance.graphData({ nodes: [], links: [] });
      
      // Use requestAnimationFrame to ensure the Set update has propagated
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          updateGraph();
        });
      });
    }
  }

  // Initialize graph when container is available
  $: if (graphContainer && !graphInstance && typeof window !== 'undefined') {
    (async () => {
      await initGraph();
      // If we have graph data and auto-load is not prevented, update the graph after initialization
      if (!preventAutoLoad && graphData && (graphData.nodes?.length > 0 || graphData.links?.length > 0)) {
        updateGraph();
      }
    })();
  }

  // Performance: Only update graph when data actually changes (not just reference)
  // Use hash-based change detection to catch when nodes/links are replaced with same-length arrays
  let lastGraphDataHash = '';
  let updateGraphTimeout = null;
  
  // Watch both graphData AND enabledNodeTypes for changes
  // Reference enabledNodeTypes.size to ensure reactivity
  $: if (graphInstance && graphData && !preventAutoLoad && enabledNodeTypes.size >= 0) {
    // Debounce updates to prevent excessive calls
    if (updateGraphTimeout) {
      clearTimeout(updateGraphTimeout);
    }
    
    updateGraphTimeout = setTimeout(() => {
      // Create hash that detects actual data changes
      // Use a combination of counts and a sample of IDs for performance
      const nodeCount = graphData.nodes?.length || 0;
      const linkCount = graphData.links?.length || 0;
      
      // Sample IDs from different parts of the array for better change detection
      let idSample = '';
      if (nodeCount > 0) {
        const sampleSize = Math.min(10, nodeCount); // Sample up to 10 nodes
        const step = Math.max(1, Math.floor(nodeCount / sampleSize));
        const sampledIds = [];
        for (let i = 0; i < nodeCount; i += step) {
          sampledIds.push(graphData.nodes[i]?.id || '');
          if (sampledIds.length >= sampleSize) break;
        }
        idSample = sampledIds.join(',');
      }
      
      const enabledTypesHash = [...enabledNodeTypes].sort().join(',');
      const hash = `${nodeCount}-${linkCount}-${idSample}-${enabledTypesHash}`;
      
      // Always update if hash changed, or if it's the first load, or if we have data but hash is empty
      if (hash !== lastGraphDataHash || lastGraphDataHash === '' || (nodeCount > 0 && lastGraphDataHash === '')) {
        lastGraphDataHash = hash;
        updateGraph();
      }
      updateGraphTimeout = null;
    }, 30); // Reduced debounce to 30ms for more responsive updates
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
    
    // Memory leak fix: Clean up updateGraph timeout
    if (updateGraphTimeout) {
      clearTimeout(updateGraphTimeout);
      updateGraphTimeout = null;
    }
    
    // Memory leak fix: Clean up tooltip timeout
    if (tooltipTimeout) {
      clearTimeout(tooltipTimeout);
      tooltipTimeout = null;
    }
    
    // Memory leak fix: Clean up resize timeout
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
      resizeTimeout = null;
    }
    
    // Clean up recenter timeout
    if (recenterTimeout) {
      clearTimeout(recenterTimeout);
      recenterTimeout = null;
    }
    
    // Clean up scroll timeout
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
      scrollTimeout = null;
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

<div class="app" class:graph-collapsed={graphCollapsed} class:graph-fullscreen={graphFullscreen} class:has-right-sidebar={!graphFullscreen && graphData?.nodes?.length > 0}>
  <!-- Cached Graph Dialog -->
  {#if showCachedGraphDialog}
    <div 
      class="modal-overlay" 
      role="button"
      tabindex="-1"
      aria-label="Close dialog"
      on:click|self={handleCancelCachedGraph}
      on:keydown={(e) => e.key === 'Escape' && handleCancelCachedGraph()}
    >
      <div class="modal-dialog" role="dialog" aria-labelledby="cached-graph-title" aria-modal="true">
        <h3 id="cached-graph-title">Load Cached Graph?</h3>
        <p>A cached graph from a previous session was found ({cachedGraphData?.nodes?.length || 0} nodes, {cachedGraphData?.links?.length || 0} edges).</p>
        <p>Would you like to load it or start fresh?</p>
        <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
          <Button variant="secondary" on:click={handleCancelCachedGraph} size="sm">
            Cancel
          </Button>
          <Button on:click={handleLoadCachedGraph} size="sm">
            Load Cached
          </Button>
        </div>
      </div>
    </div>
  {/if}

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
    <div class="graph-inner" style="position: relative;">
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
    
    <!-- Node Popup Modal -->
    {#if popupNode}
      <div class="node-popup-overlay" on:click={() => popupNode = null} on:keydown={(e) => e.key === 'Escape' && (popupNode = null)}>
        <div class="node-popup" on:click|stopPropagation>
          <div class="popup-header">
            <div class="popup-title">
              <strong>{popupNode.id || 'Unknown'}</strong>
              {#if popupNode.type}
                <span class="popup-type">{popupNode.type}</span>
              {/if}
            </div>
            <button class="popup-close" on:click={() => popupNode = null} title="Close (Esc)">
              ×
            </button>
          </div>
          <div class="popup-body">
            {#each Object.entries(popupNode).filter(([key]) => !key.startsWith('__') && key !== 'id' && key !== 'type' && key !== 'x' && key !== 'y' && key !== 'vx' && key !== 'vy' && key !== 'fx' && key !== 'fy' && key !== 'level' && key !== 'layoutType') as [key, value]}
              <div class="popup-row">
                <span class="popup-key">{key}:</span>
                <span class="popup-value">
                  {#if typeof value === 'object' && value !== null}
                    {#if Array.isArray(value)}
                      {value.length} items
                      {#if value.length > 0}
                        <div class="popup-array">
                          {#each value as item}
                            <div class="popup-array-item">{typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item)}</div>
                          {/each}
                        </div>
                      {/if}
                    {:else}
                      <div class="popup-object">
                        {#each Object.entries(value) as [subKey, subValue]}
                          <div class="popup-nested">
                            <span class="popup-key">{subKey}:</span>
                            <span class="popup-value">{typeof subValue === 'object' ? JSON.stringify(subValue, null, 2) : String(subValue)}</span>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  {:else}
                    {String(value)}
                  {/if}
                </span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Right Sidebar: Node Type Filter -->
  <div class="right-sidebar" class:hidden={graphFullscreen || !graphData?.nodes?.length}>
    {#if !graphFullscreen && graphData?.nodes?.length > 0}
      <NodeTypeFilter 
        graphData={graphData}
        enabledTypes={enabledNodeTypes}
        onToggleType={toggleNodeType}
      />
    {/if}
  </div>
</div>

