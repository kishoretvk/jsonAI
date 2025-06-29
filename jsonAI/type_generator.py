import torch
from typing import Union, Callable
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
from jsonAI.type_prefixes import get_prefix_tokens_for_types


class TypeGenerator:
    def __init__(
        self,
        model_backend: ModelBackend,
        debug: Callable,
        max_number_tokens: int = 6,
        max_string_token_length: int = 175,
        temperature: float = 1.0,
    ):
        self.model_backend = model_backend
        self.debug = debug
        self.max_number_tokens = max_number_tokens
        self.max_string_token_length = max_string_token_length
        self.temperature = temperature

        if hasattr(self.model_backend, "tokenizer"):
            self.type_prefix_tokens = get_prefix_tokens_for_types(self.model_backend.tokenizer)
            self.number_logit_processor = OutputNumbersTokens(self.model_backend.tokenizer)
            self.integer_logit_processor = OutputIntegersTokens(self.model_backend.tokenizer)
        else:
            self.type_prefix_tokens = None
            self.number_logit_processor = None
            self.integer_logit_processor = None

    def generate_number(
        self, prompt: str, temperature: Union[float, None] = None, iterations=0
    ) -> float:
        self.debug("[generate_number]", prompt, is_prompt=True)
        
        if hasattr(self.model_backend, "tokenizer"):
            input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
                self.model_backend.model.device
            )
            response = self.model_backend.model.generate(
                input_tokens,
                max_new_tokens=self.max_number_tokens,
                num_return_sequences=1,
                logits_processor=[self.number_logit_processor],
                stopping_criteria=[
                    NumberStoppingCriteria(self.model_backend.tokenizer, len(input_tokens[0]))
                ],
                temperature=temperature or self.temperature,
                pad_token_id=self.model_backend.tokenizer.eos_token_id,
            )
            response = self.model_backend.tokenizer.decode(response[0], skip_special_tokens=True)
        else:
            response = self.model_backend.generate(
                prompt,
                max_new_tokens=self.max_number_tokens,
                temperature=temperature or self.temperature,
            )

        response = response[len(prompt):]
        if "," in response:
            response = response.split(",")[0]
        response = response.replace(" ", "").rstrip(".")
        self.debug("[generate_number]", response)
        try:
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
        self.debug("[generate_integer]", prompt, is_prompt=True)
        if hasattr(self.model_backend, "tokenizer"):
            input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
                self.model_backend.model.device
            )
            response = self.model_backend.model.generate(
                input_tokens,
                max_new_tokens=self.max_number_tokens,
                num_return_sequences=1,
                logits_processor=[self.integer_logit_processor],
                stopping_criteria=[
                    IntegerStoppingCriteria(self.model_backend.tokenizer, len(input_tokens[0]))
                ],
                temperature=temperature or self.temperature,
                pad_token_id=self.model_backend.tokenizer.eos_token_id,
            )
            response = self.model_backend.tokenizer.decode(response[0], skip_special_tokens=True)
        else:
            response = self.model_backend.generate(
                prompt,
                max_new_tokens=self.max_number_tokens,
                temperature=temperature or self.temperature,
            )

        response = response[len(prompt):]
        if "," in response:
            response = response.split(",")[0]
        response = response.replace(" ", "")
        self.debug("[generate_integer]", response)
        try:
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
            response = self.model_backend.generate(prompt, max_new_tokens=1)
            return "true" in response.lower()

    def generate_string(self, prompt: str, maxLength=None) -> str:
        prompt = prompt + '"'
        self.debug("[generate_string]", prompt, is_prompt=True)
        if hasattr(self.model_backend, "tokenizer"):
            input_tokens = self.model_backend.tokenizer.encode(prompt, return_tensors="pt").to(
                self.model_backend.model.device
            )
            response = self.model_backend.model.generate(
                input_tokens,
                max_new_tokens=self.max_string_token_length,
                num_return_sequences=1,
                temperature=self.temperature,
                stopping_criteria=[
                    StringStoppingCriteria(
                        self.model_backend.tokenizer, len(input_tokens[0]), maxLength
                    )
                ],
                pad_token_id=self.model_backend.tokenizer.eos_token_id,
            )
            if (
                len(response[0]) >= len(input_tokens[0])
                and (response[0][:len(input_tokens[0])] == input_tokens).all()
            ):
                response = response[0][len(input_tokens[0]):]
            if response.shape[0] == 1:
                response = response[0]
            response = self.model_backend.tokenizer.decode(response, skip_special_tokens=True)
        else:
            response = self.model_backend.generate(
                prompt,
                max_new_tokens=self.max_string_token_length,
                temperature=self.temperature,
            )
        self.debug("[generate_string]", "|" + response + "|")
        if response.count('"') < 1:
            return response
        return response.split('"')[0].strip()

    def generate_p_enum(self, prompt: str, values: list, round: int) -> str:
        prompt = prompt + '"'
        self.debug("[generate_p_enum]", prompt, is_prompt=True)
        if not hasattr(self.model_backend, "tokenizer"):
            raise NotImplementedError("p_enum is not supported for this model backend")
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

    def generate_p_integer(
        self, prompt: str, range_min: float, range_max: float, round: int
    ) -> float:
        values = [str(n) for n in range(int(range_min), int(range_max) + 1)]
        result = self.generate_p_enum(prompt, values, round=round)
        total = 0.0
        for r in result:
            total += float(r["choice"]) * r["prob"]
        if round is not None:
            total = round_to_nsf(total, round)
        return total
