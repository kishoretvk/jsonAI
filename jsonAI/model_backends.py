from abc import ABC, abstractmethod
from transformers import PreTrainedModel, PreTrainedTokenizer
import asyncio

class ModelBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async version of generate. Default implementation uses threads."""
        loop = asyncio.get_running_loop()
        # Pass kwargs as a single dictionary argument to generate
        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))

class TransformersBackend(ModelBackend):
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text with detailed error handling."""
        try:
            input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(self.model.device)
            response = self.model.generate(input_tokens, **kwargs)
            return self.tokenizer.decode(response[0], skip_special_tokens=True)
        except Exception as e:
            raise ValueError(f"Failed to generate text: {e}")

class OllamaBackend(ModelBackend):
    def __init__(self, model_name: str, host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        try:
            import ollama
            self.client = ollama.Client(host=host)
        except ImportError:
            raise ImportError("Ollama is not installed. Please install it with `pip install ollama`")

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.generate(model=self.model_name, prompt=prompt, stream=False, options=kwargs)
        return response['response']

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async implementation for Ollama with error handling."""
        try:
            import ollama
            response = await ollama.AsyncClient(host=self.host).generate(
                model=self.model_name, 
                prompt=prompt, 
                stream=False, 
                options=kwargs
            )
            return response['response']
        except Exception as e:
            raise ValueError(f"Failed to generate text asynchronously: {e}")

class OpenAIBackend(ModelBackend):
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError("OpenAI library is not installed. Please install it with `pip install openai`")

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.openai.ChatCompletion.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 100),
                temperature=kwargs.get("temperature", 0.7),
                api_key=self.api_key
            )
            return response.choices[0].message["content"].strip()
        except Exception as e:
            raise ValueError(f"Failed to generate text with OpenAI: {e}")

    async def agenerate(self, prompt: str, **kwargs) -> str:
        loop = asyncio.get_running_loop()
        # Pass kwargs as a single dictionary argument to generate
        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))
