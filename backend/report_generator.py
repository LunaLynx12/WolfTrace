"""
Report Generator - Generate PDF reports from graph data
"""
from typing import Dict, List, Any
from datetime import datetime
import json

class ReportGenerator:
    def __init__(self, graph_engine, analytics):
        self.graph_engine = graph_engine
        self.analytics = analytics
    
    def generate_report_data(self, include_graph: bool = True) -> Dict[str, Any]:
        """
        Generate report data structure
        
        Args:
            include_graph: Whether to include full graph data
        
        Returns:
            Report data dictionary
        """
        stats = self.analytics.get_statistics()
        graph_data = self.graph_engine.get_full_graph() if include_graph else None
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0'
            },
            'summary': {
                'total_nodes': stats.get('basic', {}).get('nodes', 0),
                'total_edges': stats.get('basic', {}).get('edges', 0),
                'node_types': stats.get('node_types', {}),
                'edge_types': stats.get('edge_types', {}),
                'connected_components': stats.get('basic', {}).get('connected_components', 0),
                'is_connected': stats.get('is_connected', False)
            },
            'analytics': {
                'top_nodes_by_degree': stats.get('top_nodes_by_degree', [])[:10],
                'top_nodes_by_betweenness': stats.get('top_nodes_by_betweenness', [])[:10],
                'node_type_distribution': stats.get('node_types', {}),
                'edge_type_distribution': stats.get('edge_types', {})
            }
        }
        
        if graph_data:
            report['graph'] = graph_data
        
        return report
    
    def generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML report from report data"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WolfTrace Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #4CAF50; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .section {{ margin: 30px 0; }}
        .metadata {{ color: #888; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>WolfTrace Graph Analysis Report</h1>
        <div class="metadata">Generated: {report_data['metadata']['generated_at']}</div>
        
        <div class="section">
            <h2>Summary</h2>
            <div class="summary">
                <div class="stat-card">
                    <div class="stat-value">{report_data['summary']['total_nodes']}</div>
                    <div class="stat-label">Total Nodes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['summary']['total_edges']}</div>
                    <div class="stat-label">Total Edges</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['summary']['connected_components']}</div>
                    <div class="stat-label">Components</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{'Yes' if report_data['summary']['is_connected'] else 'No'}</div>
                    <div class="stat-label">Connected</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Node Type Distribution</h2>
            <table>
                <tr><th>Node Type</th><th>Count</th></tr>
"""
        
        for node_type, count in report_data['summary']['node_types'].items():
            html += f"<tr><td>{node_type}</td><td>{count}</td></tr>"
        
        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Edge Type Distribution</h2>
            <table>
                <tr><th>Edge Type</th><th>Count</th></tr>
"""
        
        for edge_type, count in report_data['summary']['edge_types'].items():
            html += f"<tr><td>{edge_type}</td><td>{count}</td></tr>"
        
        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Top Nodes by Degree Centrality</h2>
            <table>
                <tr><th>Node ID</th><th>Centrality</th></tr>
"""
        
        for node in report_data['analytics']['top_nodes_by_degree']:
            html += f"<tr><td>{node['id']}</td><td>{node['centrality']:.4f}</td></tr>"
        
        html += """
            </table>
        </div>
"""
        
        if report_data['analytics']['top_nodes_by_betweenness']:
            html += """
        <div class="section">
            <h2>Top Nodes by Betweenness Centrality</h2>
            <table>
                <tr><th>Node ID</th><th>Centrality</th></tr>
"""
            for node in report_data['analytics']['top_nodes_by_betweenness']:
                html += f"<tr><td>{node['id']}</td><td>{node['centrality']:.4f}</td></tr>"
            html += """
            </table>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def generate_json_report(self, report_data: Dict) -> str:
        """Generate JSON report"""
        return json.dumps(report_data, indent=2)

