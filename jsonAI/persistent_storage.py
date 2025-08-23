"""
Persistent storage mechanisms for JsonAI.

This module provides persistent storage capabilities using SQLite
for workflow state and context management.
"""

import sqlite3
import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """SQLite-based persistent storage for JsonAI state and context."""
    
    def __init__(self, db_path: str = "jsonai_state.db", debug: bool = False):
        self.db_path = db_path
        self.debug = debug
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the SQLite database with required tables."""
        with self._get_connection() as conn:
            # Create tables for state variables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_variables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL,
                    scope TEXT NOT NULL DEFAULT 'global',
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    metadata TEXT,
                    UNIQUE(name, scope, session_id)
                )
            """)
            
            # Create tables for workflow executions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create tables for execution steps
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error TEXT,
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_variables_name_scope 
                ON state_variables(name, scope)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_variables_session 
                ON state_variables(session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_executions_status 
                ON workflow_executions(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_steps_execution_id 
                ON execution_steps(execution_id)
            """)
            
            conn.commit()
            
        if self.debug:
            logger.debug(f"Initialized SQLite database at {self.db_path}")
            
    @contextmanager
    def _get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
            
    def save_variable(self, name: str, value: Any, 
                     scope: str = "global", 
                     session_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save a variable to persistent storage."""
        # Serialize the value and metadata
        serialized_value = self._serialize_value(value)
        serialized_metadata = json.dumps(metadata) if metadata else None
        var_type = type(value).__name__
        updated_at = datetime.now()
        
        with self._get_connection() as conn:
            # Check if variable already exists
            cursor = conn.execute("""
                SELECT version FROM state_variables 
                WHERE name = ? AND scope = ? AND session_id IS ?
            """, (name, scope, session_id))
            
            row = cursor.fetchone()
            if row:
                # Update existing variable
                version = row['version'] + 1
                conn.execute("""
                    UPDATE state_variables 
                    SET value = ?, type = ?, updated_at = ?, version = ?, metadata = ?
                    WHERE name = ? AND scope = ? AND session_id IS ?
                """, (serialized_value, var_type, updated_at, version, serialized_metadata,
                      name, scope, session_id))
            else:
                # Insert new variable
                conn.execute("""
                    INSERT INTO state_variables 
                    (name, value, type, scope, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, serialized_value, var_type, scope, session_id, serialized_metadata))
                
            conn.commit()
            
        if self.debug:
            logger.debug(f"Saved variable {name} to persistent storage")
            
    def load_variable(self, name: str, 
                     scope: str = "global", 
                     session_id: Optional[str] = None) -> Any:
        """Load a variable from persistent storage."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value, type FROM state_variables 
                WHERE name = ? AND scope = ? AND session_id IS ?
            """, (name, scope, session_id))
            
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Variable {name} not found in {scope} scope")
                
            serialized_value = row['value']
            var_type = row['type']
            value = self._deserialize_value(serialized_value, var_type)
            
        if self.debug:
            logger.debug(f"Loaded variable {name} from persistent storage")
            
        return value
        
    def has_variable(self, name: str, 
                    scope: str = "global", 
                    session_id: Optional[str] = None) -> bool:
        """Check if a variable exists in persistent storage."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 1 FROM state_variables 
                WHERE name = ? AND scope = ? AND session_id IS ?
            """, (name, scope, session_id))
            
            return cursor.fetchone() is not None
            
    def delete_variable(self, name: str, 
                       scope: str = "global", 
                       session_id: Optional[str] = None) -> None:
        """Delete a variable from persistent storage."""
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM state_variables 
                WHERE name = ? AND scope = ? AND session_id IS ?
            """, (name, scope, session_id))
            conn.commit()
            
        if self.debug:
            logger.debug(f"Deleted variable {name} from persistent storage")
            
    def list_variables(self, scope: str = "global", 
                      session_id: Optional[str] = None) -> List[str]:
        """List all variable names in a scope."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM state_variables 
                WHERE scope = ? AND session_id IS ?
            """, (scope, session_id))
            
            return [row['name'] for row in cursor.fetchall()]
            
    def save_workflow_execution(self, execution_id: str, status: str,
                               input_data: Optional[Dict[str, Any]] = None,
                               output_data: Optional[Dict[str, Any]] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save workflow execution data."""
        serialized_input = json.dumps(input_data) if input_data else None
        serialized_output = json.dumps(output_data) if output_data else None
        serialized_metadata = json.dumps(metadata) if metadata else None
        completed_at = datetime.now() if status in ['completed', 'failed'] else None
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_executions 
                (id, status, input_data, output_data, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (execution_id, status, serialized_input, serialized_output, 
                  completed_at, serialized_metadata))
            conn.commit()
            
        if self.debug:
            logger.debug(f"Saved workflow execution {execution_id} to persistent storage")
            
    def load_workflow_execution(self, execution_id: str) -> Dict[str, Any]:
        """Load workflow execution data."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM workflow_executions WHERE id = ?
            """, (execution_id,))
            
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Workflow execution {execution_id} not found")
                
            return {
                'id': row['id'],
                'status': row['status'],
                'input_data': json.loads(row['input_data']) if row['input_data'] else None,
                'output_data': json.loads(row['output_data']) if row['output_data'] else None,
                'started_at': row['started_at'],
                'completed_at': row['completed_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
            
    def save_execution_step(self, execution_id: str, step_id: str, step_name: str,
                           status: str, input_data: Optional[Dict[str, Any]] = None,
                           output_data: Optional[Dict[str, Any]] = None,
                           error: Optional[str] = None) -> None:
        """Save execution step data."""
        serialized_input = json.dumps(input_data) if input_data else None
        serialized_output = json.dumps(output_data) if output_data else None
        completed_at = datetime.now() if status in ['completed', 'failed'] else None
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO execution_steps 
                (execution_id, step_id, step_name, status, input_data, output_data, completed_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (execution_id, step_id, step_name, status, serialized_input, 
                  serialized_output, completed_at, error))
            conn.commit()
            
        if self.debug:
            logger.debug(f"Saved execution step {step_id} for execution {execution_id}")
            
    def load_execution_steps(self, execution_id: str) -> List[Dict[str, Any]]:
        """Load all execution steps for a workflow execution."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM execution_steps WHERE execution_id = ?
                ORDER BY id
            """, (execution_id,))
            
            steps = []
            for row in cursor.fetchall():
                steps.append({
                    'id': row['id'],
                    'execution_id': row['execution_id'],
                    'step_id': row['step_id'],
                    'step_name': row['step_name'],
                    'status': row['status'],
                    'input_data': json.loads(row['input_data']) if row['input_data'] else None,
                    'output_data': json.loads(row['output_data']) if row['output_data'] else None,
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at'],
                    'error': row['error']
                })
                
            return steps
            
    def _serialize_value(self, value: Any) -> str:
        """Serialize a value for storage."""
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            # If JSON serialization fails, convert to string
            return json.dumps(str(value))
            
    def _deserialize_value(self, serialized_value: str, var_type: str) -> Any:
        """Deserialize a value from storage."""
        try:
            value = json.loads(serialized_value)
            # Additional type conversion could be done here based on var_type
            return value
        except (TypeError, ValueError, json.JSONDecodeError):
            # If deserialization fails, return as string
            return serialized_value
            
    def clear_storage(self) -> None:
        """Clear all data from the storage."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM state_variables")
            conn.execute("DELETE FROM workflow_executions")
            conn.execute("DELETE FROM execution_steps")
            conn.commit()
            
        if self.debug:
            logger.debug("Cleared all data from persistent storage")
            
    def close(self) -> None:
        """Close the database connection."""
        # Connection is automatically closed by the context manager
        pass