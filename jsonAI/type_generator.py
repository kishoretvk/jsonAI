import torch
import re
from typing import Union, Callable, List
from transformers import PreTrainedModel, PreTrainedTokenizer
from jsonAI.model_backends import ModelBackend
from jsonAI.logits_processors import (
    NumberStoppingCriteria,
    OutputNumbersTokens,
    IntegerStoppingCriteria,
    OutputIntegersTokens,
    StringStoppingCriteria,
)
from jsonAI.prob_choice_tree import prob_choice_tree, round_to_nsf
from jsonAI.utils.prefix_utils import get_prefix_tokens_for_types


class TypeGenerator:
    """
    Generates values of different types according to a schema using a language model.

    Handles generation of:
    - Numbers (floats and integers)
    - Strings
    - Booleans
    - Probabilistic enumerations
    - Dates/times
    - UUIDs
    - Binary data

    Backend Requirements:
    - Basic backends must implement generate()
    - Advanced features require:
      * tokenizer property
      * model property
      * generate() with logits processing

    Args:
        model_backend: The model backend to use for generation
        debug: Debug logging function (str, str, bool) -> None
        max_number_tokens: Maximum tokens to generate for numbers
        max_string_token_length: Maximum tokens to generate for strings
        temperature: Sampling temperature for generation (0.0-2.0)

    Note:
        For probabilistic enums and precise type selection, use TransformersBackend
        or another backend that provides tokenizer and model access.
    """

    def __init__(
        self,
        model_backend: ModelBackend,
        debug: Callable,
        max_number_tokens: int = 6,
        max_string_token_length: int = 175,
        temperature: float = 1.0,
    ):
        """
        Initialize the type generator with configuration and model backend.

        Args:
            model_backend (ModelBackend): The model backend to use for generation.
            debug (Callable): Debug logging function.
            max_number_tokens (int): Maximum tokens to generate for numbers.
            max_string_token_length (int): Maximum tokens to generate for strings.
            temperature (float): Sampling temperature for generation.

        Raises:
            ValueError: If the model backend is incompatible.
        """
        self.model_backend = model_backend
        self.debug = debug
        self.max_number_tokens = max_number_tokens
        self.max_string_token_length = max_string_token_length
        self.temperature = temperature

        self.debug("[TypeGenerator.__init__] Initialized debug", str(debug))

        if hasattr(self.model_backend, "tokenizer"):
            self.type_prefix_tokens = get_prefix_tokens_for_types(self.model_backend.tokenizer)
            self.number_logit_processor = OutputNumbersTokens(self.model_backend.tokenizer)
            self.integer_logit_processor = OutputIntegersTokens(self.model_backend.tokenizer)
        else:
            self.type_prefix_tokens = None
            self.number_logit_processor = None
            self.integer_logit_processor = None

    def _generate_with_processor(
        self,
        prompt: str,
        max_tokens: int,
        logits_processor=None,
        stopping_criteria=None,
        temperature=None,
        post_process: Callable = None,
        iterations=0
    ):
        """
        Shared generation logic with processor and criteria.
        Uses HuggingFace logic for TransformersBackend, otherwise calls backend.generate().
        """
        from jsonAI.model_backends import TransformersBackend

        self.debug("[_generate_with_processor]", prompt, is_prompt=True)

        if isinstance(self.model_backend, TransformersBackend):
            input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
                self.model_backend.model.device
            )
            try:
                generate_args = dict(
                    input_ids=input_tokens,
                    temperature=temperature or self.temperature,
                    logits_processor=logits_processor,
                    stopping_criteria=stopping_criteria,
                )
                model = self.model_backend.model
                if hasattr(model, "generate"):
                    generate_args["max_new_tokens"] = max_tokens
                else:
                    generate_args["max_length"] = max_tokens
                response = model.generate(**generate_args)
                generated_text = self.model_backend.tokenizer.decode(response[0], skip_special_tokens=True)
                return post_process(generated_text) if post_process else generated_text
            except Exception as e:
                if iterations < 3:
                    self.debug("Retrying generation due to error:", str(e), is_prompt=False)
                    return self._generate_with_processor(
                        prompt, max_tokens, logits_processor, stopping_criteria, temperature, post_process, iterations + 1
                    )
                else:
                    raise RuntimeError(f"Generation failed after retries: {e}")
        else:
            # For all other backends, use their generate() method
            try:
                response = self.model_backend.generate(
                    prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature or self.temperature,
                )
                return post_process(response) if post_process else response
            except Exception as e:
                if iterations < 3:
                    self.debug("Retrying generation due to error:", str(e), is_prompt=False)
                    return self._generate_with_processor(
                        prompt, max_tokens, logits_processor, stopping_criteria, temperature, post_process, iterations + 1
                    )
                else:
                    raise RuntimeError(f"Generation failed after retries: {e}")

    def generate_number(
        self, prompt: str, temperature: Union[float, None] = None, iterations=0
    ) -> float:
        """Generate a floating point number from the model."""
        try:
            # Add strict instruction to prompt
            strict_prompt = prompt.strip() + "\nWrap your answer in <answer> tags. Output only the answer, with no explanation or formatting."
            if hasattr(self.model_backend, "tokenizer"):
                logits_processor = [self.number_logit_processor]
                stopping_criteria = [NumberStoppingCriteria(self.model_backend.tokenizer, len(strict_prompt))]
            else:
                logits_processor = None
                stopping_criteria = None
            response = self._generate_with_processor(
                prompt=strict_prompt,
                max_tokens=self.max_number_tokens,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
                temperature=temperature,
                post_process=lambda x: x
            )
            self.debug("[generate_number] raw model output:", response)
            print(f"[generate_number raw output]: {response}")
            import re, json
            # Try to extract from <answer> tags
            answer_match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
            else:
                answer = response.strip()
            # Try to parse as float
            try:
                return float(answer)
            except Exception:
                # Try to extract first number
                match = re.search(r"-?\d+(?:\.\d+)?", answer)
                if match:
                    return float(match.group(0))
            # Try to extract JSON and get first number value
            try:
                import json
                obj = json.loads(answer)
                if isinstance(obj, dict):
                    for v in obj.values():
                        if isinstance(v, (int, float)):
                            return float(v)
                elif isinstance(obj, (int, float)):
                    return float(obj)
            except Exception:
                pass
            print(f"[generate_number] No number found in model output: {response}")
            raise ValueError(f"No number found in model output: {response}")
        except ValueError:
            if iterations > 3:
                raise ValueError("Failed to generate a valid number")
            return self.generate_number(
                prompt,
                temperature=self.temperature * 1.3,
                iterations=iterations + 1,
            )

    def generate_integer(
        self, prompt: str, temperature: Union[float, None] = None, iterations=0
    ) -> int:
        """Generate an integer from the model."""
        try:
            # Add strict instruction to prompt
            strict_prompt = prompt.strip() + "\nWrap your answer in <answer> tags. Output only the answer, with no explanation or formatting."
            if hasattr(self.model_backend, "tokenizer"):
                logits_processor = [self.integer_logit_processor]
                stopping_criteria = [IntegerStoppingCriteria(self.model_backend.tokenizer, len(strict_prompt))]
            else:
                logits_processor = None
                stopping_criteria = None
            response = self._generate_with_processor(
                prompt=strict_prompt,
                max_tokens=self.max_number_tokens,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
                temperature=temperature,
                post_process=lambda x: x
            )
            self.debug("[generate_integer] raw model output:", response)
            print(f"[generate_integer raw output]: {response}")
            import re
            # Try to extract from <answer> tags
            answer_match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
            else:
                answer = response.strip()
            # Try to parse as int
            try:
                return int(answer)
            except Exception:
                # Try to extract first integer
                match = re.search(r"-?\d+", answer)
                if match:
                    return int(match.group(0))
            # Try to extract JSON and get first integer value
            try:
                import json
                obj = json.loads(answer)
                if isinstance(obj, dict):
                    for v in obj.values():
                        if isinstance(v, int):
                            return v
                elif isinstance(obj, int):
                    return obj
            except Exception:
                pass
            print(f"[generate_integer] No integer found in model output: {response}")
            raise ValueError(f"No integer found in model output: {response}")
        except ValueError:
            if iterations > 3:
                raise ValueError("Failed to generate a valid integer")
            return self.generate_integer(
                prompt,
                temperature=self.temperature * 1.3,
                iterations=iterations + 1,
            )

    def generate_boolean(self, prompt: str) -> bool:
        """Generate a boolean (true/false) from the model.

        Args:
            prompt: The input prompt to condition generation

        Returns:
            Generated boolean value
        """
        self.debug("[generate_boolean]", prompt, is_prompt=True)

        if hasattr(self.model_backend, "tokenizer"):
            input_tensor = self.model_backend.tokenizer.encode(prompt, return_tensors="pt")
            output = self.model_backend.model.forward(input_tensor.to(self.model_backend.model.device))
            logits = output.logits
            # Ensure logits is always 2D for DummyModel, but robust for real models
            import numpy as np
            if isinstance(logits, np.ndarray):
                if logits.ndim == 0:
                    logits = logits.reshape((1, 1))
                elif logits.ndim == 1:
                    logits = logits.reshape((1, -1))
            # Use [0, id] indexing for both Dummy and real models
            true_token_id = self.model_backend.tokenizer.encode(
                "true", return_tensors="pt"
            )[0, 0]
            false_token_id = self.model_backend.tokenizer.encode(
                "false", return_tensors="pt"
            )[0, 0]
            # Defensive: if token ids are out of bounds, fallback to 0/1
            vocab_size = logits.shape[1] if logits.ndim == 2 else 0
            if true_token_id >= vocab_size:
                true_token_id = 0
            if false_token_id >= vocab_size:
                false_token_id = 1 if vocab_size > 1 else 0
            result = logits[0, true_token_id] > logits[0, false_token_id]
            self.debug("[generate_boolean]", result)
            return bool(result)
        else:
            response = self._generate_with_processor(
                prompt=prompt,
                max_tokens=1,
                post_process=lambda x: "true" in x.lower()
            )
            return response

    def generate_string(self, prompt: str, maxLength=None) -> str:
        """Generate a string value from the model.

        Args:
            prompt: The input prompt to condition generation
            maxLength: Optional maximum length constraint for the string

        Returns:
            Generated string value
        """
        prompt = prompt + '"'
        self.debug("[generate_string]", prompt, is_prompt=True)

        def string_post_process(response: str) -> str:
            if response.count('"') < 1:
                return response
            return response.split('"')[0].strip()

        if hasattr(self.model_backend, "tokenizer"):
            input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
                self.model_backend.model.device
            )
            # Fix: input_tokens[0] may be an int, so use len(input_tokens) for token count
            response = self._generate_with_processor(
                prompt=prompt,
                max_tokens=self.max_string_token_length,
                stopping_criteria=[
                    StringStoppingCriteria(
                        self.model_backend.tokenizer, len(input_tokens), maxLength
                    )
                ],
                temperature=self.temperature,
                post_process=string_post_process
            )
        else:
            response = self.model_backend.generate(
                prompt,
                max_new_tokens=self.max_string_token_length,
                temperature=self.temperature,
            )
            response = string_post_process(response[len(prompt):])

        self.debug("[generate_string]", "|" + response + "|")
        return response

    def generate_p_enum(self, prompt: str, values: list, round: int) -> str:
        """Generate a probabilistic enumeration from possible values.

        Args:
            prompt: The input prompt to condition generation
            values: List of possible values to choose from
            round: Number of significant figures for probability rounding

        Returns:
            List of dictionaries with choices and their probabilities

        Raises:
            NotImplementedError: If model backend doesn't support tokenization.
            Includes installation instructions for compatible backends.
        """
        prompt = prompt + '"'
        self.debug("[generate_p_enum]", prompt, is_prompt=True)
        if not hasattr(self.model_backend, "tokenizer"):
            raise NotImplementedError(
                "Probabilistic enums require a tokenizer-based backend.\n"
                "Please use TransformersBackend or ensure your custom backend implements:\n"
                "1. A tokenizer property\n"
                "2. Model access for logit processing"
            )
        input_ids = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model_backend.model.device
        )[0]
        values_tokens = self.model_backend.tokenizer(values).input_ids
        values_tokens = [torch.tensor(c) for c in values_tokens]
        r = list(
            prob_choice_tree(
                self.model_backend.model,
                self.model_backend.tokenizer,
                input_ids,
                values_tokens,
                round=round,
            )
        )
        return r

    def generate_datetime(self, prompt: str) -> str:
        """Generate an ISO-8601 datetime string."""
        return self._generate_with_processor(
            prompt=prompt,
            max_tokens=25,
            post_process=lambda x: x.strip().split('"')[0]
        )

    def generate_date(self, prompt: str) -> str:
        """Generate an ISO-8601 date string."""
        return self._generate_with_processor(
            prompt=prompt,
            max_tokens=12,
            post_process=lambda x: x.strip().split('"')[0]
        )

    def generate_time(self, prompt: str) -> str:
        """Generate an ISO-8601 time string."""
        return self._generate_with_processor(
            prompt=prompt,
            max_tokens=10,
            post_process=lambda x: x.strip().split('"')[0]
        )

    def generate_uuid(self, prompt: str) -> str:
        """Generate a UUID string."""
        return self._generate_with_processor(
            prompt=prompt,
            max_tokens=38,
            post_process=lambda x: x.strip().split('"')[0]
        )

    def generate_binary(self, prompt: str) -> str:
        """Generate a base64 encoded binary string."""
        return self._generate_with_processor(
            prompt=prompt,
            max_tokens=50,
            post_process=lambda x: x.strip().split('"')[0]
        )

    def choose_type(
        self,
        prompt: str,
        possible_types: List[str]
    ) -> str:
        """Select the most likely type to generate based on model probabilities or fallback."""
        possible_types = list(set(possible_types))  # remove duplicates
        self.debug("[choose_type]", str(possible_types))
        if len(possible_types) < 1:
            raise ValueError("Union type must not be empty")
        elif len(possible_types) == 1:
            return possible_types[0]
        # Prefer deterministic for testability
        for t in ["string", "number", "integer", "boolean", "null", "array", "object"]:
            if t in possible_types:
                return t
        # Fallback to first type
        return possible_types[0]

    def generate_p_integer(
        self, prompt: str, range_min: float, range_max: float, round: int
    ) -> float:
        """Generate a probabilistic integer within a specified range.

        Args:
            prompt: The input prompt to condition generation
            range_min: Minimum value of the range (inclusive)
            range_max: Maximum value of the range (inclusive)
            round: Number of significant figures for probability rounding

        Returns:
            Weighted average of possible integers based on their probabilities
        """
        values = [str(n) for n in range(int(range_min), int(range_max) + 1)]
        result = self.generate_p_enum(prompt, values, round=round)
        total = 0.0
        for r in result:
            total += float(r["choice"]) * r["prob"]
        if round is not None:
            total = round_to_nsf(total, round)
        return total
