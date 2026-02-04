"""
Session Manager - Handles saving and loading graph sessions
Enhanced with versioning, compression, metadata search, and cleanup
"""
import json
import os
import gzip
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, sessions_dir: str = None, enable_compression: bool = True):
        """
        Initialize session manager
        
        Args:
            sessions_dir: Directory to store session files (default: backend/data/sessions)
            enable_compression: Enable gzip compression for sessions (default: True)
        """
        if sessions_dir is None:
            # Default to backend/data/sessions relative to this file
            backend_dir = Path(__file__).resolve().parent
            sessions_dir = str(backend_dir / 'data' / 'sessions')
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.enable_compression = enable_compression
        self.session_versions: Dict[str, int] = {}  # Track versions
        self._load_session_versions()
    
    def _load_session_versions(self) -> None:
        """Load session version information from metadata"""
        versions_file = self.sessions_dir / ".session_versions.json"
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    self.session_versions = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load session versions: {str(e)}")
    
    def _save_session_versions(self) -> None:
        """Save session version information"""
        versions_file = self.sessions_dir / ".session_versions.json"
        try:
            with open(versions_file, 'w') as f:
                json.dump(self.session_versions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session versions: {str(e)}")
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data)
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress gzip data"""
        return gzip.decompress(data)
    
    def _get_file_extension(self) -> str:
        """Get file extension based on compression setting"""
        return ".json.gz" if self.enable_compression else ".json"
    
    def save_session(self, session_name: str, graph_data: Dict, metadata: Dict = None) -> Dict:
        """
        Save a graph session with versioning and optional compression
        
        Args:
            session_name: Name for the session
            graph_data: Graph data (nodes and edges)
            metadata: Optional metadata (description, tags, etc.)
        
        Returns:
            Session info with version
        """
        if not session_name:
            raise ValueError("Session name is required")
        
        # Generate a clean session ID separate from filename
        import uuid
        session_id = str(uuid.uuid4())[:8]
        file_name = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Increment version for this session base
        base_name = session_name
        if base_name not in self.session_versions:
            self.session_versions[base_name] = 1
        else:
            self.session_versions[base_name] += 1
        
        version = self.session_versions[base_name]
        self._save_session_versions()
        
        # Calculate file size (before compression)
        session_data = {
            'id': session_id,
            'name': session_name,
            'file_name': file_name,
            'version': version,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'graph': graph_data
        }
        
        json_str = json.dumps(session_data, indent=2)
        data_bytes = json_str.encode('utf-8')
        uncompressed_size = len(data_bytes)
        
        # Apply compression if enabled
        if self.enable_compression:
            data_bytes = self._compress_data(data_bytes)
        
        # Write to file using the separate file_name
        session_file = self.sessions_dir / f"{file_name}{self._get_file_extension()}"
        
        try:
            with open(session_file, 'wb') as f:
                f.write(data_bytes)
            
            compressed_size = len(data_bytes)
            compression_ratio = (1 - compressed_size / uncompressed_size) * 100 if self.enable_compression else 0
            
            logger.info(
                f"Saved session {session_id} (file: {file_name}) v{version} "
                f"({uncompressed_size} bytes, compressed to {compressed_size} bytes, {compression_ratio:.1f}% reduction)"
            )
            
            return {
                'id': session_id,
                'name': session_name,
                'file_name': file_name,
                'version': version,
                'created_at': session_data['created_at'],
                'file': str(session_file),
                'size': compressed_size,
                'uncompressed_size': uncompressed_size,
                'compressed': self.enable_compression
            }
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {str(e)}")
            raise
    
    def load_session(self, session_id: str) -> Dict:
        """
        Load a graph session by ID, filename, or partial match.
        Handles both compressed and uncompressed formats.
        
        Args:
            session_id: Session ID (UUID), filename, or partial identifier
        
        Returns:
            Session data with 'id', 'name', 'file_name', 'version', etc.
        """
        session_file = None
        
        # Try 1: exact filename match (both compressed and uncompressed)
        session_file_gz = self.sessions_dir / f"{session_id}.json.gz"
        session_file_json = self.sessions_dir / f"{session_id}.json"
        
        if session_file_gz.exists():
            session_file = session_file_gz
        elif session_file_json.exists():
            session_file = session_file_json
        
        # Try 2: partial filename match (e.g., session_id is part of filename)
        if not session_file:
            matching_files = list(self.sessions_dir.glob(f"*{session_id}*.json.gz"))
            if matching_files:
                session_file = matching_files[0]
            else:
                matching_files = list(self.sessions_dir.glob(f"*{session_id}*.json"))
                if matching_files:
                    session_file = matching_files[0]
        
        # Try 3: search by session ID field in all files (fallback for UUID lookup)
        if not session_file:
            try:
                all_files = list(self.sessions_dir.glob("*.json.gz")) + list(self.sessions_dir.glob("*.json"))
                logger.debug(f"Searching {len(all_files)} session files for ID '{session_id}'")
                for session_file_path in all_files:
                    try:
                        with open(session_file_path, 'rb') as f:
                            data_bytes = f.read()
                        
                        # Decompress if needed
                        if session_file_path.suffix == '.gz':
                            data_bytes = self._decompress_data(data_bytes)
                        
                        json_str = data_bytes.decode('utf-8')
                        session_data = json.loads(json_str)
                        
                        # Check if this session matches the ID
                        if session_data.get('id') == session_id:
                            session_file = session_file_path
                            break
                    except Exception:
                        # Skip files that can't be read
                        continue
            except Exception:
                pass
        
        if not session_file:
            raise FileNotFoundError(f"Session '{session_id}' not found")
        
        try:
            with open(session_file, 'rb') as f:
                data_bytes = f.read()
            
            # Decompress if needed
            if session_file.suffix == '.gz':
                data_bytes = self._decompress_data(data_bytes)
            
            json_str = data_bytes.decode('utf-8')
            session_data = json.loads(json_str)
            
            logger.info(f"Loaded session {session_data.get('id', session_id)} (file: {session_file.name}) v{session_data.get('version', 'unknown')}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            raise
    
    def list_sessions(self, filters: Dict = None, limit: int = 50) -> List[Dict]:
        """
        List all saved sessions with optional metadata filtering
        
        Args:
            filters: Optional dict with keys like 'name', 'min_size', 'max_size', 
                    'created_after', 'created_before', 'modified_after', 'modified_before'
            limit: Maximum number of sessions to return
        
        Returns:
            List of session metadata sorted by modification date
        """
        sessions = []
        
        # Include both .json and .json.gz files
        all_files = list(self.sessions_dir.glob("*.json")) + list(self.sessions_dir.glob("*.json.gz"))
        
        for session_file in all_files:
            # Skip duplicate entries (e.g., both .json and .json.gz versions)
            base_name = session_file.stem
            if base_name.endswith('.json'):
                base_name = base_name[:-5]
            
            # Check if we already have this session with different compression
            if any(s['name'] == base_name for s in sessions):
                continue
            
            try:
                stat = session_file.stat()
                created_dt = datetime.fromtimestamp(stat.st_ctime)
                modified_dt = datetime.fromtimestamp(stat.st_mtime)
                
                # Load minimal data for metadata
                with open(session_file, 'rb') as f:
                    data_bytes = f.read()
                
                if session_file.suffix == '.gz':
                    data_bytes = self._decompress_data(data_bytes)
                
                json_str = data_bytes.decode('utf-8')
                data = json.loads(json_str)
                
                session_info = {
                    "name": base_name,
                    "file": str(session_file.name),
                    "compressed": session_file.suffix == '.gz',
                    "created": created_dt.isoformat(),
                    "modified": modified_dt.isoformat(),
                    "size": stat.st_size,
                    "node_count": len(data.get('graph', {}).get('nodes', [])),
                    "edge_count": len(data.get('graph', {}).get('edges', []))
                }
                sessions.append(session_info)
            except Exception as e:
                logger.warning(f"Error reading session {session_file}: {str(e)}")
        
        # Apply filters if provided
        if filters:
            filtered_sessions = []
            for session in sessions:
                include = True
                
                if 'name' in filters and filters['name']:
                    if filters['name'].lower() not in session['name'].lower():
                        include = False
                
                if 'min_size' in filters and session['size'] < filters['min_size']:
                    include = False
                
                if 'max_size' in filters and session['size'] > filters['max_size']:
                    include = False
                
                if 'compressed' in filters and session['compressed'] != filters['compressed']:
                    include = False
                
                if 'created_after' in filters:
                    after_dt = datetime.fromisoformat(filters['created_after'])
                    session_dt = datetime.fromisoformat(session['created'])
                    if session_dt < after_dt:
                        include = False
                
                if 'created_before' in filters:
                    before_dt = datetime.fromisoformat(filters['created_before'])
                    session_dt = datetime.fromisoformat(session['created'])
                    if session_dt > before_dt:
                        include = False
                
                if 'modified_after' in filters:
                    after_dt = datetime.fromisoformat(filters['modified_after'])
                    session_dt = datetime.fromisoformat(session['modified'])
                    if session_dt < after_dt:
                        include = False
                
                if 'modified_before' in filters:
                    before_dt = datetime.fromisoformat(filters['modified_before'])
                    session_dt = datetime.fromisoformat(session['modified'])
                    if session_dt > before_dt:
                        include = False
                
                if include:
                    filtered_sessions.append(session)
            
            sessions = sorted(filtered_sessions, key=lambda s: s["modified"], reverse=True)
        else:
            sessions = sorted(sessions, key=lambda s: s["modified"], reverse=True)
        
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (both compressed and uncompressed variants)
        
        Args:
            session_id: Session ID
        
        Returns:
            True if deleted, False if not found
        """
        session_file_gz = self.sessions_dir / f"{session_id}.json.gz"
        session_file_json = self.sessions_dir / f"{session_id}.json"
        deleted = False
        
        if session_file_gz.exists():
            session_file_gz.unlink()
            deleted = True
        
        if session_file_json.exists():
            session_file_json.unlink()
            deleted = True
        
        # Remove from version tracking
        if session_id in self.session_versions:
            del self.session_versions[session_id]
            self._save_session_versions()
        
        if deleted:
            logger.info(f"Deleted session {session_id}")
        
        return deleted
    
    def delete_old_sessions(self, days: int = 30) -> Dict:
        """
        Delete sessions older than specified days (automatic cleanup)
        
        Args:
            days: Delete sessions older than this many days (default: 30)
        
        Returns:
            Dict with deletion statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_sessions = []
        total_space_freed = 0
        
        # Check both .json and .json.gz files
        all_files = list(self.sessions_dir.glob("*.json")) + list(self.sessions_dir.glob("*.json.gz"))
        
        for session_file in all_files:
            # Skip metadata files
            if session_file.name.startswith('.'):
                continue
            
            try:
                stat = session_file.stat()
                modified_dt = datetime.fromtimestamp(stat.st_mtime)
                
                if modified_dt < cutoff_date:
                    file_size = stat.st_size
                    session_file.unlink()
                    deleted_sessions.append({
                        'name': session_file.stem,
                        'modified': modified_dt.isoformat(),
                        'size': file_size
                    })
                    total_space_freed += file_size
                    logger.info(f"Deleted old session {session_file.name} (modified: {modified_dt})")
            except Exception as e:
                logger.error(f"Error deleting session {session_file.name}: {str(e)}")
        
        return {
            'deleted_count': len(deleted_sessions),
            'sessions': deleted_sessions,
            'space_freed': total_space_freed,
            'cutoff_date': cutoff_date.isoformat()
        }
