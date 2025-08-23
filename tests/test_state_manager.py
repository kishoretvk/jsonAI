"""
Test cases for the StateManager.
"""

import unittest
from jsonAI.state_manager import StateManager, StateVariable


class TestStateManager(unittest.TestCase):
    """Test cases for StateManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state_manager = StateManager(debug=True)
        
    def test_create_session(self):
        """Test creating a new session."""
        session_id = self.state_manager.create_session()
        self.assertIsNotNone(session_id)
        self.assertEqual(self.state_manager.get_session(), session_id)
        
    def test_create_session_with_id(self):
        """Test creating a session with a specific ID."""
        session_id = "test_session_123"
        created_id = self.state_manager.create_session(session_id)
        self.assertEqual(created_id, session_id)
        self.assertEqual(self.state_manager.get_session(), session_id)
        
    def test_set_session(self):
        """Test setting the current session."""
        session_id1 = self.state_manager.create_session()
        session_id2 = self.state_manager.create_session()
        
        # Switch back to first session
        self.state_manager.set_session(session_id1)
        self.assertEqual(self.state_manager.get_session(), session_id1)
        
    def test_set_session_nonexistent(self):
        """Test setting a non-existent session."""
        with self.assertRaises(ValueError):
            self.state_manager.set_session("nonexistent_session")
            
    def test_set_variable_global(self):
        """Test setting a global variable."""
        self.state_manager.set_variable("test_var", "test_value", scope="global")
        self.assertTrue(self.state_manager.has_variable("test_var", scope="global"))
        
    def test_set_variable_session(self):
        """Test setting a session variable."""
        session_id = self.state_manager.create_session()
        self.state_manager.set_variable("test_var", "test_value", scope="session")
        self.assertTrue(self.state_manager.has_variable("test_var", scope="session"))
        
    def test_set_variable_session_no_active_session(self):
        """Test setting a session variable without an active session."""
        with self.assertRaises(ValueError):
            self.state_manager.set_variable("test_var", "test_value", scope="session")
            
    def test_get_variable(self):
        """Test getting a variable."""
        self.state_manager.set_variable("test_var", "test_value", scope="global")
        value = self.state_manager.get_variable("test_var", scope="global")
        self.assertEqual(value, "test_value")
        
    def test_get_variable_nonexistent(self):
        """Test getting a non-existent variable."""
        with self.assertRaises(KeyError):
            self.state_manager.get_variable("nonexistent_var", scope="global")
            
    def test_delete_variable(self):
        """Test deleting a variable."""
        self.state_manager.set_variable("test_var", "test_value", scope="global")
        self.assertTrue(self.state_manager.has_variable("test_var", scope="global"))
        
        self.state_manager.delete_variable("test_var", scope="global")
        self.assertFalse(self.state_manager.has_variable("test_var", scope="global"))
        
    def test_get_all_variables(self):
        """Test getting all variables from a scope."""
        self.state_manager.set_variable("var1", "value1", scope="global")
        self.state_manager.set_variable("var2", "value2", scope="global")
        
        all_vars = self.state_manager.get_all_variables(scope="global")
        self.assertEqual(len(all_vars), 2)
        self.assertEqual(all_vars["var1"], "value1")
        self.assertEqual(all_vars["var2"], "value2")
        
    def test_clear_session(self):
        """Test clearing a session."""
        session_id = self.state_manager.create_session()
        self.state_manager.set_variable("var1", "value1", scope="session")
        self.state_manager.set_variable("var2", "value2", scope="session")
        
        self.assertTrue(self.state_manager.has_variable("var1", scope="session"))
        self.assertTrue(self.state_manager.has_variable("var2", scope="session"))
        
        self.state_manager.clear_session()
        self.assertFalse(self.state_manager.has_variable("var1", scope="session"))
        self.assertFalse(self.state_manager.has_variable("var2", scope="session"))
        
    def test_delete_session(self):
        """Test deleting a session."""
        session_id = self.state_manager.create_session()
        self.state_manager.set_variable("var1", "value1", scope="session")
        
        self.state_manager.delete_session(session_id)
        with self.assertRaises(ValueError):
            self.state_manager.set_session(session_id)
            
    def test_get_session_variables(self):
        """Test getting all variables for a specific session."""
        session_id = self.state_manager.create_session()
        self.state_manager.set_variable("var1", "value1", scope="session")
        self.state_manager.set_variable("var2", "value2", scope="session")
        
        session_vars = self.state_manager.get_session_variables(session_id)
        self.assertEqual(len(session_vars), 2)
        self.assertEqual(session_vars["var1"], "value1")
        self.assertEqual(session_vars["var2"], "value2")
        
    def test_get_history(self):
        """Test getting variable history."""
        self.state_manager.set_variable("test_var", "value1", scope="global")
        self.state_manager.set_variable("test_var", "value2", scope="global")
        
        history = self.state_manager.get_history("test_var")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["value"], "value1")
        self.assertEqual(history[1]["value"], "value2")
        
    def test_serialize_deserialize_state(self):
        """Test serializing and deserializing state."""
        self.state_manager.set_variable("var1", "value1", scope="global")
        self.state_manager.set_variable("var2", {"nested": "value"}, scope="global")
        
        serialized = self.state_manager.serialize_state(scope="global")
        self.assertIsInstance(serialized, str)
        
        # Create a new state manager and deserialize
        new_state_manager = StateManager()
        new_state_manager.deserialize_state(serialized, scope="global")
        
        self.assertEqual(new_state_manager.get_variable("var1", scope="global"), "value1")
        self.assertEqual(new_state_manager.get_variable("var2", scope="global"), {"nested": "value"})


if __name__ == "__main__":
    unittest.main()