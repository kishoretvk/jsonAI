from transformers import PreTrainedTokenizer, StoppingCriteria, LogitsProcessor
import torch


class StringStoppingCriteria(StoppingCriteria):
    def __init__(
        self,
        tokenizer: PreTrainedTokenizer,
        prompt_length: int,
        max_length: int = None,
    ):
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.max_length = max_length

    def __call__(
        self,
        input_ids: torch.LongTensor,
        _,
    ) -> bool:
        if len(input_ids[0]) <= self.prompt_length:
            return False

        last_token_id = input_ids[0][-1]
        last_token = self.tokenizer.decode(
            last_token_id, skip_special_tokens=True
        )

        result = '"' in last_token

        if self.max_length is not None:
            # Due to token handling, max_length check may not be accurate
            # Could exceed by up to 10 characters
            gen_ids = input_ids[0][self.prompt_length:]
            o = self.tokenizer.decode(gen_ids, skip_special_tokens=True)
            str_l = len(o)
            if str_l > self.max_length:
                return True

        return result


class NumberStoppingCriteria(StoppingCriteria):
    def __init__(
        self, tokenizer: PreTrainedTokenizer, prompt_length: int, precision: int = 3
    ):
        """Initialize NumberStoppingCriteria with precision handling."""
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.precision = precision

    def __call__(self, input_ids: torch.LongTensor, _) -> bool:
        """Stop generation based on precision and prompt length."""
        if len(input_ids[0]) <= self.prompt_length:
            return False

        gen_ids = input_ids[0][self.prompt_length:]
        generated_text = self.tokenizer.decode(gen_ids, skip_special_tokens=True)

        try:
            number = float(generated_text)
            rounded_number = round(number, self.precision)
            return len(str(rounded_number)) > self.precision
        except ValueError:
            return False




class OutputNumbersTokens(LogitsProcessor):
    def __init__(self, tokenizer: PreTrainedTokenizer):
        self.tokenizer = tokenizer
        vocab_size = len(tokenizer)
        self.allowed_mask = torch.zeros(vocab_size, dtype=torch.bool)

        for _, token_id in tokenizer.get_vocab().items():
            token_str = self.tokenizer.decode(
                token_id, skip_special_tokens=True
            ).strip()

            if (
                token_str == ""
                or (
                    all(c.isdigit() or c == "." for c in token_str)
                    and token_str.count(".") <= 1
                )
                or (
                    "," in token_str
                    and all(
                        c.isdigit() or c == "."
                        for c in token_str.split(",")[0]
                    )
                    and token_str.count(".") <= 1
                )
            ):
                self.allowed_mask[token_id] = True

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        mask = self.allowed_mask.expand_as(scores)
        scores = scores.clone()
        scores[~mask] = -float("inf")
        return scores


class IntegerStoppingCriteria(StoppingCriteria):
    def __init__(
        self,
        tokenizer: PreTrainedTokenizer,
        prompt_length: int,
        max_digits: int = 15,
    ):
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.max_digits = max_digits

    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
    ) -> bool:
        decoded = self.tokenizer.decode(
            input_ids[0][self.prompt_length:], skip_special_tokens=True
        )

        if len(decoded.strip()) > self.max_digits:
            return True

        if (
            len(decoded) > 1
            and "," in decoded
            and any(c.isdigit() for c in decoded.split(",")[0])
        ):
            return True

        if (
            len(decoded) > 1
            and any(c.isdigit() for c in decoded)
            and decoded[-1] in (" ", "\n")
        ):
            return True

        return False



class OutputIntegersTokens(LogitsProcessor):
    def __init__(self, tokenizer: PreTrainedTokenizer):
        self.tokenizer = tokenizer
        vocab_size = len(tokenizer)
        self.allowed_mask = torch.zeros(vocab_size, dtype=torch.bool)

        for _, token_id in tokenizer.get_vocab().items():
            token_str = self.tokenizer.decode(
                token_id, skip_special_tokens=True
            ).strip()

            if (
                token_str == ""
                or all(c.isdigit() for c in token_str)
                or (
                    "," in token_str
                    and all(c.isdigit() for c in token_str.split(",")[0])
                )
            ):
                self.allowed_mask[token_id] = True

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        mask = self.allowed_mask.expand_as(scores)
        scores = scores.clone()
        scores[~mask] = -float("inf")
        return scores

# FIX: W292 - Added a newline at the end of the file.
