"""
Session Manager - Handles saving and loading graph sessions
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class SessionManager:
    def __init__(self, sessions_dir: str = None):
        """
        Initialize session manager
        
        Args:
            sessions_dir: Directory to store session files (default: backend/data/sessions)
        """
        if sessions_dir is None:
            # Default to backend/data/sessions relative to this file
            backend_dir = Path(__file__).resolve().parent
            sessions_dir = str(backend_dir / 'data' / 'sessions')
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session_name: str, graph_data: Dict, metadata: Dict = None) -> Dict:
        """
        Save a graph session
        
        Args:
            session_name: Name for the session
            graph_data: Graph data (nodes and edges)
            metadata: Optional metadata (description, tags, etc.)
        
        Returns:
            Session info
        """
        if not session_name:
            raise ValueError("Session name is required")
        
        session_id = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_file = self.sessions_dir / f"{session_id}.json"
        
        session_data = {
            'id': session_id,
            'name': session_name,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'graph': graph_data
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return {
            'id': session_id,
            'name': session_name,
            'created_at': session_data['created_at'],
            'file': str(session_file)
        }
    
    def load_session(self, session_id: str) -> Dict:
        """
        Load a graph session
        
        Args:
            session_id: Session ID or filename
        
        Returns:
            Session data
        """
        # Try exact match first
        session_file = self.sessions_dir / f"{session_id}.json"
        
        # If not found, try to find by partial match
        if not session_file.exists():
            matching_files = list(self.sessions_dir.glob(f"*{session_id}*.json"))
            if matching_files:
                session_file = matching_files[0]
            else:
                raise FileNotFoundError(f"Session '{session_id}' not found")
        
        with open(session_file, 'r') as f:
            return json.load(f)
    
    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """
        List all saved sessions
        
        Args:
            limit: Maximum number of sessions to return
        
        Returns:
            List of session info
        """
        sessions = []
        for session_file in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        'id': data.get('id', session_file.stem),
                        'name': data.get('name', session_file.stem),
                        'created_at': data.get('created_at'),
                        'metadata': data.get('metadata', {}),
                        'node_count': len(data.get('graph', {}).get('nodes', [])),
                        'edge_count': len(data.get('graph', {}).get('edges', []))
                    })
            except Exception as e:
                print(f"Error reading session {session_file}: {e}")
        
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
        
        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False

