from jaxtyping import Float
import torch
from torch.nn import functional as F
from torch import Tensor
from typing import List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
import math


def round_to_nsf(num, nsf):
    """
    Round a number to a specified number of significant figures.

    Args:
        num (float): The number to round.
        nsf (int): Number of significant figures.

    Returns:
        float: The rounded number.
    """
    if num != 0:
        return round(num, -int(math.floor(math.log10(abs(num))) + 1 - nsf))
    else:
        return 0  # Can't take the log of 0


def get_valid_next_choices(
    choices_tokens: List[Tensor],
    current_tokens: Tensor
):
    """
    Get valid next token choices based on current tokens.

    Args:
        choices_tokens (List[Tensor]): List of token sequences.
        current_tokens (Tensor): Current token sequence.

    Returns:
        torch.LongTensor: Valid next token choices.
    """
    next_choices = []
    for choice_tokens in choices_tokens:
        # if we have some more slots left
        if len(current_tokens) < len(choice_tokens):
            # see if current_tokens matches
            if (
                choice_tokens[: len(current_tokens)] == current_tokens
            ).all():
                c = choice_tokens[len(current_tokens)].item()
                next_choices.append(c)

    return torch.LongTensor(list(set(next_choices)))


def _prob_choice_tree(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    input_ids: Tensor,
    choices_tokens: List[Tensor],
    choice: Optional[Tensor] = None,
    prob: float = 1,
    current_tokens: Tensor = torch.LongTensor([]),
    max_depth: Optional[int] = None,
):
    """
    Recursively generate token sequences with probabilities.

    Args:
        model (AutoModelForCausalLM): Language model.
        tokenizer (AutoTokenizer): Tokenizer.
        input_ids (Tensor): Input token IDs.
        choices_tokens (List[Tensor]): List of token sequences.
        choice (Optional[Tensor]): Current choice token.
        prob (float): Current probability.
        current_tokens (Tensor): Current token sequence.
        max_depth (Optional[int]): Maximum recursion depth.

    Yields:
        dict: Token sequence and probability.
    """
    if max_depth is not None and len(current_tokens) >= max_depth:
        return

    if choice is not None:
        c = choice[None].to(current_tokens.device)
        current_tokens = torch.cat([current_tokens, c], dim=-1)
        c = choice[None].to(input_ids.device)
        input_ids = torch.cat([input_ids, c], dim=-1)

    next_choices = get_valid_next_choices(choices_tokens, current_tokens)
    if len(next_choices) == 0:
        s = tokenizer.decode(current_tokens, skip_special_tokens=True)
        r = dict(prob=prob, choice=s)
        yield r
    else:
        o = model(input_ids[None])
        logits_constrained = o.logits[0, -1][next_choices]
        probs = F.softmax(logits_constrained, dim=-1)
        for i in range(len(next_choices)):
            next_choice_tensor = torch.LongTensor([next_choices[i]])
            next_prob = prob * probs[i].item()
            yield from _prob_choice_tree(
                model=model,
                tokenizer=tokenizer,
                choices_tokens=choices_tokens,
                input_ids=input_ids,
                choice=next_choice_tensor,
                prob=next_prob,
                current_tokens=current_tokens,
                max_depth=max_depth,
            )


def prob_choice_tree(
    *args,
    sort: bool = True,
    round=3,
    max_depth: Optional[int] = None,
    **kwargs,
):
    """
    Generate token sequences with probabilities.

    Args:
        sort (bool): Whether to sort results by probability.
        round (int): Number of significant figures for probabilities.
        max_depth (Optional[int]): Maximum recursion depth.

    Returns:
        List[dict]: List of token sequences and probabilities.
    """
    choice_json = list(
        _prob_choice_tree(
            *args,
            max_depth=max_depth,
            **kwargs,
        )
    )

    # order by probability
    if sort:
        choice_json = sorted(choice_json, key=lambda x: -x["prob"])

    # round probabilities
    for c in choice_json:
        c["prob"] = round_to_nsf(c["prob"], round)
    return choice_json
