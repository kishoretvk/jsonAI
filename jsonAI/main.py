from typing import List, Set, Union, Dict, Any
from jsonAI.type_generator import TypeGenerator
from jsonAI.output_formatter import OutputFormatter
from jsonAI.schema_validator import SchemaValidator
from termcolor import cprint
from transformers import PreTrainedModel, PreTrainedTokenizer
import json

GENERATION_MARKER = "|GENERATION|"

class Jsonformer:
    value: Dict[str, Any] = {}

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        json_schema: Dict[str, Any],
        prompt: str,
        *,
        output_format: str = "json",
        validate_output: bool = False,
        debug: bool = False,
        max_array_length: int = 10,
        max_number_tokens: int = 6,
        temperature: float = 1.0,
        max_string_token_length:极
