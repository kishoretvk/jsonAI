import torch
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

        Args:
            prompt (str): Input prompt to generate from.
            max_tokens (int): Maximum tokens to generate.
            logits_processor (Callable): Optional logits processor.
            stopping_criteria (Callable): Optional stopping criteria.
            temperature (float): Sampling temperature.
            post_process (Callable): Function to post-process generated text.
            iterations (int): Retry counter for error handling.

        Returns:
            str: Generated text after applying processors and post-processing.

        Raises:
            RuntimeError: If generation fails after retries.
        """
        self.debug("[_generate_with_processor]", prompt, is_prompt=True)

        if not hasattr(self.model_backend, "tokenizer"):
            raise ValueError("Model backend does not support tokenization.")

        input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model_backend.model.device
        )

        try:
            response = self.model_backend.model.generate(
                input_tokens,
                max_length=max_tokens,
                temperature=temperature or self.temperature,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
            )
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

    def generate_number(
        self, prompt: str, temperature: Union[float, None] = None, iterations=0
    ) -> float:
        """Generate a floating point number from the model.

        Args:
            prompt: The input prompt to condition generation
            temperature: Sampling temperature (higher = more random)
            iterations: Internal retry counter for error handling

        Returns:
            Generated number as float

        Raises:
            ValueError: If generation fails after max retries
        """
        try:
            response = self._generate_with_processor(
                prompt=prompt,
                max_tokens=self.max_number_tokens,
                logits_processor=[self.number_logit_processor],
                stopping_criteria=[
                    NumberStoppingCriteria(self.model_backend.tokenizer, len(prompt))
                ],
                temperature=temperature,
                post_process=lambda x: x.replace(" ", "").rstrip(".").split(",")[0]
            )
            self.debug("[generate_number]", response)
            return float(response)
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
        """Generate an integer from the model.

        Args:
            prompt: The input prompt to condition generation
            temperature: Sampling temperature (higher = more random)
            iterations: Internal retry counter for error handling

        Returns:
            Generated number as integer

        Raises:
            ValueError: If generation fails after max retries
        """
        try:
            response = self._generate_with_processor(
                prompt=prompt,
                max_tokens=self.max_number_tokens,
                logits_processor=[self.integer_logit_processor],
                stopping_criteria=[
                    IntegerStoppingCriteria(self.model_backend.tokenizer, len(prompt))
                ],
                temperature=temperature,
                post_process=lambda x: x.replace(" ", "").split(",")[0]
            )
            self.debug("[generate_integer]", response)
            return int(response)
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
            logits = output.logits[0, -1]

            true_token_id = self.model_backend.tokenizer.encode(
                "true", return_tensors="pt"
            )[0, 0]
            false_token_id = self.model_backend.tokenizer.encode(
                "false", return_tensors="pt"
            )[0, 0]

            result = logits[true_token_id] > logits[false_token_id]
            self.debug("[generate_boolean]", result)
            return result.item()
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
            response = self._generate_with_processor(
                prompt=prompt,
                max_tokens=self.max_string_token_length,
                stopping_criteria=[
                    StringStoppingCriteria(
                        self.model_backend.tokenizer, len(input_tokens[0]), maxLength
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
        """Select the most likely type to generate based on model probabilities.

        For backends with tokenizers: Uses model logits to select the most probable type.
        For other backends: Uses weighted random selection based on type frequency.

        Args:
            prompt: The input prompt to condition generation
            possible_types: List of possible schema types to choose from

        Returns:
            The selected type name

        Raises:
            ValueError: If no valid type can be chosen or types are unsupported
        """
        possible_types = list(set(possible_types))  # remove duplicates
        self.debug("[choose_type]", str(possible_types))

        if len(possible_types) < 1:
            raise ValueError("Union type must not be empty")
        elif len(possible_types) == 1:
            return possible_types[0]

        # For backends without tokenizers
        if not hasattr(self.model_backend, "tokenizer"):
            self.debug("[choose_type]", "Using weighted random fallback")
            import random
            # Simple weighted random selection favoring more common types
            weights = {
                "string": 5,
                "number": 4,
                "integer": 3,
                "boolean": 2,
                "array": 1,
                "object": 1
            }
            valid_types = [t for t in possible_types if t in weights]
            if not valid_types:
                raise ValueError(f"No supported types in: {possible_types}")
            return random.choices(valid_types, weights=[weights[t] for t in valid_types])[0]

        # Original tokenizer-based implementation
        try:
            input_tensor = self.model_backend.tokenizer.encode(
                prompt,
                return_tensors="pt"
            )
            output = self.model_backend.model.forward(
                input_tensor.to(self.model_backend.model.device)
            )
            logits = output.logits[0, -1]

            max_type = None
            max_logit = -float("inf")
            for possible_type in possible_types:
                try:
                    prefix_tokens = self.type_prefix_tokens[possible_type]
                    max_type_logit = logits[prefix_tokens].max()
                    if max_type_logit > max_logit:
                        max_type = possible_type
                        max_logit = max_type_logit
                except KeyError:
                    raise ValueError(f"Unsupported schema type: {possible_type}")

            if max_type is None:
                raise ValueError("Unable to determine type to generate")

            self.debug("[choose_type]", max_type)
            return max_type
        except Exception as e:
            self.debug("[choose_type:error]", str(e))
            raise ValueError(f"Type selection failed: {str(e)}")

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
