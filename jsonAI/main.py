from typing import List, Set, Union, Dict, Any
from datetime import datetime, date, time
import uuid
import base64
import xml.etree.ElementTree as ET # Import for XML
import yaml # Import for YAML
from jsonschema import validate, ValidationError # Import for validation
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
        debug: bool = False,
        max_array_length: int = 10,
        max_number_tokens: int = 6,
        temperature: float = 1.0,
        max_string_token_length: int = 175,
        output_format: str = "json", # Add output format parameter
        validate_output: bool = False, # Add validation parameter
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format.lower() # Store output format
        self.validate_output = validate_output # Store validation flag

        self.type_prefix_tokens = get_prefix_tokens_for_types(tokenizer)

        self.number_logit_processor = OutputNumbersTokens(self.tokenizer, self.prompt)
        self.integer_logit_processor = OutputIntegersTokens(self.tokenizer, self.prompt)

        self.generation_marker = "|GENERATION|"
        self.debug_on = debug
        self.max_array_length = max_array_length

        self.max_number_tokens = max_number_tokens
        self.temperature = temperature
        self.max_string_token_length = max_string_token_length

    def debug(self, caller: str, value: str, is_prompt: bool = False):
        if self.debug_on:
            if is_prompt:
                cprint(caller, "green", end=" ")
                cprint(value, "yellow")
            else:
                cprint(caller, "green", end=" ")
                cprint(value, "blue")

    def generate_datetime(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_datetime]", prompt, is_prompt=True)
        return datetime.now().isoformat()

    def generate_date(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_date]", prompt, is_prompt=True)
        return date.today().isoformat()

    def generate_time(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_time]", prompt, is_prompt=True)
        return datetime.now().time().isoformat()
    
    def generate_uuid(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
        self.debug("[generate_uuid]", prompt, is_prompt=True)
        # Directly generate a valid UUID
        uuid_str = str(uuid.uuid4())
        self.debug("[generate_uuid]", uuid_str)
        return uuid_str
   

    def generate_number(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
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
                raise ValueError(f"Failed to generate a valid number after multiple attempts for prompt: '{self.prompt}'")

            return self.generate_number(
                temperature=self.temperature * 1.3, iterations=iterations + 1
            )

    def generate_integer(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
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
                raise ValueError(f"Failed to generate a valid integer after multiple attempts for prompt: '{self.prompt}'")

            return self.generate_integer(temperature=self.temperature * 1.3)

    def generate_binary(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_binary]", prompt, is_prompt=True)
        return base64.b64encode(b"example binary data").decode('utf-8')


    def generate_boolean(self) -> bool:
        prompt = self.get_prompt()
        self.debug("[generate_boolean]", prompt, is_prompt=True)

        input_tensor = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.forward(input_tensor.to(self.model.device))
        logits = output.logits[0, -1]

        true_token_id = self.tokenizer.encode("true", return_tensors="pt")[0, 0]
        false_token_id = self.tokenizer.encode("false", return_tensors="pt")[0, 0]

        result = logits[true_token_id] > logits[false_token_id]

        self.debug("[generate_boolean]", result)

        return result.item()

    def generate_string(self, maxLength=None) -> str:
        prompt = self.get_prompt() + '"'
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
                StringStoppingCriteria(self.tokenizer, len(input_tokens[0]), maxLength)
            ],
            pad_token_id=self.tokenizer.eos_token_id,
        )

        if (
            len(response[0]) >= len(input_tokens[0])
            and (response[0][: len(input_tokens[0])] == input_tokens).all()
        ):
            response = response[0][len(input_tokens[0]) :]
        if response.shape[0] == 1:
            response = response[0]

        response = self.tokenizer.decode(response, skip_special_tokens=True)

        self.debug("[generate_string]", "|" + response + "|")

        if response.count('"') < 1:
            return response

        return response.split('"')[0].strip()

    def generate_p_enum(self, values: list, round: int) -> str:
        prompt = self.get_prompt() + '"'
        self.debug("[generate_p_enum]", prompt, is_prompt=True)
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )[0]
        values_tokens = self.tokenizer(values).input_ids
        values_tokens = [torch.tensor(c) for c in values_tokens]

        r = list(
            prob_choice_tree(
                self.model, self.tokenizer, input_ids, values_tokens, round=round
            )
        )
        return r

    def generate_p_integer(
        self, range_min: float, range_max: float, round: int
    ) -> float:
        values = [str(n) for n in range(int(range_min), int(range_max) + 1)]
        result = self.generate_p_enum(values, round=round)

        total = 0.0
        for r in result:
            total += float(r["choice"]) * r["prob"]

        if round is not None:
            total = round_to_nsf(total, round)
        return total

    def generate_enum(self, enum_values: Set[str]) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_enum]", prompt, is_prompt=True)

        terminal_tokens = torch.concat(
            [
                self.tokenizer.encode(s, add_special_tokens=False, return_tensors="pt")[
                    :, 0
                ]
                for s in ('", "', '"}', '"]')
            ]
        )

        highest_probability = 0.0
        best_option = None
        for option in enum_values:
            n_option_tokens = self.tokenizer.encode(
                f'"{option}', add_special_tokens=False, return_tensors="pt"
            ).shape[1]
            prompt_tokens = self.tokenizer.encode(
                prompt + f'"{option}', return_tensors="pt"
            )
            option_tokens = prompt_tokens[0, -n_option_tokens:]

            with torch.no_grad():
                logits = self.model.forward(prompt_tokens.to(self.model.device)).logits[
                    0, -n_option_tokens - 1 :
                ]
            probabilities = torch.softmax(logits, dim=1)
            option_token_probabilities = probabilities[:-1][
                torch.arange(probabilities.shape[0] - 1), option_tokens
            ]

            termination_probability = torch.max(probabilities[-1, terminal_tokens])
            option_probability = (
                torch.prod(option_token_probabilities) * termination_probability
            )
            self.debug("[generate_enum]", f"{option_probability}, {option}")

            if option_probability > highest_probability:
                best_option = option
                highest_probability = option_probability

        self.debug("[generate_enum]", best_option)

        return best_option

    def generate_object(
        self, properties: Dict[str, Any], obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        for key, schema in properties.items():
            self.debug("[generate_object] generating value for", key)
            obj[key] = self.generate_value(schema, obj, key)
        return obj

    def generate_array(self, item_schema: Dict[str, Any], obj: Dict[str, Any]) -> list:
        for _ in range(self.max_array_length):
            element = self.generate_value(item_schema, obj)
            obj[-1] = element

            obj.append(self.generation_marker)
            input_prompt = self.get_prompt()
            obj.pop()
            input_tensor = self.tokenizer.encode(input_prompt, return_tensors="pt")
            output = self.model.forward(input_tensor.to(self.model.device))
            logits = output.logits[0, -1]

            top_indices = logits.topk(30).indices
            sorted_token_ids = top_indices[logits[top_indices].argsort(descending=True)]

            found_comma = False
            found_close_bracket = False

            for token_id in sorted_token_ids:
                decoded_token = self.tokenizer.decode(
                    token_id, skip_special_tokens=True
                )
                if "," in decoded_token:
                    found_comma = True
                    break
                if "]" in decoded_token:
                    found_close_bracket = True
                    break

            if found_close_bracket or not found_comma:
                break

        return obj

    def choose_type_to_generate(self, possible_types: List[str]) -> str:
        possible_types = list(set(possible_types))  # remove duplicates
        self.debug("[choose_type_to_generate]", possible_types)
        if len(possible_types) < 1:
            raise ValueError(f"Union type must not be empty")
        elif len(possible_types) == 1:
            return possible_types[0]

        prompt = self.get_prompt()
        input_tensor = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.forward(input_tensor.to(self.model.device))
        logits = output.logits[0, -1]

        max_type = None
        max_logit = -float("inf")
        for possible_type in possible_types:
            try:
                prefix_tokens = self.type_prefix_tokens[possible_type]
            except KeyError:
                raise ValueError(f"Unsupported schema type: {possible_type}")
            max_type_logit = logits[prefix_tokens].max()
            if max_type_logit > max_logit:
                max_type = possible_type
                max_logit = max_type_logit

        if max_type is None:
            raise Exception("Unable to find best type to generate for union type")
        self.debug("[choose_type_to_generate]", max_type)
        return max_type

    def generate_value(
        self,
        schema: Dict[str, Any],
        obj: Union[Dict[str, Any], List[Any]],
        key: Union[str, None] = None,
    ) -> Any:
        schema_type = schema["type"]
        if isinstance(schema_type, list):
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            schema_type = self.choose_type_to_generate(schema_type)
        if schema_type == "number":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_number()
        elif schema_type == "integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_integer()
        elif schema_type == "boolean":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_boolean()
        elif schema_type == "string":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_string(
                schema["maxLength"] if "maxLength" in schema else None
            )
        elif schema_type == "datetime":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_datetime()
        elif schema_type == "date":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_date()
        elif schema_type == "time":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_time()
        elif schema_type == "uuid":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_uuid()
        elif schema_type == "binary":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_binary()
        elif schema_type == "p_enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_p_enum(schema["values"], round=schema.get("round", 3))
        elif schema_type == "p_integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_p_integer(
                schema["minimum"], schema["maximum"], round=schema.get("round", 3)
            )
        elif schema_type == "enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_enum(set(schema["values"]))
        elif schema_type == "array":
            new_array = []
            obj[key] = new_array
            return self.generate_array(schema["items"], new_array)
        elif schema_type == "object":
            new_obj = {}
            if key:
                obj[key] = new_obj
            else:
                obj.append(new_obj)
            return self.generate_object(schema["properties"], new_obj)
        elif schema_type == "null":
            return None
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_prompt(self):
        template = """{prompt}\nOutput result in the following JSON schema format:\n```json{schema}```\nResult: ```json\n{progress}"""
        value = self.value

        progress = json.dumps(value)
        gen_marker_index = progress.find(f'"{self.generation_marker}"')
        if gen_marker_index != -1:
            progress = progress[:gen_marker_index]
        else:
            raise ValueError("Failed to find generation marker")

        prompt = template.format(
            prompt=self.prompt,
            schema=json.dumps(self.json_schema),
            progress=progress,
        )

        return prompt

    def __call__(self) -> Dict[str, Any]:
        self.value = {}
    def _to_xml(self, data, element_name="item"):
        # Helper function to convert Python dict/list/primitive to XML Element
        if isinstance(data, dict):
            element = ET.Element(element_name)
            for key, value in data.items():
                child = self._to_xml(value, key)
                element.append(child)
            return element
        elif isinstance(data, list):
            # For lists, create a container element and add each item
            element = ET.Element(element_name)
            for item in data:
                 # Use a generic item name for list items
                 item_element = self._to_xml(item, "item") # Using "item" as default list item name
                 element.append(item_element)
            return element
        else:
            # For primitive types
            element = ET.Element(element_name)
            element.text = str(data)
            return element

    def __call__(self) -> Union[Dict[str, Any], str]:
        self.value = {}
        generated_data = self.generate_object(
            self.json_schema["properties"], self.value
        )

        # Optional: Validate output
        if self.validate_output:
            try:
                validate(instance=generated_data, schema=self.json_schema)
                self.debug("[__call__]", "Output validated successfully against schema.")
            except ValidationError as e:
                self.debug("[__call__]", f"Output validation failed: {e}", is_prompt=True)
                raise ValidationError(f"Generated output failed schema validation: {e}")

        # Format output based on self.output_format
        if self.output_format == "json":
            return generated_data
        elif self.output_format == "xml":
            # Convert generated_data (dict/list) to XML string
            # Need a root element name. Let's use "root" or infer from schema if possible (complex).
            # For now, use "root" if the top level is a dict, or "list" if it's a list.
            if isinstance(generated_data, dict):
                 root_element = self._to_xml(generated_data, "root") # Default root name for dict
            elif isinstance(generated_data, list):
                 root_element = self._to_xml(generated_data, "list") # Default root name for list
            else:
                 # Should not happen with current generate_object/array logic, but handle
                 root_element = self._to_xml({"value": generated_data}, "root") # Wrap primitive in a root
            return ET.tostring(root_element, encoding='unicode')
        elif self.output_format == "yaml":
            # Convert generated_data (dict/list) to YAML string
            return yaml.dump(generated_data, indent=2, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}. Supported formats are 'json', 'xml', 'yaml'.")
from typing import List, Set, Union, Dict, Any
from datetime import datetime, date, time
import uuid
import base64
import xml.etree.ElementTree as ET # Import for XML
import yaml # Import for YAML
from jsonschema import validate, ValidationError # Import for validation
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
        debug: bool = False,
        max_array_length: int = 10,
        max_number_tokens: int = 6,
        temperature: float = 1.0,
        max_string_token_length: int = 175,
        output_format: str = "json", # Add output format parameter
        validate_output: bool = False, # Add validation parameter
    ):
        """
        Initializes the Jsonformer instance.

        Args:
            model: The pre-trained language model.
            tokenizer: The tokenizer for the model.
            json_schema: The JSON schema to follow.
            prompt: The initial prompt for the model.
            debug: Enable debug output.
            max_array_length: Maximum number of items to generate in an array.
            max_number_tokens: Maximum tokens to generate for numbers/integers.
            temperature: Sampling temperature.
            max_string_token_length: Maximum tokens to generate for strings.
            output_format: The desired output format ('json', 'xml', 'yaml').
            validate_output: Whether to validate the output against the schema.

        Note on JSON Schema Support:
        The generation logic directly handles the following schema types/keywords:
        'type' (string, number, integer, boolean, array, object, datetime, date, time, uuid, binary, p_enum, p_integer, null)
        'properties' (for objects)
        'items' (for arrays)
        'maxLength' (for strings)
        'minimum', 'maximum' (for p_integer)
        'values' (for enums and p_enum)
        'round' (for p_enum and p_integer)
        Union types (list of types for 'type')

        Other JSON Schema keywords (e.g., 'required', 'pattern', 'format', 'minLength', 'uniqueItems', 'contains', 'allOf', 'anyOf', 'oneOf', 'not', 'if/then/else')
        are NOT directly used by the generation logic to constrain output during token generation.
        However, if `validate_output` is True, the final generated output will be validated against the *entire* provided `json_schema`
        using the `jsonschema` library, which supports a much wider range of keywords.
        """
        self.model = model
        self.tokenizer = tokenizer
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format.lower() # Store output format
        self.validate_output = validate_output # Store validation flag

        self.type_prefix_tokens = get_prefix_tokens_for_types(tokenizer)

        self.number_logit_processor = OutputNumbersTokens(self.tokenizer, self.prompt)
        self.integer_logit_processor = OutputIntegersTokens(self.tokenizer, self.prompt)

        self.generation_marker = "|GENERATION|"
        self.debug_on = debug
        self.max_array_length = max_array_length

        self.max_number_tokens = max_number_tokens
        self.temperature = temperature
        self.max_string_token_length = max_string_token_length

    def debug(self, caller: str, value: str, is_prompt: bool = False):
        if self.debug_on:
            if is_prompt:
                cprint(caller, "green", end=" ")
                cprint(value, "yellow")
            else:
                cprint(caller, "green", end=" ")
                cprint(value, "blue")

    def generate_datetime(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_datetime]", prompt, is_prompt=True)
        return datetime.now().isoformat()

    def generate_date(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_date]", prompt, is_prompt=True)
        return date.today().isoformat()

    def generate_time(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_time]", prompt, is_prompt=True)
        return datetime.now().time().isoformat()
    
    def generate_uuid(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
        self.debug("[generate_uuid]", prompt, is_prompt=True)
        # Directly generate a valid UUID
        uuid_str = str(uuid.uuid4())
        self.debug("[generate_uuid]", uuid_str)
        return uuid_str
   

    def generate_number(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
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
                temperature=self.temperature * 1.3, iterations=iterations + 1
            )

    def generate_integer(self, temperature: Union[float, None] = None, iterations=0):
        prompt = self.get_prompt()
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

            return self.generate_integer(temperature=self.temperature * 1.3)
        
    def generate_binary(self) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_binary]", prompt, is_prompt=True)
        return base64.b64encode(b"example binary data").decode('utf-8')


    def generate_boolean(self) -> bool:
        prompt = self.get_prompt()
        self.debug("[generate_boolean]", prompt, is_prompt=True)

        input_tensor = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.forward(input_tensor.to(self.model.device))
        logits = output.logits[0, -1]

        true_token_id = self.tokenizer.encode("true", return_tensors="pt")[0, 0]
        false_token_id = self.tokenizer.encode("false", return_tensors="pt")[0, 0]

        result = logits[true_token_id] > logits[false_token_id]

        self.debug("[generate_boolean]", result)

        return result.item()

    def generate_string(self, maxLength=None) -> str:
        prompt = self.get_prompt() + '"'
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
                StringStoppingCriteria(self.tokenizer, len(input_tokens[0]), maxLength)
            ],
            pad_token_id=self.tokenizer.eos_token_id,
        )

        if (
            len(response[0]) >= len(input_tokens[0])
            and (response[0][: len(input_tokens[0])] == input_tokens).all()
        ):
            response = response[0][len(input_tokens[0]) :]
        if response.shape[0] == 1:
            response = response[0]

        response = self.tokenizer.decode(response, skip_special_tokens=True)

        self.debug("[generate_string]", "|" + response + "|")

        if response.count('"') < 1:
            return response

        return response.split('"')[0].strip()

    def generate_p_enum(self, values: list, round: int) -> str:
        prompt = self.get_prompt() + '"'
        self.debug("[generate_p_enum]", prompt, is_prompt=True)
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(
            self.model.device
        )[0]
        values_tokens = self.tokenizer(values).input_ids
        values_tokens = [torch.tensor(c) for c in values_tokens]

        r = list(
            prob_choice_tree(
                self.model, self.tokenizer, input_ids, values_tokens, round=round
            )
        )
        return r

    def generate_p_integer(
        self, range_min: float, range_max: float, round: int
    ) -> float:
        values = [str(n) for n in range(int(range_min), int(range_max) + 1)]
        result = self.generate_p_enum(values, round=round)

        total = 0.0
        for r in result:
            total += float(r["choice"]) * r["prob"]

        if round is not None:
            total = round_to_nsf(total, round)
        return total

    def generate_enum(self, enum_values: Set[str]) -> str:
        prompt = self.get_prompt()
        self.debug("[generate_enum]", prompt, is_prompt=True)

        terminal_tokens = torch.concat(
            [
                self.tokenizer.encode(s, add_special_tokens=False, return_tensors="pt")[
                    :, 0
                ]
                for s in ('", "', '"}', '"]')
            ]
        )

        highest_probability = 0.0
        best_option = None
        for option in enum_values:
            n_option_tokens = self.tokenizer.encode(
                f'"{option}', add_special_tokens=False, return_tensors="pt"
            ).shape[1]
            prompt_tokens = self.tokenizer.encode(
                prompt + f'"{option}', return_tensors="pt"
            )
            option_tokens = prompt_tokens[0, -n_option_tokens:]

            with torch.no_grad():
                logits = self.model.forward(prompt_tokens.to(self.model.device)).logits[
                    0, -n_option_tokens - 1 :
                ]
            probabilities = torch.softmax(logits, dim=1)
            option_token_probabilities = probabilities[:-1][
                torch.arange(probabilities.shape[0] - 1), option_tokens
            ]

            termination_probability = torch.max(probabilities[-1, terminal_tokens])
            option_probability = (
                torch.prod(option_token_probabilities) * termination_probability
            )
            self.debug("[generate_enum]", f"{option_probability}, {option}")

            if option_probability > highest_probability:
                best_option = option
                highest_probability = option_probability

        self.debug("[generate_enum]", best_option)

        return best_option

    def generate_object(
        self, properties: Dict[str, Any], obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        for key, schema in properties.items():
            self.debug("[generate_object] generating value for", key)
            obj[key] = self.generate_value(schema, obj, key)
        return obj

    def generate_array(self, item_schema: Dict[str, Any], obj: Dict[str, Any]) -> list:
        for _ in range(self.max_array_length):
            element = self.generate_value(item_schema, obj)
            obj[-1] = element

            obj.append(self.generation_marker)
            input_prompt = self.get_prompt()
            obj.pop()
            input_tensor = self.tokenizer.encode(input_prompt, return_tensors="pt")
            output = self.model.forward(input_tensor.to(self.model.device))
            logits = output.logits[0, -1]

            top_indices = logits.topk(30).indices
            sorted_token_ids = top_indices[logits[top_indices].argsort(descending=True)]

            found_comma = False
            found_close_bracket = False

            for token_id in sorted_token_ids:
                decoded_token = self.tokenizer.decode(
                    token_id, skip_special_tokens=True
                )
                if "," in decoded_token:
                    found_comma = True
                    break
                if "]" in decoded_token:
                    found_close_bracket = True
                    break

            if found_close_bracket or not found_comma:
                break

        return obj

    def choose_type_to_generate(self, possible_types: List[str]) -> str:
        possible_types = list(set(possible_types))  # remove duplicates
        self.debug("[choose_type_to_generate]", possible_types)
        if len(possible_types) < 1:
            raise ValueError(f"Union type must not be empty")
        elif len(possible_types) == 1:
            return possible_types[0]

        prompt = self.get_prompt()
        input_tensor = self.tokenizer.encode(prompt, return_tensors="pt")
        output = self.model.forward(input_tensor.to(self.model.device))
        logits = output.logits[0, -1]

        max_type = None
        max_logit = -float("inf")
        for possible_type in possible_types:
            try:
                prefix_tokens = self.type_prefix_tokens[possible_type]
            except KeyError:
                raise ValueError(f"Unsupported schema type: {possible_type}")
            max_type_logit = logits[prefix_tokens].max()
            if max_type_logit > max_logit:
                max_type = possible_type
                max_logit = max_type_logit

        if max_type is None:
            raise Exception("Unable to find best type to generate for union type")
        self.debug("[choose_type_to_generate]", max_type)
        return max_type

    def generate_value(
        self,
        schema: Dict[str, Any],
        obj: Union[Dict[str, Any], List[Any]],
        key: Union[str, None] = None,
    ) -> Any:
        schema_type = schema["type"]
        if isinstance(schema_type, list):
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            schema_type = self.choose_type_to_generate(schema_type)
        if schema_type == "number":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_number()
        elif schema_type == "integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_integer()
        elif schema_type == "boolean":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_boolean()
        elif schema_type == "string":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_string(
                schema["maxLength"] if "maxLength" in schema else None
            )
        elif schema_type == "datetime":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_datetime()
        elif schema_type == "date":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_date()
        elif schema_type == "time":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_time()
        elif schema_type == "uuid":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_uuid()
        elif schema_type == "binary":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_binary()
        elif schema_type == "p_enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_p_enum(schema["values"], round=schema.get("round", 3))
        elif schema_type == "p_integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_p_integer(
                schema["minimum"], schema["maximum"], round=schema.get("round", 3)
            )
        elif schema_type == "enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.generate_enum(set(schema["values"]))
        elif schema_type == "array":
            new_array = []
            obj[key] = new_array
            return self.generate_array(schema["items"], new_array)
        elif schema_type == "object":
            new_obj = {}
            if key:
                obj[key] = new_obj
            else:
                obj.append(new_obj)
            return self.generate_object(schema["properties"], new_obj)
        elif schema_type == "null":
            return None
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_prompt(self):
        template = """{prompt}\nOutput result in the following JSON schema format:\n```json{schema}```\nResult: ```json\n{progress}"""
        value = self.value

        progress = json.dumps(value)
        gen_marker_index = progress.find(f'"{self.generation_marker}"')
        if gen_marker_index != -1:
            progress = progress[:gen_marker_index]
        else:
            raise ValueError("Failed to find generation marker")

        prompt = template.format(
            prompt=self.prompt,
            schema=json.dumps(self.json_schema),
            progress=progress,
        )

        return prompt

    def _to_xml(self, data, element_name="item"):
        # Helper function to convert Python dict/list/primitive to XML Element
        if isinstance(data, dict):
            element = ET.Element(element_name)
            for key, value in data.items():
                child = self._to_xml(value, key)
                element.append(child)
            return element
        elif isinstance(data, list):
            # For lists, create a container element and add each item
            element = ET.Element(element_name)
            for item in data:
                 # Use a generic item name for list items
                 item_element = self._to_xml(item, "item") # Using "item" as default list item name
                 element.append(item_element)
            return element
        else:
            # For primitive types
            element = ET.Element(element_name)
            element.text = str(data)
            return element

    def __call__(self) -> Union[Dict[str, Any], str]:
        self.value = {}
        generated_data = self.generate_object(
            self.json_schema["properties"], self.value
        )

        # Optional: Validate output
        if self.validate_output:
            try:
                validate(instance=generated_data, schema=self.json_schema)
                self.debug("[__call__]", "Output validated successfully against schema.")
            except ValidationError as e:
                self.debug("[__call__]", f"Output validation failed: {e}", is_prompt=True)
                raise ValidationError(f"Generated output failed schema validation: {e}")

        # Format output based on self.output_format
        if self.output_format == "json":
            return generated_data
        elif self.output_format == "xml":
            # Convert generated_data (dict/list) to XML string
            # Need a root element name. Let's use "root" or infer from schema if possible (complex).
            # For now, use "root" if the top level is a dict, or "list" if it's a list.
            if isinstance(generated_data, dict):
                 root_element = self._to_xml(generated_data, "root") # Default root name for dict
            elif isinstance(generated_data, list):
                 root_element = self._to_xml(generated_data, "list") # Default root name for list
            else:
                 # Should not happen with current generate_object/array logic, but handle
                 root_element = self._to_xml({"value": generated_data}, "root") # Wrap primitive in a root
            return ET.tostring(root_element, encoding='unicode')
        elif self.output_format == "yaml":
            # Convert generated_data (dict/list) to YAML string
            return yaml.dump(generated_data, indent=2, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}. Supported formats are 'json', 'xml', 'yaml'.")
