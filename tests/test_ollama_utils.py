"""
Test cases for Ollama utilities.
"""

import unittest
from jsonAI.ollama_utils import OllamaModelSelector, OllamaPerformanceTuner


class TestOllamaModelSelector(unittest.TestCase):
    """Test cases for OllamaModelSelector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.selector = OllamaModelSelector()
        
    def test_default_model_ranking(self):
        """Test default model ranking."""
        ranking = self.selector.DEFAULT_MODEL_RANKING
        self.assertIsInstance(ranking, list)
        self.assertGreater(len(ranking), 0)
        self.assertIn("mistral", ranking)
        
    def test_task_preferences(self):
        """Test task-specific model preferences."""
        # Test that we get a model for each task type
        task_types = ["json_generation", "structured_data", "creative_writing", 
                     "code_generation", "reasoning", "general"]
                     
        for task_type in task_types:
            model = self.selector.select_best_model(task_type)
            self.assertIsInstance(model, str)
            self.assertGreater(len(model), 0)
            
    def test_model_parameters(self):
        """Test model parameter recommendations."""
        # Test with common models
        models = ["mistral", "llama3", "phi3"]
        task_types = ["json_generation", "structured_data", "general"]
        
        for model in models:
            for task_type in task_types:
                params = self.selector.get_model_parameters(model, task_type)
                self.assertIsInstance(params, dict)
                self.assertIn("temperature", params)
                self.assertIn("top_p", params)
                self.assertIn("repeat_penalty", params)
                

class TestOllamaPerformanceTuner(unittest.TestCase):
    """Test cases for OllamaPerformanceTuner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.selector = OllamaModelSelector()
        self.tuner = OllamaPerformanceTuner(self.selector)
        
    def test_task_analysis(self):
        """Test task type analysis."""
        # Test JSON generation task
        task_type = self.tuner._analyze_task_type(
            "Generate a JSON object",
            {"type": "object", "properties": {"name": {"type": "string"}}}
        )
        self.assertIn(task_type, ["structured_data", "json_generation"])
        
        # Test creative writing task
        task_type = self.tuner._analyze_task_type(
            "Write a creative story",
            {}
        )
        self.assertEqual(task_type, "creative_writing")
        
        # Test code generation task
        task_type = self.tuner._analyze_task_type(
            "Generate Python code",
            {}
        )
        self.assertEqual(task_type, "code_generation")
        
        # Test reasoning task
        task_type = self.tuner._analyze_task_type(
            "Calculate the sum of numbers",
            {}
        )
        self.assertEqual(task_type, "reasoning")
        
    def test_tune_for_task(self):
        """Test tuning for a specific task."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        model_name, params = self.tuner.tune_for_task(
            "Generate person profiles",
            "Generate a person with name and age",
            schema
        )
        
        self.assertIsInstance(model_name, str)
        self.assertIsInstance(params, dict)
        self.assertGreater(len(model_name), 0)
        self.assertIn("temperature", params)
        

if __name__ == "__main__":
    unittest.main()