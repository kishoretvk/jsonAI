from transformers import PreTrainedTokenizer
from typing import Dict, List
import re

def is_number_prefix(s: str) -> bool:
    return re.match(r"^[\-\d]+\.?[\d]*$", s)

def is_boolean_prefix(s: str) -> bool:
    return 'true'.startswith(s) or 'false'.startswith(s)

def is_null_prefix(s: str) -> bool:
    return 'null'.startswith(s)

def is_string_prefix(s: str) -> bool:
    return re.match(r'^"[^"]*"?$', s)

def is_array_prefix(s: str) -> bool:
    return re.match(r'^\[["\-\d\[{]*$', s)

def is_object_prefix(s: str) -> bool:
    return re.match(r'^\{"?$', s)

def is_datetime_prefix(s: str) -> bool:
    return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s)

def is_date_prefix(s: str) -> bool:
    return re.match(r'^\d{4}-\d{2}-\d{2}$', s)

def is_time_prefix(s: str) -> bool:
    return re.match(r'^\d{2}:\d{2}:\d{2}$', s)

def is_uuid_prefix(s: str) -> bool:
    return re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s)

def is_binary_prefix(s: str) -> bool:
    return re.match(r'^[A-Za-z0-9+/]+={0,2}$', s)


def get_prefix_tokens_for_types(tokenizer: PreTrainedTokenizer) -> Dict[str, List[str]]:
    vocab = tokenizer.vocab.items()
    return {
        "number": [v for k, v in vocab if is_number_prefix(k)],
        "boolean": [v for k, v in vocab if is_boolean_prefix(k)],
        "null": [v for k, v in vocab if is_null_prefix(k)],
        "string": [v for k, v in vocab if is_string_prefix(k)],
        "datetime": [v for k, v in vocab if is_datetime_prefix(k)],
        "date": [v for k, v in vocab if is_date_prefix(k)],
        "time": [v for k, v in vocab if is_time_prefix(k)],
        "uuid": [v for k, v in vocab if is_uuid_prefix(k)],
        "binary": [v for k, v in vocab if is_binary_prefix(k)],
    }

