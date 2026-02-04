"""
Advanced search and filtering module
Provides regex-based, fuzzy matching, and full-text search capabilities
"""
import re
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class AdvancedSearch:
    """Advanced search and filtering capabilities"""
    
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
    
    def search_regex(self, pattern: str, node_type: Optional[str] = None,
                     search_fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Search nodes using regex pattern matching
        
        Args:
            pattern: Regex pattern to match
            node_type: Optional node type filter
            search_fields: Optional list of fields to search (default: all string fields)
            
        Returns:
            List of matching nodes
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {str(e)}")
            return []
        
        results = []
        nodes = self.graph_engine.get_nodes(node_type)
        
        for node in nodes:
            if self._matches_regex(node, regex, search_fields):
                results.append(node)
        
        return results
    
    def search_fuzzy(self, query: str, node_type: Optional[str] = None,
                    threshold: float = 0.6, limit: int = 50) -> List[Dict]:
        """
        Search nodes using fuzzy matching (similar to Ctrl+F in editors)
        
        Args:
            query: Search query string
            node_type: Optional node type filter
            threshold: Similarity threshold (0-1, default 0.6)
            limit: Maximum results to return
            
        Returns:
            List of nodes with fuzzy match scores, sorted by relevance
        """
        nodes = self.graph_engine.get_nodes(node_type)
        scored_matches = []
        
        for node in nodes:
            score = self._fuzzy_match_node(node, query)
            if score >= threshold:
                scored_matches.append({
                    **node,
                    "_fuzzy_score": score
                })
        
        # Sort by score (highest first)
        scored_matches.sort(key=lambda x: x["_fuzzy_score"], reverse=True)
        return scored_matches[:limit]
    
    def search_full_text(self, query: str, node_type: Optional[str] = None,
                         case_sensitive: bool = False, limit: int = 50) -> List[Dict]:
        """
        Full-text search across all node properties
        
        Args:
            query: Search query (supports multiple terms)
            node_type: Optional node type filter
            case_sensitive: Whether to use case-sensitive matching
            limit: Maximum results to return
            
        Returns:
            List of matching nodes
        """
        terms = query.split()
        nodes = self.graph_engine.get_nodes(node_type)
        results = []
        
        for node in nodes:
            node_text = self._node_to_text(node)
            if not case_sensitive:
                node_text = node_text.lower()
                search_terms = [t.lower() for t in terms]
            else:
                search_terms = terms
            
            # Node matches if it contains ALL search terms
            if all(term in node_text for term in search_terms):
                results.append(node)
        
        return results[:limit]
    
    def search_complex_filter(self, filters: Dict[str, Any]) -> List[Dict]:
        """
        Complex filtering using AND/OR/NOT logic
        
        Supported filter structure:
        {
            "and": [filter1, filter2],  # All must match
            "or": [filter1, filter2],   # Any must match
            "not": filter,              # Must not match
            "field": "value",           # Direct field match
            "field_regex": "pattern",   # Regex on field
            "field_fuzzy": {"query": "term", "threshold": 0.7}
        }
        
        Args:
            filters: Filter specification dictionary
            
        Returns:
            List of matching nodes
        """
        nodes = self.graph_engine.get_nodes()
        return [n for n in nodes if self._matches_filter(n, filters)]
    
    def _matches_regex(self, node: Dict, regex: re.Pattern,
                       search_fields: Optional[List[str]] = None) -> bool:
        """Check if node matches regex pattern"""
        if search_fields:
            # Search only specified fields
            for field in search_fields:
                value = node.get(field, "")
                if regex.search(str(value)):
                    return True
            return False
        else:
            # Search all fields
            for key, value in node.items():
                if isinstance(value, (str, int, float)):
                    if regex.search(str(value)):
                        return True
            return False
    
    def _fuzzy_match_node(self, node: Dict, query: str) -> float:
        """
        Calculate fuzzy match score for a node (0-1)
        Score is based on similarity with node ID and all string properties
        """
        node_text = self._node_to_text(node).lower()
        query_lower = query.lower()
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, query_lower, node_text).ratio()
        
        # Boost score if query matches node ID
        if "id" in node:
            id_similarity = SequenceMatcher(None, query_lower, str(node["id"]).lower()).ratio()
            similarity = max(similarity, id_similarity * 1.5)  # Boost ID matches
        
        return min(similarity, 1.0)  # Clamp to [0, 1]
    
    def _node_to_text(self, node: Dict) -> str:
        """Convert node to searchable text"""
        text_parts = []
        for key, value in node.items():
            if not key.startswith("_"):  # Skip internal fields
                text_parts.append(str(value))
        return " ".join(text_parts)
    
    def _matches_filter(self, node: Dict, filters: Dict[str, Any]) -> bool:
        """Recursively check if node matches complex filter"""
        # AND: all conditions must match
        if "and" in filters:
            return all(self._matches_filter(node, f) for f in filters["and"])
        
        # OR: at least one condition must match
        if "or" in filters:
            return any(self._matches_filter(node, f) for f in filters["or"])
        
        # NOT: condition must not match
        if "not" in filters:
            return not self._matches_filter(node, filters["not"])
        
        # Direct field match
        for key, value in filters.items():
            if not key.endswith("_regex") and not key.endswith("_fuzzy") and key not in ["and", "or", "not"]:
                if node.get(key) != value:
                    return False
        
        # Regex matches (e.g., "name_regex": "pattern")
        for key in filters:
            if key.endswith("_regex"):
                field = key[:-6]  # Remove "_regex" suffix
                try:
                    regex = re.compile(filters[key], re.IGNORECASE)
                    if not regex.search(str(node.get(field, ""))):
                        return False
                except re.error:
                    return False
        
        # Fuzzy matches (e.g., "name_fuzzy": {"query": "term", "threshold": 0.7})
        for key in filters:
            if key.endswith("_fuzzy"):
                field = key[:-6]  # Remove "_fuzzy" suffix
                fuzzy_config = filters[key]
                query = fuzzy_config.get("query", "")
                threshold = fuzzy_config.get("threshold", 0.6)
                
                # Create a temporary node with just this field for scoring
                field_node = {field: node.get(field, "")}
                score = self._fuzzy_match_node(field_node, query)
                if score < threshold:
                    return False
        
        return True
