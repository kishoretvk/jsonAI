"""
Test cases for the SQLiteStorage.
"""

import unittest
import os
import tempfile
from jsonAI.persistent_storage import SQLiteStorage


class TestSQLiteStorage(unittest.TestCase):
    """Test cases for SQLiteStorage."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_storage.db")
        self.storage = SQLiteStorage(db_path=self.db_path, debug=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.storage.close()
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        
    def test_save_and_load_variable(self):
        """Test saving and loading a variable."""
        self.storage.save_variable("test_var", "test_value", scope="global")
        value = self.storage.load_variable("test_var", scope="global")
        self.assertEqual(value, "test_value")
        
    def test_save_and_load_complex_variable(self):
        """Test saving and loading a complex variable."""
        complex_value = {"name": "John", "age": 30, "scores": [85, 92, 78]}
        self.storage.save_variable("complex_var", complex_value, scope="global")
        value = self.storage.load_variable("complex_var", scope="global")
        self.assertEqual(value, complex_value)
        
    def test_has_variable(self):
        """Test checking if a variable exists."""
        self.assertFalse(self.storage.has_variable("test_var", scope="global"))
        self.storage.save_variable("test_var", "test_value", scope="global")
        self.assertTrue(self.storage.has_variable("test_var", scope="global"))
        
    def test_delete_variable(self):
        """Test deleting a variable."""
        self.storage.save_variable("test_var", "test_value", scope="global")
        self.assertTrue(self.storage.has_variable("test_var", scope="global"))
        self.storage.delete_variable("test_var", scope="global")
        self.assertFalse(self.storage.has_variable("test_var", scope="global"))
        
    def test_list_variables(self):
        """Test listing variables in a scope."""
        self.storage.save_variable("var1", "value1", scope="global")
        self.storage.save_variable("var2", "value2", scope="global")
        self.storage.save_variable("var3", "value3", scope="global")
        
        variables = self.storage.list_variables(scope="global")
        self.assertEqual(len(variables), 3)
        self.assertIn("var1", variables)
        self.assertIn("var2", variables)
        self.assertIn("var3", variables)
        
    def test_save_and_load_session_variable(self):
        """Test saving and loading a session variable."""
        session_id = "test_session_123"
        self.storage.save_variable("session_var", "session_value", 
                                 scope="session", session_id=session_id)
        value = self.storage.load_variable("session_var", scope="session", session_id=session_id)
        self.assertEqual(value, "session_value")
        
    def test_save_workflow_execution(self):
        """Test saving workflow execution data."""
        execution_id = "exec_123"
        input_data = {"prompt": "Test prompt", "schema": {"type": "object"}}
        output_data = {"result": "Test result"}
        metadata = {"user_id": "user_456"}
        
        self.storage.save_workflow_execution(
            execution_id=execution_id,
            status="completed",
            input_data=input_data,
            output_data=output_data,
            metadata=metadata
        )
        
        # Verify the data was saved
        execution_data = self.storage.load_workflow_execution(execution_id)
        self.assertEqual(execution_data['id'], execution_id)
        self.assertEqual(execution_data['status'], "completed")
        self.assertEqual(execution_data['input_data'], input_data)
        self.assertEqual(execution_data['output_data'], output_data)
        self.assertEqual(execution_data['metadata'], metadata)
        
    def test_save_and_load_execution_steps(self):
        """Test saving and loading execution steps."""
        execution_id = "exec_123"
        steps_data = [
            {
                "step_id": "step_1",
                "step_name": "Generation Step",
                "status": "completed",
                "input_data": {"prompt": "Generate object"},
                "output_data": {"result": "Generated object"}
            },
            {
                "step_id": "step_2",
                "step_name": "Validation Step",
                "status": "completed",
                "input_data": {"data": {"name": "John"}},
                "output_data": {"valid": True}
            }
        ]
        
        # Save steps
        for step_data in steps_data:
            self.storage.save_execution_step(
                execution_id=execution_id,
                step_id=step_data["step_id"],
                step_name=step_data["step_name"],
                status=step_data["status"],
                input_data=step_data["input_data"],
                output_data=step_data["output_data"]
            )
            
        # Load steps
        loaded_steps = self.storage.load_execution_steps(execution_id)
        self.assertEqual(len(loaded_steps), 2)
        self.assertEqual(loaded_steps[0]['step_id'], "step_1")
        self.assertEqual(loaded_steps[1]['step_id'], "step_2")
        self.assertEqual(loaded_steps[0]['status'], "completed")
        self.assertEqual(loaded_steps[1]['status'], "completed")
        
    def test_nonexistent_variable(self):
        """Test loading a non-existent variable."""
        with self.assertRaises(KeyError):
            self.storage.load_variable("nonexistent_var", scope="global")
            
    def test_nonexistent_workflow_execution(self):
        """Test loading a non-existent workflow execution."""
        with self.assertRaises(KeyError):
            self.storage.load_workflow_execution("nonexistent_exec")
            
    def test_clear_storage(self):
        """Test clearing all storage data."""
        # Add some data
        self.storage.save_variable("var1", "value1", scope="global")
        self.storage.save_variable("var2", "value2", scope="session", session_id="sess_123")
        self.storage.save_workflow_execution("exec_123", "completed")
        
        # Verify data exists
        self.assertTrue(self.storage.has_variable("var1", scope="global"))
        variables = self.storage.list_variables(scope="global")
        self.assertGreater(len(variables), 0)
        
        # Clear storage
        self.storage.clear_storage()
        
        # Verify data is cleared
        variables = self.storage.list_variables(scope="global")
        self.assertEqual(len(variables), 0)