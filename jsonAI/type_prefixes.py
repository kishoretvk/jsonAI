from transformers import PreTrainedTokenizer
from typing import Dict, List
import re


class TypePrefixIdentifier:
    """
    A class for identifying prefixes of various data types.
    """

    @staticmethod
    def is_number_prefix(s: str) -> bool:
        return re.match(r"^[\-\d]+\.?[\d]*$", s)

    @staticmethod
    def is_boolean_prefix(s: str) -> bool:
        return 'true'.startswith(s) or 'false'.startswith(s)

    @staticmethod
    def is_null_prefix(s: str) -> bool:
        return 'null'.startswith(s)

    @staticmethod
    def is_string_prefix(s: str) -> bool:
        return re.match(r'^"[^"]*"?$', s)

    @staticmethod
    def is_array_prefix(s: str) -> bool:
        return re.match(r'^\["\-\d\[{]*$', s)

    @staticmethod
    def is_object_prefix(s: str) -> bool:
        return re.match(r'^\{"?$', s)

    @staticmethod
    def is_datetime_prefix(s: str) -> bool:
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s)

    @staticmethod
    def is_date_prefix(s: str) -> bool:
        return re.match(r'^\d{4}-\d{2}-\d{2}$', s)

    @staticmethod
    def is_time_prefix(s: str) -> bool:
        return re.match(r'^\d{2}:\d{2}:\d{2}$', s)

    @staticmethod
    def is_uuid_prefix(s: str) -> bool:
        return re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            s,
        )

    @staticmethod
    def is_binary_prefix(s: str) -> bool:
        return re.match(r'^[A-Za-z0-9+/]+={0,2}$', s)


class TypePrefixExtractor:
    """
    A class for extracting prefix tokens for various data types from a tokenizer.
    """

    @staticmethod
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
