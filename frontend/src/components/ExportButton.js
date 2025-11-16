import React, { useRef } from 'react';
import axios from 'axios';
import * as d3 from 'd3';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function ExportButton({ graphData, graphRef }) {
  const exportGraph = async (format) => {
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
      alert(`Export failed: ${error.message}`);
    }
  };

  const exportAsPNG = () => {
    if (!graphRef || !graphRef.current) {
      alert('Graph not available for export');
      return;
    }

    try {
      const canvas = graphRef.current.getGraph2dCanvas();
      if (!canvas) {
        alert('Canvas not available');
        return;
      }

      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-graph-${Date.now()}.png`;
        link.click();
        URL.revokeObjectURL(url);
      }, 'image/png');
    } catch (error) {
      alert(`PNG export failed: ${error.message}`);
    }
  };

  const exportAsSVG = () => {
    if (!graphData || !graphData.nodes) {
      alert('No graph data to export');
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

      // Create a group for the graph
      const g = svg.append('g');

      // Simple force simulation for layout
      const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

      // Draw links
      const links = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('stroke', 'rgba(255,255,255,0.2)')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)');

      // Draw nodes
      const nodes = g.append('g')
        .selectAll('circle')
        .data(graphData.nodes)
        .enter().append('circle')
        .attr('r', 8)
        .attr('fill', (d) => {
          const colors = {
            'Entity': '#4CAF50',
            'Host': '#2196F3',
            'ec2': '#FF9800',
            'Resource': '#9C27B0',
            'default': '#607D8B'
          };
          return colors[d.type] || colors['default'];
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);

      // Add labels
      const labels = g.append('g')
        .selectAll('text')
        .data(graphData.nodes)
        .enter().append('text')
        .text(d => d.id)
        .attr('font-size', '12px')
        .attr('fill', '#e0e0e0')
        .attr('dx', 10)
        .attr('dy', 4);

      // Add arrow marker
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

      // Run simulation
      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);

        labels
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      });

      // Wait for simulation to settle
      setTimeout(() => {
        simulation.stop();
        const svgString = new XMLSerializer().serializeToString(svg.node());
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolftrace-graph-${Date.now()}.svg`;
        link.click();
        URL.revokeObjectURL(url);
      }, 1000);
    } catch (error) {
      alert(`SVG export failed: ${error.message}`);
    }
  };

  return (
    <div className="export-buttons">
      <button onClick={() => exportGraph('json')} className="btn-export">
        Export JSON
      </button>
      <button onClick={() => exportGraph('png')} className="btn-export">
        Export PNG
      </button>
      <button onClick={() => exportGraph('svg')} className="btn-export">
        Export SVG
      </button>
    </div>
  );
}

export default ExportButton;

