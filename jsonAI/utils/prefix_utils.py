from transformers import PreTrainedTokenizer
from typing import Dict, List
from jsonAI.type_prefixes import TypePrefixIdentifier

def get_prefix_tokens_for_types(
    tokenizer: PreTrainedTokenizer,
) -> Dict[str, List[str]]:
    """
    Extract prefix tokens for various data types from a tokenizer's vocabulary.

    Args:
        tokenizer (PreTrainedTokenizer): The tokenizer to extract prefixes from.

    Returns:
        Dict[str, List[str]]: A dictionary mapping data types to prefix tokens.

    Raises:
        ValueError: If the tokenizer's vocabulary is empty.
    """
    if not tokenizer.vocab:
        raise ValueError("Tokenizer vocabulary is empty.")

    vocab = tokenizer.vocab.items()
    return {
        "number": [v for k, v in vocab if TypePrefixIdentifier.is_number_prefix(k)],
        "boolean": [v for k, v in vocab if TypePrefixIdentifier.is_boolean_prefix(k)],
        "null": [v for k, v in vocab if TypePrefixIdentifier.is_null_prefix(k)],
        "string": [v for k, v in vocab if TypePrefixIdentifier.is_string_prefix(k)],
        "datetime": [v for k, v in vocab if TypePrefixIdentifier.is_datetime_prefix(k)],
        "date": [v for k, v in vocab if TypePrefixIdentifier.is_date_prefix(k)],
        "time": [v for k, v in vocab if TypePrefixIdentifier.is_time_prefix(k)],
        "uuid": [v for k, v in vocab if TypePrefixIdentifier.is_uuid_prefix(k)],
        "binary": [v for k, v in vocab if TypePrefixIdentifier.is_binary_prefix(k)],
    }
