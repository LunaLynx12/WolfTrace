<script>
  import axios from 'axios';
  import * as d3 from 'd3';
  import Button from './ui/Button.svelte';
  import { showNotification } from '../utils/notifications.js';

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  export let graphData;
  export let graphInstance;
  
  // Performance: Move color map to top-level constant to avoid recreating on every render
  const NODE_COLORS_EXPORT = {
    'Entity': '#4CAF50',
    'Host': '#2196F3',
    'ec2': '#FF9800',
    'Resource': '#9C27B0',
    'default': '#607D8B'
  };

  async function exportGraph(format) {
    try {
      if (format === 'json') {
        const response = await axios.get(`${API_BASE}/export`, {
          params: { format: 'json' }
        });
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-graph-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
      } else if (format === 'png') {
        exportAsPNG();
      } else if (format === 'svg') {
        exportAsSVG();
      }
    } catch (error) {
      showNotification(`Export failed: ${error.message}`, 'error');
    }
  }

  function exportAsPNG() {
    if (!graphInstance) {
      showNotification('Graph not available for export', 'error');
      return;
    }

    try {
      // Get the canvas from force-graph
      const canvas = graphInstance.getGraph2dCanvas();
      if (!canvas) {
        showNotification('Canvas not available', 'error');
        return;
      }

      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-graph-${Date.now()}.png`;
        link.click();
        URL.revokeObjectURL(url);
        showNotification('PNG exported successfully', 'success');
      }, 'image/png');
    } catch (error) {
      showNotification(`PNG export failed: ${error.message}`, 'error');
    }
  }

  function exportAsSVG() {
    if (!graphData || !graphData.nodes) {
      showNotification('No graph data to export', 'error');
      return;
    }

    try {
      const width = 1200;
      const height = 800;
      const svg = d3.create('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('xmlns', 'http://www.w3.org/2000/svg')
        .style('background', '#1a1a1a');

      const g = svg.append('g');

      // Performance: Use existing node positions from graphInstance if available
      // This avoids creating a new force simulation and blocking the UI
      const nodesWithPositions = graphData.nodes.map(node => {
        // If graphInstance exists and node has x/y, use those positions
        if (graphInstance && node.x !== undefined && node.y !== undefined) {
          return {
            ...node,
            x: node.x + width / 2, // Center the positions
            y: node.y + height / 2
          };
        }
        return node;
      });

      // Only create simulation if nodes don't have positions
      const hasPositions = nodesWithPositions.every(n => n.x !== undefined && n.y !== undefined);
      
      let simulation = null;
      if (!hasPositions) {
        simulation = d3.forceSimulation(nodesWithPositions)
          .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100))
          .force('charge', d3.forceManyBody().strength(-300))
          .force('center', d3.forceCenter(width / 2, height / 2));
      }

      const links = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('stroke', 'rgba(255,255,255,0.2)')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)');

      const nodes = g.append('g')
        .selectAll('circle')
        .data(nodesWithPositions)
        .enter().append('circle')
        .attr('r', 8)
        .attr('fill', (d) => {
          // Performance: Use top-level constant instead of creating object
          return NODE_COLORS_EXPORT[d.type] || NODE_COLORS_EXPORT['default'];
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);

      const labels = g.append('g')
        .selectAll('text')
        .data(nodesWithPositions)
        .enter().append('text')
        .text(d => d.id)
        .attr('font-size', '12px')
        .attr('fill', '#e0e0e0')
        .attr('dx', 10)
        .attr('dy', 4);

      svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', 'rgba(255,255,255,0.2)');

      // Performance: Only run simulation if needed, otherwise use existing positions
      if (simulation) {
        simulation.on('tick', () => {
          links
            .attr('x1', d => {
              const source = typeof d.source === 'object' ? d.source : nodesWithPositions.find(n => n.id === d.source);
              return source?.x || width / 2;
            })
            .attr('y1', d => {
              const source = typeof d.source === 'object' ? d.source : nodesWithPositions.find(n => n.id === d.source);
              return source?.y || height / 2;
            })
            .attr('x2', d => {
              const target = typeof d.target === 'object' ? d.target : nodesWithPositions.find(n => n.id === d.target);
              return target?.x || width / 2;
            })
            .attr('y2', d => {
              const target = typeof d.target === 'object' ? d.target : nodesWithPositions.find(n => n.id === d.target);
              return target?.y || height / 2;
            });

          nodes
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

          labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
        });

        // Performance: Wait for simulation to actually settle instead of fixed timeout
        let exportCalled = false;
        const doExport = () => {
          if (!exportCalled) {
            exportCalled = true;
            exportSVG();
          }
        };
        
        // Listen for simulation end event
        simulation.on('end', doExport);
        
        // Also check alpha decay - when simulation settles
        const checkAlpha = () => {
          if (simulation && simulation.alpha() < 0.01) {
            simulation.stop();
            doExport();
          } else if (simulation) {
            requestAnimationFrame(checkAlpha);
          }
        };
        checkAlpha();
        
        // Fallback timeout (max 3 seconds)
        setTimeout(() => {
          if (simulation && !exportCalled) {
            simulation.stop();
            doExport();
          }
        }, 3000);
      } else {
        // Use existing positions immediately
        links
          .attr('x1', d => {
            const source = typeof d.source === 'object' ? d.source : nodesWithPositions.find(n => n.id === d.source);
            return source?.x || width / 2;
          })
          .attr('y1', d => {
            const source = typeof d.source === 'object' ? d.source : nodesWithPositions.find(n => n.id === d.source);
            return source?.y || height / 2;
          })
          .attr('x2', d => {
            const target = typeof d.target === 'object' ? d.target : nodesWithPositions.find(n => n.id === d.target);
            return target?.x || width / 2;
          })
          .attr('y2', d => {
            const target = typeof d.target === 'object' ? d.target : nodesWithPositions.find(n => n.id === d.target);
            return target?.y || height / 2;
          });

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);

        labels
          .attr('x', d => d.x)
          .attr('y', d => d.y);

        // Export immediately since we have positions
        exportSVG();
      }

      function exportSVG() {
        const svgString = new XMLSerializer().serializeToString(svg.node());
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-graph-${Date.now()}.svg`;
        link.click();
        URL.revokeObjectURL(url);
        showNotification('SVG exported successfully', 'success');
      }
    } catch (error) {
      showNotification(`SVG export failed: ${error.message}`, 'error');
    }
  }
</script>

<div class="export-buttons">
  <Button variant="primary" on:click={() => exportGraph('json')}>
    Export JSON
  </Button>
  <Button variant="primary" on:click={() => exportGraph('png')}>
    Export PNG
  </Button>
  <Button variant="primary" on:click={() => exportGraph('svg')}>
    Export SVG
  </Button>
</div>

