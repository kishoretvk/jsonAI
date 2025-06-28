import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI import Jsonformer
from jsonschema import ValidationError

# --- Configuration ---
# Using a small local transformers model for demonstration
# Replace with your desired local model if needed (e.g., "gpt2")
MODEL_NAME = "gpt2"
DEBUG_MODE = True  # Set to True to see debug output

# --- Load Model and Tokenizer ---
print(f"Loading model: {MODEL_NAME}")
try:
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    # Add a pad token if the tokenizer doesn't have one
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': tokenizer.eos_token})
        model.resize_token_embeddings(len(tokenizer))
    print("Model and tokenizer loaded successfully.")
except Exception as e:
    print(f"Error loading model {MODEL_NAME}: {e}")
    print("Please ensure you have the model downloaded or accessible.")
    exit()

# --- Example 1: Basic JSON Generation ---
print("\n--- Example 1: Basic JSON Generation ---")
json_schema_1 = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "isStudent": {"type": "boolean"}
    }
}
prompt_1 = "Generate a person's profile."

try:
    jsonformer_1 = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema_1,
        prompt=prompt_1,
        debug=DEBUG_MODE,
        output_format="json"
    )
    output_json_1 = jsonformer_1()
    print("Generated JSON:")
    print(json.dumps(output_json_1, indent=2))
except Exception as e:
    print(f"Error in Example 1: {e}")

# --- Example 2: JSON Generation with Array ---
print("\n--- Example 2: JSON Generation with Array ---")
json_schema_2 = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}
prompt_2 = "Generate a list of fruits."

try:
    jsonformer_2 = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema_2,
        prompt=prompt_2,
        debug=DEBUG_MODE,
        output_format="json"
    )
    output_json_2 = jsonformer_2()
    print("Generated JSON with Array:")
    print(json.dumps(output_json_2, indent=2))
except Exception as e:
    print(f"Error in Example 2: {e}")

# --- Example 3: XML Generation ---
print("\n--- Example 3: XML Generation ---")
json_schema_3 = {
    "type": "object",
    "properties": {
        "book": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "year": {"type": "integer"}
            }
        }
    }
}
prompt_3 = "Generate details for a book."

try:
    jsonformer_3 = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema_3,
        prompt=prompt_3,
        debug=DEBUG_MODE,
        output_format="xml"
    )
    output_xml_3 = jsonformer_3()
    print("Generated XML:")
    print(output_xml_3)
except Exception as e:
    print(f"Error in Example 3: {e}")

# --- Example 4: YAML Generation ---
print("\n--- Example 4: YAML Generation ---")
json_schema_4 = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "id": {"type": "integer"},
                "active": {"type": "boolean"}
            }
        }
    }
}
prompt_4 = "Generate user information."

try:
    jsonformer_4 = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema_4,
        prompt=prompt_4,
        debug=DEBUG_MODE,
        output_format="yaml"
    )
    output_yaml_4 = jsonformer_4()
    print("Generated YAML:")
    print(output_yaml_4)
except Exception as e:
    print(f"Error in Example 4: {e}")

# --- Example 5: JSON Generation with Validation ---
print("\n--- Example 5: JSON Generation with Validation ---")
json_schema_5 = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "status": {"type": "string", "enum": ["pass", "fail", "incomplete"]}
    },
    "required": ["score", "status"]
}
prompt_5 = "Generate a test result."

try:
    jsonformer_5 = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema_5,
        prompt=prompt_5,
        debug=DEBUG_MODE,
        output_format="json",
        validate_output=True  # Enable validation
    )
    output_json_5 = jsonformer_5()
    print("Generated JSON (with validation enabled):")
    print(json.dumps(output_json_5, indent=2))
except ValidationError as e:
    print(f"Validation Error in Example 5: {e}")
except Exception as e:
    print(f"Error in Example 5: {e}")

# --- Instructions ---
print("\n--- Instructions ---")
# FIX: E501 - Broke long print statement into multiple lines
print(
    f"To run this test file, make sure you have the '{MODEL_NAME}' model "
    "accessible"
)
print("and the project dependencies installed (`poetry install`).")
print("Then run: poetry run python test.py")