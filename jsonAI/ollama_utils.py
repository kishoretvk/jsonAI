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
            
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                import ollama
                client = ollama.Client(host=self.host)
                response = client.list()
                models = [model.model.split(':')[0] for model in response.models]
                self._available_models = models
                return models
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
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
            # Check exact match first
            if model in available:
                return model
            # Check with version tags (e.g., "mistral:latest")
            for avail_model in available:
                if avail_model.startswith(model + ":"):
                    return avail_model
                    
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
        
        # Model-specific adjustments (only non-temperature parameters)
        model_params = {
            "mistral": {
                "top_p": 0.9,
                "repeat_penalty": 1.1
            },
            "llama3": {
                "top_p": 0.95,
                "repeat_penalty": 1.1
            },
            "phi3": {
                "top_p": 0.9,
                "repeat_penalty": 1.2
            },
            "gemma": {
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
        
        # Apply task-specific parameters FIRST (higher priority)
        if task_type in task_params:
            params.update(task_params[task_type])
            
        # Apply model-specific parameters (lower priority, only for model-specific tuning)
        # Handle version tags (e.g., "mistral:latest" -> "mistral")
        base_model_name = model_name.split(':')[0] if ':' in model_name else model_name
        if base_model_name in model_params:
            params.update(model_params[base_model_name])
            
        # Validate parameters
        return self._validate_parameters(params)
        
    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clamp parameters to valid ranges."""
        validated = params.copy()
        
        # Temperature: 0.0 to 2.0
        validated["temperature"] = max(0.0, min(2.0, params.get("temperature", 0.7)))
        
        # Top-p: 0.0 to 1.0
        validated["top_p"] = max(0.0, min(1.0, params.get("top_p", 0.9)))
        
        # Repeat penalty: 1.0 to 2.0
        validated["repeat_penalty"] = max(1.0, min(2.0, params.get("repeat_penalty", 1.1)))
        
        return validated


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
        if any(keyword in desc_lower
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
