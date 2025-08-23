"""
StateManager for managing context and state in JsonAI workflows.

This module provides capabilities for managing persistent context
and state across workflow executions.
"""

from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import json
import uuid
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class StateVariable:
    """Represents a state variable with metadata."""
    name: str
    value: Any
    type: str
    scope: str = "global"  # global, session, step
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """Manages state and context for workflow executions."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.variables: Dict[str, StateVariable] = {}
        self.sessions: Dict[str, Dict[str, StateVariable]] = {}
        self.history: Dict[str, list] = defaultdict(list)
        self.current_session_id: Optional[str] = None
        
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session for state isolation."""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        self.sessions[session_id] = {}
        self.current_session_id = session_id
        
        if self.debug:
            logger.debug(f"Created session: {session_id}")
            
        return session_id
        
    def set_session(self, session_id: str) -> None:
        """Set the current session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
            
        self.current_session_id = session_id
        
        if self.debug:
            logger.debug(f"Set current session to: {session_id}")
            
    def get_session(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session_id
        
    def set_variable(self, name: str, value: Any, 
                    scope: str = "global", 
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set a variable in the state."""
        if metadata is None:
            metadata = {}
            
        var_type = type(value).__name__
        updated_at = datetime.now()
        
        variable = StateVariable(
            name=name,
            value=value,
            type=var_type,
            scope=scope,
            updated_at=updated_at,
            metadata=metadata
        )
        
        # Record in history
        self.history[name].append({
            "value": value,
            "type": var_type,
            "scope": scope,
            "timestamp": updated_at.isoformat(),
            "session_id": self.current_session_id
        })
        
        # Store in appropriate scope
        if scope == "global":
            if name in self.variables:
                variable.version = self.variables[name].version + 1
            self.variables[name] = variable
        elif scope == "session":
            if self.current_session_id is None:
                raise ValueError("No active session. Create a session first.")
                
            if name in self.sessions[self.current_session_id]:
                variable.version = self.sessions[self.current_session_id][name].version + 1
            self.sessions[self.current_session_id][name] = variable
        else:
            raise ValueError(f"Unknown scope: {scope}")
            
        if self.debug:
            logger.debug(f"Set variable {name} = {value} (scope: {scope})")
            
    def get_variable(self, name: str, scope: str = "global") -> Any:
        """Get a variable from the state."""
        variable = None
        
        if scope == "global":
            variable = self.variables.get(name)
        elif scope == "session":
            if self.current_session_id is None:
                raise ValueError("No active session. Create a session first.")
                
            if self.current_session_id in self.sessions:
                variable = self.sessions[self.current_session_id].get(name)
        else:
            raise ValueError(f"Unknown scope: {scope}")
            
        if variable is None:
            raise KeyError(f"Variable {name} not found in {scope} scope")
            
        if self.debug:
            logger.debug(f"Retrieved variable {name} = {variable.value} (scope: {scope})")
            
        return variable.value
        
    def has_variable(self, name: str, scope: str = "global") -> bool:
        """Check if a variable exists in the state."""
        if scope == "global":
            return name in self.variables
        elif scope == "session":
            if self.current_session_id is None:
                return False
            return (self.current_session_id in self.sessions and 
                    name in self.sessions[self.current_session_id])
        else:
            raise ValueError(f"Unknown scope: {scope}")
            
    def delete_variable(self, name: str, scope: str = "global") -> None:
        """Delete a variable from the state."""
        if scope == "global":
            if name in self.variables:
                del self.variables[name]
        elif scope == "session":
            if (self.current_session_id is not None and 
                self.current_session_id in self.sessions and
                name in self.sessions[self.current_session_id]):
                del self.sessions[self.current_session_id][name]
        else:
            raise ValueError(f"Unknown scope: {scope}")
            
        if self.debug:
            logger.debug(f"Deleted variable {name} from {scope} scope")
            
    def get_all_variables(self, scope: str = "global") -> Dict[str, Any]:
        """Get all variables from a specific scope."""
        result = {}
        
        if scope == "global":
            result = {name: var.value for name, var in self.variables.items()}
        elif scope == "session":
            if self.current_session_id is not None and self.current_session_id in self.sessions:
                result = {name: var.value for name, var in self.sessions[self.current_session_id].items()}
        else:
            raise ValueError(f"Unknown scope: {scope}")
            
        return result
        
    def clear_session(self, session_id: Optional[str] = None) -> None:
        """Clear all variables from a session."""
        target_session_id = session_id or self.current_session_id
        
        if target_session_id is None:
            raise ValueError("No session specified and no active session")
            
        if target_session_id in self.sessions:
            self.sessions[target_session_id].clear()
            
        if self.debug:
            logger.debug(f"Cleared session: {target_session_id}")
            
    def delete_session(self, session_id: str) -> None:
        """Delete a session entirely."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
        # If this was the current session, clear it
        if self.current_session_id == session_id:
            self.current_session_id = None
            
        if self.debug:
            logger.debug(f"Deleted session: {session_id}")
            
    def get_session_variables(self, session_id: str) -> Dict[str, Any]:
        """Get all variables for a specific session."""
        if session_id not in self.sessions:
            return {}
            
        return {name: var.value for name, var in self.sessions[session_id].items()}
        
    def get_history(self, variable_name: str) -> list:
        """Get the history of a variable."""
        return self.history.get(variable_name, [])
        
    def serialize_state(self, scope: str = "global") -> str:
        """Serialize the state to a JSON string."""
        variables = self.get_all_variables(scope)
        # Convert non-serializable objects to strings
        serializable_vars = {}
        for name, value in variables.items():
            try:
                json.dumps(value)  # Test if serializable
                serializable_vars[name] = value
            except (TypeError, ValueError):
                serializable_vars[name] = str(value)  # Convert to string if not serializable
                
        return json.dumps(serializable_vars, indent=2)
        
    def deserialize_state(self, serialized_state: str, scope: str = "global") -> None:
        """Deserialize state from a JSON string."""
        variables = json.loads(serialized_state)
        for name, value in variables.items():
            self.set_variable(name, value, scope)