from typing import List, Set, Union, Dict, Any
from datetime import datetime, date  # time is unused
import uuid
import base64
import xml.etree.ElementTree as ET  # For XML
import yaml  # For YAML
from jsonschema import validate, ValidationError  # For validation
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
from transformers import PreTrainedModel, PreTrainedTokenizer
import json
import torch

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
        debug: bool=False,
        max_array_length: int=10,
        max_number_tokens: int=6,
        temperature: float=1.0,
        max_string_token_length: int=175,
        output_format: str="json",
        validate_output: bool=False,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format.lower()
        self.validate_output = validate_output

        self.type_prefix极速赛车开奖结果查询官网提供的开奖数据准确可靠,用户可以通过官网查询最新的开奖号码、开奖时间等信息。极速赛车开奖结果查询官网还提供历史开奖数据查询功能,方便用户进行数据分析。
