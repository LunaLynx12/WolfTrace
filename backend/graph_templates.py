"""
Graph Templates - Predefined graph structures and patterns
"""
from typing import Dict, List, Any
import json
from pathlib import Path

class GraphTemplates:
    def __init__(self, templates_dir: str = None):
        """
        Initialize template manager
        
        Args:
            templates_dir: Directory containing template files (default: backend/data/templates)
        """
        if templates_dir is None:
            # Default to backend/data/templates relative to this file
            backend_dir = Path(__file__).resolve().parent
            templates_dir = str(backend_dir / 'data' / 'templates')
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from directory"""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template_id = template_data.get('id', template_file.stem)
                    self.templates[template_id] = template_data
            except Exception as e:
                print(f"Failed to load template {template_file}: {e}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                'id': template.get('id'),
                'name': template.get('name', 'Unnamed'),
                'description': template.get('description', ''),
                'category': template.get('category', 'general'),
                'node_count': len(template.get('nodes', [])),
                'edge_count': len(template.get('edges', []))
            }
            for template in self.templates.values()
        ]
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific template"""
        return self.templates.get(template_id)
    
    def create_from_template(self, template_id: str, graph_engine, variables: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Create graph from template
        
        Args:
            template_id: ID of template to use
            graph_engine: GraphEngine instance
            variables: Variable substitutions (e.g., {'domain': 'corp.local'})
        
        Returns:
            Creation result with stats
        """
        template = self.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} not found'}
        
        variables = variables or {}
        nodes_added = 0
        edges_added = 0
        
        # Process nodes
        for node_template in template.get('nodes', []):
            node_id = self._substitute_variables(node_template.get('id', ''), variables)
            node_type = self._substitute_variables(node_template.get('type', 'Entity'), variables)
            properties = node_template.get('properties', {})
            
            # Substitute variables in properties
            processed_properties = {}
            for key, value in properties.items():
                if isinstance(value, str):
                    processed_properties[key] = self._substitute_variables(value, variables)
                else:
                    processed_properties[key] = value
            
            graph_engine.add_node(node_id, node_type, processed_properties)
            nodes_added += 1
        
        # Process edges
        for edge_template in template.get('edges', []):
            source = self._substitute_variables(edge_template.get('source', ''), variables)
            target = self._substitute_variables(edge_template.get('target', ''), variables)
            edge_type = edge_template.get('type', 'RELATED_TO')
            properties = edge_template.get('properties', {})
            
            # Substitute variables in properties
            processed_properties = {}
            for key, value in properties.items():
                if isinstance(value, str):
                    processed_properties[key] = self._substitute_variables(value, variables)
                else:
                    processed_properties[key] = value
            
            graph_engine.add_edge(source, target, edge_type, processed_properties)
            edges_added += 1
        
        return {
            'template_id': template_id,
            'template_name': template.get('name'),
            'nodes_added': nodes_added,
            'edges_added': edges_added,
            'status': 'success'
        }
    
    def save_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new template"""
        template_id = template_data.get('id')
        if not template_id:
            return {'error': 'Template ID is required'}
        
        template_file = self.templates_dir / f"{template_id}.json"
        
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # Reload templates
        self._load_templates()
        
        return {
            'template_id': template_id,
            'status': 'saved'
        }
    
    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Substitute variables in text (e.g., {domain} -> 'corp.local')"""
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result

