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

  let initialLoaded = false;

  onMount(async () => {
    await loadPlugins();
    await initCache();
    if (!initialLoaded) {
      await loadGraph();
    }
    initGraph();
    setupKeyboardShortcuts();
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
        .nodeLabel(node => `${node.id} (${node.type})`)
        .nodeColor(nodeColor)
        .linkLabel(link => `${link.type || 'RELATED_TO'}`)
        .linkColor(linkColor)
        .linkWidth(linkWidth)
        .linkDirectionalArrowLength(6)
        .linkDirectionalArrowRelPos(1)
        .onNodeClick(handleNodeClick)
        .onNodeHover((node) => {
          if (typeof document !== 'undefined' && document.body) {
            document.body.style.cursor = node ? 'pointer' : 'default';
          }
        })
        .nodeVal(node => {
          // Hide default circle for stacked nodes
          if (node.layoutType === 'stack') return 0;
          return Math.sqrt(Object.keys(node).length) * 3;
        })
        // draw type text on top of each node circle
        .nodeCanvasObjectMode((node) => {
          // For stacked nodes, replace the default circle entirely
          if (node.layoutType === 'stack') return 'replace';
          return 'after';
        })
        .nodeCanvasObject((node, ctx, globalScale) => {
          const typeRaw = (node.type || '').toString();
          if (!typeRaw) return;
          const typeLabel = typeRaw.charAt(0).toUpperCase() + typeRaw.slice(1);
          const fontSize = Math.max(3, 3 / globalScale) + 2; // scale-aware small label
          
          // Bloodweb-style glow effect
          const level = node.level || 0;
          const glowIntensity = Math.max(0.3, 1 - (level * 0.1));
          const layoutType = node.layoutType || 'circle';
          
          ctx.save();
          
          // Draw rounded rectangle for stack layout (replaces default circle)
          if (layoutType === 'stack') {
            const width = 100;
            const height = 35;
            const radius = 8;
            const x = node.x - width / 2;
            const y = node.y - height / 2;
            
            // Draw rounded rectangle background with gradient
            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();
            
            // Create gradient for depth
            const gradient = ctx.createLinearGradient(x, y, x, y + height);
            const color = nodeColor(node);
            gradient.addColorStop(0, color);
            gradient.addColorStop(1, color + '80'); // Darker at bottom
            
            // Fill with gradient
            ctx.fillStyle = gradient;
            ctx.globalAlpha = 0.9;
            ctx.fill();
            
            // Stroke with glow effect
            ctx.strokeStyle = nodeColor(node);
            ctx.lineWidth = 2.5;
            ctx.shadowBlur = 8;
            ctx.shadowColor = nodeColor(node);
            ctx.globalAlpha = 1;
            ctx.stroke();
            
            // Reset shadow for text
            ctx.shadowBlur = 0;
            
            // Text with better visibility
            ctx.font = `bold ${Math.max(10, fontSize + 1)}px Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial`;
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(typeLabel, node.x, node.y);
          } else {
            // Circle layout - original text rendering
            ctx.shadowBlur = 15;
            ctx.shadowColor = nodeColor(node);
            ctx.font = `${fontSize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial`;
            ctx.fillStyle = `rgba(255, 255, 255, ${glowIntensity})`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(typeLabel, node.x, node.y);
          }
          
          ctx.restore();
        })
        .backgroundColor('rgba(0,0,0,0)')
        .cooldownTicks(100)
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

  function updateGraphSize() {
    if (!graphInstance || !graphContainer) return;
    const w = graphContainer.clientWidth || 0;
    const h = graphContainer.clientHeight || 0;
    if (w > 0 && h > 0) {
      graphInstance.width(w).height(h);
    }
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
      graphData = {
        nodes: response.data.nodes || [],
        links: response.data.edges || []
      };
      updateGraph();
      try {
        await cacheManager.saveGraph(graphData);
      } catch (cacheError) {
        console.error('Failed to cache graph:', cacheError);
      }
    } catch (error) {
      showNotification('Failed to load graph: ' + error.message, 'error');
    } finally {
      loading = false;
    }
  }

  function calculateBloodwebLayout(data) {
    if (!data || !data.nodes || data.nodes.length === 0) return data;
    
    const nodeMap = new Map(data.nodes.map(n => [n.id, n]));
    const linkMap = new Map();
    
    // Build adjacency map
    data.links.forEach(link => {
      const source = typeof link.source === 'string' ? link.source : link.source.id;
      const target = typeof link.target === 'string' ? link.target : link.target.id;
      
      if (!linkMap.has(source)) linkMap.set(source, []);
      if (!linkMap.has(target)) linkMap.set(target, []);
      linkMap.get(source).push(target);
      linkMap.get(target).push(source);
    });
    
    // Find root: node with most connections, or first node
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
    const levels = new Map();
    const visited = new Set();
    const queue = [{ id: rootId, level: 0 }];
    levels.set(rootId, 0);
    visited.add(rootId);
    
    while (queue.length > 0) {
      const current = queue.shift();
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
    
    // Assign levels to all nodes (unconnected nodes get max level + 1)
    const maxLevel = Math.max(...Array.from(levels.values()), 0);
    data.nodes.forEach(node => {
      if (!levels.has(node.id)) {
        levels.set(node.id, maxLevel + 1);
      }
      node.level = levels.get(node.id);
    });
    
    // Group nodes by type for stack layout
    const stackableTypes = ['Certificate', 'Technology', 'Endpoint', 'WAF', 'NameServer'];
    const nodesByType = new Map();
    const circularNodes = [];
    const stackableNodes = [];
    
    data.nodes.forEach(node => {
      const nodeType = node.type || 'default';
      if (stackableTypes.includes(nodeType)) {
        if (!nodesByType.has(nodeType)) {
          nodesByType.set(nodeType, []);
        }
        nodesByType.get(nodeType).push(node);
        stackableNodes.push(node);
      } else {
        circularNodes.push(node);
      }
    });
    
    const centerX = 0;
    const centerY = 0;
    const baseRadius = 80;
    const radiusStep = 120;
    const stackSpacing = 100; // Vertical spacing for stacks
    const stackWidth = 200; // Width of each stack column
    
    // Position circular nodes in concentric circles (if not too many)
    const maxCircularNodes = 200; // Threshold for using circles
    if (circularNodes.length <= maxCircularNodes) {
      const nodesByLevel = new Map();
      circularNodes.forEach(node => {
        const level = node.level;
        if (!nodesByLevel.has(level)) {
          nodesByLevel.set(level, []);
        }
        nodesByLevel.get(level).push(node);
      });
      
      nodesByLevel.forEach((nodes, level) => {
        const radius = baseRadius + (level * radiusStep);
        const angleStep = nodes.length > 0 ? (2 * Math.PI) / nodes.length : 0;
        
        nodes.forEach((node, index) => {
          const angle = index * angleStep;
          node.fx = centerX + radius * Math.cos(angle);
          node.fy = centerY + radius * Math.sin(angle);
          node.layoutType = 'circle';
        });
      });
    } else {
      // Too many nodes for circles - use grid/force layout
      circularNodes.forEach((node, index) => {
        const level = node.level;
        const nodesInLevel = circularNodes.filter(n => n.level === level).length;
        const indexInLevel = circularNodes.filter(n => n.level === level && 
          circularNodes.indexOf(n) <= index).length - 1;
        
        // Use a spiral or grid pattern
        const cols = Math.ceil(Math.sqrt(nodesInLevel));
        const row = Math.floor(indexInLevel / cols);
        const col = indexInLevel % cols;
        const spacing = 150;
        
        node.fx = centerX + (col - cols/2) * spacing;
        node.fy = centerY + (row - nodesInLevel/cols/2) * spacing;
        node.layoutType = 'grid';
      });
    }
    
    // Position stackable nodes in vertical stacks (rounded rectangles)
    let stackXOffset = centerX + (circularNodes.length > 0 ? 
      (baseRadius + (maxLevel * radiusStep) + 200) : 0);
    let stackColumn = 0;
    const maxStacksPerColumn = 15;
    
    nodesByType.forEach((nodes, type) => {
      // Sort nodes by level or connections
      nodes.sort((a, b) => {
        const aLevel = a.level || 0;
        const bLevel = b.level || 0;
        if (aLevel !== bLevel) return aLevel - bLevel;
        return (linkMap.get(b.id)?.length || 0) - (linkMap.get(a.id)?.length || 0);
      });
      
      const stackIndex = stackColumn % maxStacksPerColumn;
      const columnIndex = Math.floor(stackColumn / maxStacksPerColumn);
      const xPos = stackXOffset + (columnIndex * (stackWidth + 50));
      
      nodes.forEach((node, index) => {
        const yPos = centerY - (nodes.length * stackSpacing / 2) + (index * stackSpacing);
        node.fx = xPos;
        node.fy = yPos;
        node.layoutType = 'stack';
        node.stackGroup = type;
      });
      
      stackColumn++;
    });
    
    // If we have many nodes, also use a hybrid approach for remaining nodes
    const totalNodes = data.nodes.length;
    if (totalNodes > 300) {
      // Use a more efficient layout for large graphs
      data.nodes.forEach(node => {
        if (!node.fx && !node.fy) {
          // Fallback: use level-based positioning
          const level = node.level || 0;
          const nodesInLevel = data.nodes.filter(n => (n.level || 0) === level).length;
          const indexInLevel = data.nodes.filter(n => (n.level || 0) === level && 
            data.nodes.indexOf(n) <= data.nodes.indexOf(node)).length - 1;
          
          if (nodesInLevel > 50) {
            // Too many in one level - use grid
            const cols = Math.ceil(Math.sqrt(nodesInLevel));
            const row = Math.floor(indexInLevel / cols);
            const col = indexInLevel % cols;
            const spacing = 120;
            node.fx = centerX + (col - cols/2) * spacing;
            node.fy = centerY + (row - nodesInLevel/cols/2) * spacing;
            node.layoutType = 'grid';
          } else {
            // Use circle for this level
            const radius = baseRadius + (level * radiusStep);
            const angleStep = (2 * Math.PI) / nodesInLevel;
            const angle = indexInLevel * angleStep;
            node.fx = centerX + radius * Math.cos(angle);
            node.fy = centerY + radius * Math.sin(angle);
            node.layoutType = 'circle';
          }
        }
      });
    }
    
    return data;
  }

  function updateGraph() {
    if (graphInstance) {
      const data = getFilteredGraphData();
      
      // Apply bloodweb layout
      const layoutData = calculateBloodwebLayout(JSON.parse(JSON.stringify(data)));
      
      graphInstance.graphData(layoutData);
      
      // Apply dynamic forces based on layout type
      graphInstance.d3Force('radial', d3.forceRadial()
        .strength(d => {
          // Only apply radial force to circular nodes
          if (d.layoutType === 'stack') return 0;
          return 0.9;
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
          if (d.layoutType === 'stack') {
            return 50; // Wider collision for stacked nodes
          }
          const size = d.__size || Math.sqrt(Object.keys(d).length) * 3 || 8;
          return size + 8;
        })
        .strength(d => {
          // Stronger collision for stacks to keep them aligned
          if (d.layoutType === 'stack') return 1.0;
          return 0.8;
        })
      )
      .d3Force('stack', d3.forceY()
        .strength(d => {
          // Keep stacked nodes in their vertical position
          if (d.layoutType === 'stack' && d.fy !== undefined) {
            return 0.8;
          }
          return 0;
        })
        .y(d => d.fy || 0)
      )
      .d3Force('stackX', d3.forceX()
        .strength(d => {
          // Keep stacked nodes in their horizontal position
          if (d.layoutType === 'stack' && d.fx !== undefined) {
            return 0.8;
          }
          return 0;
        })
        .x(d => d.fx || 0)
      )
      .d3Force('charge', d3.forceManyBody()
        .strength(d => {
          // Less repulsion for stacked nodes
          if (d.layoutType === 'stack') return -50;
          return -200;
        })
      )
      .d3Force('link', d3.forceLink().id(d => d.id).distance(d => {
        // Shorter links for same level, longer for different levels
        const sourceLevel = d.source.level || 0;
        const targetLevel = d.target.level || 0;
        const levelDiff = Math.abs(sourceLevel - targetLevel);
        
        // Different distances for different layout types
        if (d.source.layoutType === 'stack' || d.target.layoutType === 'stack') {
          return 100 + (levelDiff * 30);
        }
        return 60 + (levelDiff * 40);
      }).strength(0.6));
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

  function showNotification(message, type = 'info') {
    if (typeof document === 'undefined' || !document.body) return;
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      background: ${type === 'error' ? '#f44336' : '#4CAF50'};
      color: white;
      border-radius: 4px;
      z-index: 10000;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
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

  function nodeColor(node) {
    if (selectedNodes.includes(node.id)) return '#FFD700';
    if (highlightedPath && highlightedPath.includes(node.id)) return '#FFD700';
    if (diffGraph && node.change_type) {
      if (node.change_type === 'added') return '#4CAF50';
      if (node.change_type === 'removed') return '#f44336';
      if (node.change_type === 'changed') return '#FF9800';
    }
    
    // Bloodweb-style colors - darker, more atmospheric
    const level = node.level || 0;
    const colors = {
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
    
    const baseColor = colors[node.type] || colors['default'];
    
    // Darken nodes further from center (higher levels)
    if (level > 0) {
      const darkenFactor = Math.min(0.3, level * 0.05);
      // Simple darkening by reducing RGB values
      return baseColor; // Keep original for now, can enhance later
    }
    
    return baseColor;
  }

  function linkColor(link) {
    if (highlightedPath) {
      const sourceIdx = highlightedPath.indexOf(link.source.id);
      const targetIdx = highlightedPath.indexOf(link.target.id);
      if (sourceIdx !== -1 && targetIdx !== -1 && Math.abs(sourceIdx - targetIdx) === 1) {
        return '#FFD700';
      }
    }
    
    // Bloodweb-style links - darker, web-like
    const sourceLevel = link.source?.level || 0;
    const targetLevel = link.target?.level || 0;
    const levelDiff = Math.abs(sourceLevel - targetLevel);
    
    // Darker links for connections between different levels (web-like)
    if (levelDiff > 0) {
      return `rgba(139, 0, 0, ${0.4 - levelDiff * 0.1})`; // Dark red, fading
    }
    
    // Lighter links for same-level connections
    return 'rgba(139, 69, 19, 0.3)'; // Saddle brown, subtle
  }

  function linkWidth(link) {
    if (highlightedPath) {
      const sourceIdx = highlightedPath.indexOf(link.source.id);
      const targetIdx = highlightedPath.indexOf(link.target.id);
      if (sourceIdx !== -1 && targetIdx !== -1 && Math.abs(sourceIdx - targetIdx) === 1) {
        return 4;
      }
    }
    return 2;
  }

  function getFilteredGraphData() {
    if (queryFilter) {
      return {
        nodes: queryFilter.nodes || [],
        links: queryFilter.edges || []
      };
    }
    if (filteredNodes) {
      return {
        nodes: graphData.nodes.filter(n => filteredNodes.includes(n.id)),
        links: graphData.links.filter(l => 
          filteredNodes.includes(l.source.id || l.source) && 
          filteredNodes.includes(l.target.id || l.target)
        )
      };
    }
    return graphData;
  }

  $: if (graphInstance && graphData) {
    updateGraph();
  }

  // re-measure after collapsing/expanding
  $: if (graphCollapsed !== undefined) {
    if (typeof window !== 'undefined') {
      setTimeout(updateGraphSize, 50);
    }
  }

  onDestroy(() => {
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
  <div class="sidebar" class:hidden={graphFullscreen}>
    <div class="sidebar-header" style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
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

    <div class="sidebar-section" style="padding: 10px 0; border-bottom: 1px solid #444;">
      <HistoryControls onHistoryChange={(graph) => {
        if (graph) {
          graphData = {
            nodes: graph.nodes || [],
            links: graph.edges || []
          };
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
          <i
            class="bi bi-keyboard icon-action"
            title="Keyboard shortcuts"
            on:click={() => (showShortcuts = true)}
          ></i>
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

