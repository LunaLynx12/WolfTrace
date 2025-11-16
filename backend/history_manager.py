"""
History Manager - Undo/Redo functionality for graph operations
"""
from typing import List, Dict, Any, Optional
from collections import deque

class HistoryManager:
    def __init__(self, max_history: int = 50):
        """
        Initialize history manager
        
        Args:
            max_history: Maximum number of history entries
        """
        self.max_history = max_history
        self.undo_stack: deque = deque(maxlen=max_history)
        self.redo_stack: deque = deque(maxlen=max_history)
        self.current_state: Optional[Dict] = None
    
    def save_state(self, graph_data: Dict[str, Any], operation: str = 'unknown'):
        """
        Save current graph state to history
        
        Args:
            graph_data: Current graph data (nodes and edges)
            operation: Description of the operation that led to this state
        """
        # Serialize graph data
        state = {
            'graph': {
                'nodes': graph_data.get('nodes', []),
                'edges': graph_data.get('edges', [])
            },
            'operation': operation,
            'timestamp': None  # Can add timestamp if needed
        }
        
        # If we have a current state, add it to undo stack
        if self.current_state is not None:
            self.undo_stack.append(self.current_state)
            # Clear redo stack when new action is performed
            self.redo_stack.clear()
        
        self.current_state = state
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Undo last operation
        
        Returns:
            Previous graph state or None if nothing to undo
        """
        if not self.undo_stack:
            return None
        
        # Move current state to redo stack
        if self.current_state:
            self.redo_stack.append(self.current_state)
        
        # Get previous state
        self.current_state = self.undo_stack.pop()
        return self.current_state.get('graph')
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """
        Redo last undone operation
        
        Returns:
            Next graph state or None if nothing to redo
        """
        if not self.redo_stack:
            return None
        
        # Move current state to undo stack
        if self.current_state:
            self.undo_stack.append(self.current_state)
        
        # Get next state
        self.current_state = self.redo_stack.pop()
        return self.current_state.get('graph')
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def get_history_info(self) -> Dict[str, Any]:
        """Get information about history state"""
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'current_operation': self.current_state.get('operation') if self.current_state else None
        }
    
    def clear(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_state = None

