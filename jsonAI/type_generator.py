import torch
from typing import Union
from transformers import PreTrainedModel, PreTrainedTokenizer
from jsonAI.logits_processors import (
    NumberStoppingCriteria,
    OutputNumbersTokens,
    IntegerStoppingCriteria,
    OutputIntegersTokens,
    StringStoppingCriteria,
)
from jsonAI.prob_choice_tree import prob_choice_tree, round_to_nsf
from jsonAI.type_prefixes import get_prefix_tokens_for_types
from termcolor import cprint


class TypeGenerator:
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        debug: bool = False,
        max_number_tokens: int = 6,
        max_string_token_length: int = 175,
        temperature: float = 1.0,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.debug_on = debug
        self.max_number_tokens = max_number_tokens
        self.max_string_token_length = max_string_token_length
        self.temperature = temperature

        self.type_prefix_tokens = get_prefix_tokens_for_types(tokenizer)
        self.number_logit_processor = OutputNumbersTokens(tokenizer)
        self.integer_logit_processor = OutputIntegersTokens(tokenizer)

    def debug(self, caller: str, value: str, is_prompt: bool = False):
        if self.debug_on:
            if is_prompt:
                cprint(caller, "green", end=" ")
                cprint(value, "yellow")
            else:
                cprint(caller, "green", end=" ")
                cprint(value, "blue")

    def generate_number(
        self, prompt: str, temperature: Union[float, None] = None, iterations=0
    ) -> float:
        self.debug("[generate_number]", prompt, is_prompt=True)
        input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )
        response = self.model.generate(
            input_tokens,
            max_new_tokens=self.max_number_tokens,
            num_return_sequences=1,
            logits_processor=[self.number_logit_processor],
            stopping_criteria=[
                NumberStoppingCriteria(self.tokenizer, len(input_tokens[0]))
            ],
            temperature=temperature or self.temperature,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        response = self.tokenizer.decode(response[0], skip_special_tokens=True)

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
        input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )
        response = self.model.generate(
            input_tokens,
            max_new_tokens=self.max_number_tokens,
            num_return_sequences=1,
            logits_processor=[self.integer_logit_processor],
            stopping_criteria=[
                IntegerStoppingCriteria(self.tokenizer, len(input_tokens[0]))
            ],
            temperature=temperature or self.temperature,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        response = self.tokenizer.decode(response[0], skip_special_tokens=True)

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

        input_tensor = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.forward(input_tensor.to(self.model.device))
        logits = output.logits[0, -1]

        true_token_id = (
            self.tokenizer.encode("true", return_tensors="pt")[0, 0]
        )
        false_token_id = (
            self.tokenizer.encode("false", return_tensors="pt")[0, 0]
        )

        result = logits[true_token_id] > logits[false_token_id]

        self.debug("[generate_boolean]", result)

        return result.item()

    def generate_string(self, prompt: str, maxLength=None) -> str:
        prompt = prompt + '"'
        self.debug("[generate_string]", prompt, is_prompt=True)
        input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )

        response = self.model.generate(
            input_tokens,
            max_new_tokens=self.max_string_token_length,
            num_return_sequences=1,
            temperature=self.temperature,
            stopping_criteria=[
                StringStoppingCriteria(
                    self.tokenizer, len(input_tokens[0]), maxLength
                )
            ],
            pad_token_id=self.tokenizer.eos_token_id,
        )

        if (
            len(response[0]) >= len(input_tokens[0])
            and (response[0][: len(input_tokens[0])] == input_tokens).all()
        ):
            response = response[0][len(input_tokens[0]):]
        if response.shape[0] == 1:
            response = response[0]

        response = self.tokenizer.decode(response, skip_special_tokens=True)

        self.debug("[generate_string]", "|" + response + "|")

        if response.count('"') < 1:
            return response

        return response.split('"')[0].strip()

    def generate_p_enum(self, prompt: str, values: list, round: int) -> str:
        prompt = prompt + '"'
        self.debug("[generate_p_enum]", prompt, is_prompt=True)
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )[0]
        values_tokens = self.tokenizer(values).input_ids
        values_tokens = [torch.tensor(c) for c in values_tokens]

        r = list(
            prob_choice_tree(
                self.model,
                self.tokenizer,
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