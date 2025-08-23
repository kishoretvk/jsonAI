"""
Ollama utilities for model selection and parameter tuning.

This module provides utilities for working with Ollama models,
including model selection, parameter tuning, and performance optimization.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
from jsonAI.model_backends import OllamaBackend


class OllamaModelSelector:
    """Utility class for selecting and tuning Ollama models."""
    
    # Default models ranked by performance and capabilities
    DEFAULT_MODEL_RANKING = [
        "mistral",
        "llama3",
        "llama2",
        "phi3",
        "gemma",
        "mixtral",
        "neural-chat",
        "starling-lm",
        "openhermes",
        "dolphin-phi",
        "llama2-uncensored",
        "nous-hermes2",
        "yi"
    ]
    
    def __init__(self, host: str = "http://localhost:11434"):
        """Initialize the model selector."""
        self.host = host
        self._available_models = None
        
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        if self._available_models is not None:
            return self._available_models
            
        try:
            import ollama
            client = ollama.Client(host=self.host)
            response = client.list()
            models = [model['name'].split(':')[0] for model in response.get('models', [])]
            self._available_models = models
            return models
        except Exception as e:
            print(f"Warning: Could not fetch available models from Ollama: {e}")
            # Return default ranking as fallback
            return self.DEFAULT_MODEL_RANKING.copy()
            
    def select_best_model(self, task_type: str = "general") -> str:
        """Select the best model for a given task type."""
        available = self.get_available_models()
        
        # Task-specific model preferences
        task_preferences = {
            "json_generation": ["mistral", "llama3", "phi3"],
            "structured_data": ["mistral", "llama3", "gemma"],
            "creative_writing": ["llama3", "gemma", "mixtral"],
            "code_generation": ["llama3", "phi3", "starling-lm"],
            "reasoning": ["mistral", "llama3", "mixtral"],
            "general": ["mistral", "llama3", "phi3"]
        }
        
        preferences = task_preferences.get(task_type, task_preferences["general"])
        
        # Find the first available model from preferences
        for model in preferences:
            if model in available:
                return model
                
        # Fallback to first available model
        return available[0] if available else "mistral"
        
    def get_model_parameters(self, model_name: str, task_type: str = "general") -> Dict[str, Any]:
        """Get recommended parameters for a specific model and task type."""
        # Base parameters
        params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        
        # Model-specific adjustments
        model_params = {
            "mistral": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            },
            "llama3": {
                "temperature": 0.7,
                "top_p": 0.95,
                "repeat_penalty": 1.1
            },
            "phi3": {
                "temperature": 0.6,
                "top_p": 0.9,
                "repeat_penalty": 1.2
            },
            "gemma": {
                "temperature": 0.6,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        # Task-specific adjustments
        task_params = {
            "json_generation": {
                "temperature": 0.3,
                "repeat_penalty": 1.2
            },
            "structured_data": {
                "temperature": 0.4,
                "repeat_penalty": 1.2
            },
            "creative_writing": {
                "temperature": 0.9,
                "top_p": 0.95
            },
            "code_generation": {
                "temperature": 0.5,
                "repeat_penalty": 1.3
            },
            "reasoning": {
                "temperature": 0.5,
                "repeat_penalty": 1.2
            }
        }
        
        # Apply model-specific parameters
        if model_name in model_params:
            params.update(model_params[model_name])
            
        # Apply task-specific parameters
        if task_type in task_params:
            params.update(task_params[task_type])
            
        return params


class OllamaPerformanceTuner:
    """Utility class for tuning Ollama model performance."""
    
    def __init__(self, model_selector: OllamaModelSelector):
        """Initialize the performance tuner."""
        self.model_selector = model_selector
        
    def tune_for_task(self, task_description: str, sample_prompt: str, 
                      sample_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Tune model and parameters for a specific task."""
        # Analyze task to determine type
        task_type = self._analyze_task_type(task_description, sample_schema)
        
        # Select best model for task
        model_name = self.model_selector.select_best_model(task_type)
        
        # Get recommended parameters
        parameters = self.model_selector.get_model_parameters(model_name, task_type)
        
        return model_name, parameters
        
    def _analyze_task_type(self, task_description: str, schema: Dict[str, Any]) -> str:
        """Analyze task description and schema to determine task type."""
        # Convert to lowercase for matching
        desc_lower = task_description.lower()
        schema_str = json.dumps(schema).lower()
        
        # Check for JSON/structured data indicators
        if any(keyword in desc_lower or keyword in schema_str 
               for keyword in ["json", "object", "array", "property", "schema"]):
            if "enum" in schema_str or any(prop.get("type") in ["string", "integer", "number"] 
                                          for prop in schema.get("properties", {}).values()):
                return "structured_data"
            return "json_generation"
            
        # Check for creative writing indicators
        if any(keyword in desc_lower 
               for keyword in ["story", "creative", "write", "narrative", "poem"]):
            return "creative_writing"
            
        # Check for code generation indicators
        if any(keyword in desc_lower 
               for keyword in ["code", "function", "program", "python", "javascript"]):
            return "code_generation"
            
        # Check for reasoning indicators
        if any(keyword in desc_lower 
               for keyword in ["calculate", "reason", "logic", "math", "analyze"]):
            return "reasoning"
            
        # Default to general
        return "general"
        
    def benchmark_models(self, prompt: str, schema: Dict[str, Any], 
                        models: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Benchmark multiple models for a given task."""
        if models is None:
            models = self.model_selector.get_available_models()[:5]  # Top 5 models
            
        results = {}
        
        for model_name in models:
            try:
                # Get parameters for this model
                params = self.model_selector.get_model_parameters(model_name, "json_generation")
                
                # Create backend
                backend = OllamaBackend(model_name=model_name)
                
                # Time the generation
                import time
                start_time = time.time()
                response = backend.generate(prompt, **params)
                end_time = time.time()
                
                # Store results
                results[model_name] = {
                    "response_time": end_time - start_time,
                    "response_length": len(response),
                    "parameters": params
                }
            except Exception as e:
                results[model_name] = {
                    "error": str(e),
                    "response_time": float('inf'),
                    "response_length": 0
                }
                
        return results