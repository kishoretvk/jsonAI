from abc import ABC, abstractmethod
from transformers import PreTrainedModel, PreTrainedTokenizer

class ModelBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async version of generate. Default implementation uses threads."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate, prompt, **kwargs)

class TransformersBackend(ModelBackend):
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    def generate(self, prompt: str, **kwargs) -> str:
        input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(self.model.device)
        response = self.model.generate(
            input_tokens,
            **kwargs
        )
        return self.tokenizer.decode(response[0], skip_special_tokens=True)

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
        """Async implementation for Ollama"""
        import ollama
        response = await ollama.AsyncClient(host=self.host).generate(
            model=self.model_name, 
            prompt=prompt, 
            stream=False, 
            options=kwargs
        )
        return response['response']
