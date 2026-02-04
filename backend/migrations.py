"""
Database Migration System for WolfTrace
Handles schema versioning and data migrations
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Migration(ABC):
    """Abstract base class for migrations"""
    
    version: str
    description: str
    
    @abstractmethod
    def up(self, db_backend) -> None:
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self, db_backend) -> None:
        """Rollback migration"""
        pass


class MigrationV001AddNodeTypes(Migration):
    """V001: Initial schema - add node type indexing"""
    
    version = "001"
    description = "Initial schema with node type indexing"
    
    def up(self, db_backend) -> None:
        """Create indices for node types"""
        logger.info("Applying migration v001: Add node type indexing")
        # For Neo4j: Create indices (label required: use Entity as default for id lookup)
        if hasattr(db_backend, 'driver') and db_backend.driver:
            with db_backend.driver.session() as session:
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.id)")
    
    def down(self, db_backend) -> None:
        """Drop indices"""
        logger.info("Rolling back migration v001")
        if hasattr(db_backend, 'driver') and db_backend.driver:
            with db_backend.driver.session() as session:
                try:
                    session.run("DROP INDEX idx_node_type IF EXISTS")
                    session.run("DROP INDEX idx_node_id IF EXISTS")
                except:
                    pass


class MigrationV002AddEdgeIndexing(Migration):
    """V002: Add edge type indexing"""
    
    version = "002"
    description = "Add edge type indexing for faster queries"
    
    def up(self, db_backend) -> None:
        """Create edge indices"""
        logger.info("Applying migration v002: Add edge indexing")
        if hasattr(db_backend, 'driver') and db_backend.driver:
            with db_backend.driver.session() as session:
                session.run("CREATE CONSTRAINT IF NOT EXISTS ON ()-[r]-() ASSERT r.type IS NOT NULL")
    
    def down(self, db_backend) -> None:
        """Drop edge indices"""
        logger.info("Rolling back migration v002")
        if hasattr(db_backend, 'driver') and db_backend.driver:
            with db_backend.driver.session() as session:
                try:
                    session.run("DROP CONSTRAINT idx_edge_type IF EXISTS")
                except:
                    pass


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, migrations_dir: str = None, db_backend = None):
        """
        Initialize migration manager
        
        Args:
            migrations_dir: Directory to store migration metadata
            db_backend: Database backend to apply migrations to
        """
        if migrations_dir is None:
            backend_dir = Path(__file__).resolve().parent
            migrations_dir = str(backend_dir / 'data' / 'migrations')
        
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.db_backend = db_backend
        
        # Built-in migrations
        self.migrations: Dict[str, Migration] = {
            "001": MigrationV001AddNodeTypes(),
            "002": MigrationV002AddEdgeIndexing(),
        }
        
        self._load_migration_history()
    
    def _load_migration_history(self) -> None:
        """Load migration history from file"""
        history_file = self.migrations_dir / "migration_history.json"
        self.history = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.history = data.get('applied_migrations', [])
            except Exception as e:
                logger.warning(f"Could not load migration history: {str(e)}")
    
    def _save_migration_history(self) -> None:
        """Save migration history to file"""
        history_file = self.migrations_dir / "migration_history.json"
        
        try:
            with open(history_file, 'w') as f:
                json.dump({
                    'applied_migrations': self.history,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save migration history: {str(e)}")
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        return [m['version'] for m in self.history]
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations"""
        applied = self.get_applied_migrations()
        return [v for v in sorted(self.migrations.keys()) if v not in applied]
    
    def apply_migration(self, version: str) -> bool:
        """
        Apply a specific migration
        
        Args:
            version: Migration version to apply
        
        Returns:
            True if successful
        """
        if version not in self.migrations:
            logger.error(f"Migration {version} not found")
            return False
        
        if version in self.get_applied_migrations():
            logger.warning(f"Migration {version} already applied")
            return True
        
        try:
            migration = self.migrations[version]
            logger.info(f"Applying migration {version}: {migration.description}")
            
            if self.db_backend:
                migration.up(self.db_backend)
            
            # Record in history
            self.history.append({
                'version': version,
                'description': migration.description,
                'applied_at': datetime.now().isoformat()
            })
            self._save_migration_history()
            
            logger.info(f"Successfully applied migration {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {str(e)}")
            return False
    
    def apply_all_pending(self) -> List[str]:
        """
        Apply all pending migrations
        
        Returns:
            List of applied migration versions
        """
        applied = []
        for version in sorted(self.get_pending_migrations()):
            if self.apply_migration(version):
                applied.append(version)
            else:
                logger.warning(f"Stopping migration due to failure at {version}")
                break
        
        return applied
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration
        
        Args:
            version: Migration version to rollback
        
        Returns:
            True if successful
        """
        if version not in self.migrations:
            logger.error(f"Migration {version} not found")
            return False
        
        applied = self.get_applied_migrations()
        if version not in applied:
            logger.warning(f"Migration {version} not applied")
            return True
        
        try:
            migration = self.migrations[version]
            logger.info(f"Rolling back migration {version}")
            
            if self.db_backend:
                migration.down(self.db_backend)
            
            # Remove from history
            self.history = [m for m in self.history if m['version'] != version]
            self._save_migration_history()
            
            logger.info(f"Successfully rolled back migration {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {str(e)}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            'applied_count': len(self.get_applied_migrations()),
            'pending_count': len(self.get_pending_migrations()),
            'applied_migrations': self.get_applied_migrations(),
            'pending_migrations': self.get_pending_migrations(),
            'total_migrations': len(self.migrations),
            'all_applied': len(self.get_pending_migrations()) == 0
        }
    
    def register_migration(self, version: str, migration: Migration) -> None:
        """
        Register a custom migration
        
        Args:
            version: Migration version
            migration: Migration instance
        """
        self.migrations[version] = migration
        logger.info(f"Registered migration {version}: {migration.description}")
