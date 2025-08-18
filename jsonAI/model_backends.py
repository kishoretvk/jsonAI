


from abc import ABC, abstractmethod
from transformers import PreTrainedModel
try:
    from transformers import PreTrainedTokenizer
except ImportError:
    PreTrainedTokenizer = None  # type: ignore
import asyncio

class ModelBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs: object) -> str:
        pass

    async def agenerate(self, prompt: str, **kwargs: object) -> str:
        """Async version of generate. Default implementation uses threads."""
        loop = asyncio.get_running_loop()
        # Pass kwargs as a single dictionary argument to generate

        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))

class TransformersBackend(ModelBackend):
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate text with detailed error handling."""
        try:
            import torch
            input_tokens = self.tokenizer.encode(prompt, return_tensors="pt")
            # Defensive: ensure input_tokens is not called as a function
            # Only call .to() if input_tokens has it (torch.Tensor)
            if hasattr(input_tokens, "to") and callable(getattr(input_tokens, "to")):
                input_tokens = input_tokens.to(getattr(self.model, "device", "cpu"))
            # Do not call input_tokens as a function (fix mypy "Tensor not callable")
            # Use input_tokens directly
            response = getattr(self.model, "generate", lambda *a, **k: None)(input_tokens, **kwargs)
            if response is None:
                raise ValueError("Model generate returned None")
            return self.tokenizer.decode(response[0], skip_special_tokens=True)
        except Exception as e:
            raise ValueError(f"Failed to generate text: {e}")


class OllamaBackend(ModelBackend):
    def __init__(self, model_name: str, host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.structured = True  # Mark as structured for integration test
        try:
            import ollama
            try:
                from ollama.types import Options  # type: ignore
                self._OllamaOptions = Options
            except ImportError:
                self._OllamaOptions = None
            self.client = ollama.Client(host=host)
        except ImportError:
            raise ImportError("Ollama is not installed. Please install it with `pip install ollama`")

    def generate(self, prompt: str, **kwargs) -> str:
        # Always use the real Ollama call for integration tests, for any schema type
        options = None
        if hasattr(self, "_OllamaOptions") and self._OllamaOptions is not None and kwargs:
            try:
                options = self._OllamaOptions(**kwargs)
            except Exception:
                options = None
        response = self.client.generate(model=self.model_name, prompt=prompt, stream=False, options=options)
        # Handle Mapping or Iterator response
        if isinstance(response, dict) and 'response' in response:
            return response['response']
        elif hasattr(response, '__iter__'):
            # If it's an iterator, get the first item with 'response'
            for item in response:
                if isinstance(item, dict) and 'response' in item:
                    return item['response']
            raise ValueError("No 'response' found in Ollama response iterator")
        else:
            raise TypeError("Unexpected Ollama response type")

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async implementation for Ollama with error handling."""
        try:
            import ollama
            options = None
            if hasattr(self, "_OllamaOptions") and self._OllamaOptions is not None and kwargs:
                try:
                    options = self._OllamaOptions(**kwargs)
                except Exception:
                    options = None
            response = await ollama.AsyncClient(host=self.host).generate(
                model=self.model_name, 
                prompt=prompt, 
                stream=False, 
                options=options
            )
            if isinstance(response, dict) and 'response' in response:
                return response['response']
            elif hasattr(response, '__aiter__'):
                async for item in response:
                    if isinstance(item, dict) and 'response' in item:
                        return item['response']
                raise ValueError("No 'response' found in Ollama async response iterator")
            else:
                raise TypeError("Unexpected Ollama async response type")
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
            # Always use OpenAI client for openai>=1.0.0
            client = self.openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get("max_tokens", 100),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate text with OpenAI: {e}")

    async def agenerate(self, prompt: str, **kwargs) -> str:
        loop = asyncio.get_running_loop()
        # Pass kwargs as a single dictionary argument to generate

        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))

# DummyBackend for tests and mock generation (define at the end, after all other backends)
class DummyTokenizer:
    def __init__(self):
        self.vocab = {"dummy": 0}
    def encode(self, text: str, return_tensors: object = None) -> object:
        class DummyTensor:
            def __init__(self, data):
                self.data = data
            def to(self, device):
                return self
            def __getitem__(self, idx):
                # Support tuple indices (e.g., [0, -1]) for test compatibility
                if isinstance(idx, tuple):
                    # Return a dummy value for any tuple index
                    return 0
                return self.data[idx]
            def __len__(self):
                return len(self.data)
        return DummyTensor([0])
    def decode(self, tokens: object, skip_special_tokens: bool = True) -> str:
        return "dummy"
    def __len__(self) -> int:
        return len(self.vocab)
    def get_vocab(self) -> dict:
        return self.vocab

class DummyBackend(ModelBackend):
    class DummyModel:
        @property
        def device(self):
            return "cpu"
        def forward(self, *args, **kwargs):
            # Return a dummy object with a .logits attribute for boolean/integer tests
            class Dummy:
                def to(self, device):
                    return self
                def __getitem__(self, idx):
                    return 1
                def __len__(self):
                    return 1
            class DummyOutput:
                @property
                def logits(self):
                    import numpy as np
                    # Return a 2D array (batch_size=1, vocab_size=10) for all test index patterns
                    return np.full((1, 10), 10)
            return DummyOutput()

    def __init__(self) -> None:
        self.tokenizer = DummyTokenizer()
        self.model = self.DummyModel()
    def generate(self, prompt: str, **kwargs: object) -> str:
        # Return a number string if the prompt looks like it expects a number
        lowered = prompt.lower()
        if any(word in lowered for word in ["number", "integer", "float", "age", "factor", "sum", "product"]):
            return "42"
        return "dummy"
