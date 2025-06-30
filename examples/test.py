import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI import Jsonformer
from jsonschema import ValidationError

# --- Configuration ---
MODEL_NAME = "gpt2"
DEBUG_MODE = True

# --- Helper Functions ---
def load_model_and_tokenizer(model_name: str):
    """
    Load the model and tokenizer.

    Args:
        model_name (str): Name of the model to load.

    Returns:
        tuple: Loaded model and tokenizer.

    Raises:
        RuntimeError: If loading fails.
    """
    print(f"Loading model: {model_name}")
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.add_special_tokens({'pad_token': tokenizer.eos_token})
            model.resize_token_embeddings(len(tokenizer))
        print("Model and tokenizer loaded successfully.")
        return model, tokenizer
    except Exception as e:
        raise RuntimeError(f"Error loading model {model_name}: {e}")


def generate_json(model, tokenizer, json_schema, prompt, debug_mode, output_format="json"):
    """
    Generate JSON using Jsonformer.

    Args:
        model: The language model.
        tokenizer: The tokenizer.
        json_schema (dict): The JSON schema.
        prompt (str): The generation prompt.
        debug_mode (bool): Debug mode flag.
        output_format (str): Output format (default: "json").

    Returns:
        dict: Generated JSON.

    Raises:
        Exception: If generation fails.
    """
    jsonformer = Jsonformer(
        model=model,
        tokenizer=tokenizer,
        json_schema=json_schema,
        prompt=prompt,
        debug=debug_mode,
        output_format=output_format
    )
    return jsonformer()

# --- Main Script ---
try:
    model, tokenizer = load_model_and_tokenizer(MODEL_NAME)
except RuntimeError as e:
    print(e)
    exit()

examples = [
    {
        "description": "Basic JSON Generation",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "isStudent": {"type": "boolean"}
            }
        },
        "prompt": "Generate a person's profile.",
    },
    {
        "description": "YAML Generation",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        },
        "prompt": "Generate a person's profile in YAML.",
        "output_format": "yaml",
    },
    {
        "description": "CSV Generation",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        },
        "prompt": "Generate a list of people in CSV.",
        "output_format": "csv",
    },
    {
        "description": "Advanced Schema with oneOf",
        "schema": {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"}
            ]
        },
        "prompt": "Generate a value that can be either a string or an integer.",
    },
    {
        "description": "Custom Format: Email",
        "schema": {
            "type": "string",
            "format": "email"
        },
        "prompt": "Generate a valid email address.",
    },
    {
        "description": "Streaming JSON Generation",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        },
        "prompt": "Stream a person's profile.",
    }
]

for example in examples:
    print(f"\n--- {example['description']} ---")
    if example['description'] == "Streaming JSON Generation":
        jsonformer = Jsonformer(model, tokenizer, example['schema'], example['prompt'], debug_mode=DEBUG_MODE)
        for chunk in jsonformer.stream_generate_data():
            print("Generated Chunk:", chunk)
    else:
        try:
            output = generate_json(
                model=model,
                tokenizer=tokenizer,
                json_schema=example["schema"],
                prompt=example["prompt"],
                debug_mode=DEBUG_MODE,
                output_format=example.get("output_format", "json")
            )
            print("Generated Output:")
            print(json.dumps(output, indent=2) if isinstance(output, dict) else output)
        except Exception as e:
            print(f"Error in {example['description']}: {e}")

# --- Instructions ---
print("\n--- Instructions ---")
# FIX: E501 - Broke long print statement into multiple lines
print(
    f"To run this test file, make sure you have the '{MODEL_NAME}' model "
    "accessible"
)
print("and the project dependencies installed (`poetry install`).")
print("Then run: poetry run python test.py")
