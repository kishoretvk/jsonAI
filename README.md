# jsonAI 

jsonAI is a Python library for generating JSON objects based on a given schema using a pre-trained language model. It supports a wide range of data types, including numbers, integers, booleans, strings, datetime, date, time, UUID, and binary data.

The idea to create json structures with strong typed schemas is now possible, with any numbe rof variable combinations. 

This currently supports a subset of JSON Schema. Below is a list of the supported schema types:

- number
- integer
- boolean
- string  (descriptions also enabled to satisfy summary)
- datetime
- date
- time
- UUID
- binary data
### combinations
- arrays
- enums
- complex object

## Supported Output Formats

In addition to JSON, `jsonAI` now supports generating output in XML and YAML formats. You can specify the desired format using the `output_format` parameter in the `Jsonformer` constructor.

**XML Output Example:**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
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

prompt = "Generate information about a book."

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    output_format="xml"
)

generated_data = jsonformer()
print(generated_data)
```

**YAML Output Example:**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
    "type": "object",
    "properties": {
        "person": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "isStudent": {"type": "boolean"}
            }
        }
    }
}

prompt = "Generate information about a person."

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    output_format="yaml"
)

generated_data = jsonformer()
print(generated_data)
```

## Output Validation

You can enable schema validation for the generated output by setting the `validate_output` parameter to `True`. This requires the `jsonschema` library to be installed (`pip install jsonschema`).

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name", "age"]
}

prompt = "Generate a person's information."

# This will raise a jsonschema.exceptions.ValidationError if the output doesn't match the schema
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    validate_output=True
)

generated_data = jsonformer()
print(generated_data)
```

## Examples

We have included examples to demonstrate how to integrate `jsonAI` with other libraries and frameworks. You can find them in the `examples/` directory.

### FastAPI Integration Example

This example shows how to use `jsonAI` within a FastAPI web application to create an API endpoint that generates structured data based on user input.

To run the FastAPI example:

1.  Install necessary dependencies:
    ```bash
    pip install fastapi uvicorn transformers torch jsonschema PyYAML
    ```
2.  Navigate to the `examples/` directory.
3.  Run the server:
    ```bash
    uvicorn fastapi_example:app --reload
    ```
4.  Send a POST request to `http://127.0.0.1:8000/generate/` with a JSON body containing `prompt` and optionally `json_schema`, `output_format`, and `validate_output`. See the comments in `examples/fastapi_example.py` for more details.

## Basic Usage


## Examples

``` python 
# Define the JSON schema
json_schema = {
    "type": "object",
    "properties": {
        "transaction_id": {"type": "uuid"},
        "store": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "location": {"type": "string"},
                "datetime": {"type": "datetime"}
            }
        },
        "customer": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "uuid"},
                "name": {"type": "string"},
                "membership": {"type": "boolean"}
            }
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "uuid"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "price": {"type": "number"},
                    "quantity": {"type": "integer"}
                }
            }
        },
        "total_amount": {"type": "number"},
        "payment_method": {"type": "string"},
        "transaction_date": {"type": "date"},
        "transaction_time": {"type": "time"},
        "receipt_binary": {"type": "binary"}
    }
}

# Define the prompt
prompt = "Generate a JSON object representing a transaction at a Starbucks coffee shop. The transaction includes details such as transaction ID, store information, customer information, items purchased, total amount, payment method, transaction date and time, and a binary receipt."

# Initialize Jsonformer
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    debug=True
)

# Generate the data
generated_data = jsonformer()
print(generated_data)
highlight_values(generated_data)

```

## generated Output 

``` json
{
  transaction_id: "035a6195-5536-4272-966b-ba700c6de39c",
  store: {
    name: "Starbucks",
    location: "San Francisco",
    datetime: "2024-09-21T19:47:28.164729"
  },
  customer: {
    customer_id: "b8a61099-4baf-4352-af86-922f476f2bfc",
    name: "John Doe",
    membership: True
  },
  items: [
    {
      item_id: "f60a82b6-b7e8-4a85-a202-fc6aa28e1de8",
      name: "Coffee",
      category: "Drip Brew",
      price: 10.0,
      quantity: 10000000
    }
  ],
  total_amount: 2024092119.0,
  payment_method: "card",
  transaction_date: "2024-09-21",
  transaction_time: "19:47:30.686584",
  receipt_binary: "ZXhhbXBsZSBiaW5hcnkgZGF0YQ=="
}

```

## Example 

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
json_schema = {
    "type": "object",
    "properties": {
        "number": {"type": "number"},
        "integer": {"type": "integer"},
        "boolean": {"type": "boolean"},
        "string": {"type": "string"},
        "datetime": {"type": "datetime"},
        "date": {"type": "date"},
        "time": {"type": "time"},
        "uuid": {"type": "uuid"},
        "binary": {"type": "binary"},
    }
}
prompt = "Generate a JSON object"

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    debug=True
)

generated_data = jsonformer()
print(generated_data)


```

## Development

### this is for colab 


```bash
# autoreload your package
%load_ext autoreload
%autoreload 2

```
```bash
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Loading model and tokenizer...")
model_name = "databricks/dolly-v2-3b"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    use_cache=True,
    torch_dtype=torch.float16,
    attn_implementation="eager",
).to("cuda:0")
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, use_cache=True)
print("Loaded model and tokenizer")

```

```bash
!git clone https://github.com/kishoretvk/jsonAI.git
%cd jsonAI
```

```bash
!pip install jaxtyping termcolor typeguard
```

```bash
from jsonAI.format import highlight_values
from jsonAI.main import Jsonformer

```

### after the above stpes on colab try any example given 




# below refers to older code 


### prob_jsonformer: Probabilistic Structured JSON from Language Models.

This fork has been modified to include the token probabilities. This is not complaint with json schema, but it can be useful for efficient extracting of a range of possible values.

I've also merged some of the recent PR's for enum, integer, null, union. They are not yet included in the upstream Jsonformer. You can see them all below in this example:


~~~
# installing
pip install git+https://github.com/wassname/prob_jsonformer.git
~~~


## Metrics

How well does it work? Well when I asked is `Q: Please sample a number from the distribution [0, 20]: `, assumming it should be a uniform distribution, this is how well it did:

Lower is better as it indicates a faithful sampling of the distribution. Time is in seconds.

| method                   | KL_div_loss |     time |
| :----------------------- | ----------: | -------: |
| method0: sampling        |    -3.09214 |  48.5044 |
| method1: hindsight       |    -3.09214 | 0.683987 |
| method3: generation tree |   **-3.09216**| **0.075112**|

KL_div_loss is the -1 * KL divergence between the true distribution and the generated distribution. 


## Example

```python
from prob_jsonformer import Jsonformer
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "databricks/dolly-v2-3b"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

json_schema = {
    "type": "object",
    "properties": {
        # we can return the probability of each choice, even if they are multiple tokens
        "age_probs": {"type": "p_enum", "values": [str(s) for s in range(10, 20)]},
        # we can return the probabilistic weighted mean of a range
        "age_wmean": {"type": "p_integer", "minimum": 10, "maximum": 20},
        # the prob of true and false
        "is_student_probs": {"type": "p_enum", "values": ["true", "false"]},
        "is_student": {"type": "boolean"},
        # we've merged patches for enum, integer, null, union - currently mising from jsonformer
        "name": {"type": "string", "maxLength": 4},
        "age": {"type": "integer"},
        "unit_time": {"type": "number"},
        "courses": {"type": "array", "items": {"type": "string"}},
        "trim": {"type": ["string", "null"]},
        "color": {
            "type": "enum",
            "values": ["red", "green", "blue", "brown", "white", "black"],
        },
    },
}

prompt = "Generate a young person's information based on the following schema:"
jsonformer = Jsonformer(model, tokenizer, json_schema, prompt, temperature=0)
generated_data = jsonformer()

generated_data = {
    "age_probs": [
        {"prob": 0.62353515625, "choice": "10"},
        {"prob": 0.349609375, "choice": "12"},
        {"prob": 0.01123809814453125, "choice": "11"},
        {"prob": 0.00760650634765625, "choice": "16"},
        {"prob": 0.0025482177734375, "choice": "13"},
        {"prob": 0.0025081634521484375, "choice": "15"},
        {"prob": 0.0018062591552734375, "choice": "14"},
        {"prob": 0.00104522705078125, "choice": "18"},
        {"prob": 0.00011551380157470703, "choice": "17"},
        {"prob": 5.042552947998047e-05, "choice": "19"},
    ],
    "age_wmean": 15.544570922851562,
    "is_student_probs": [
        {"prob": 0.962890625, "choice": "true"},
        {"prob": 0.037322998046875, "choice": "false"},
    ],
    "is_student": False,
    "name": "John",
    "age": 17,
    "unit_time": 0.5,
    "courses": ["C++"],
    "trim": None,
    "color": "green",
}
```

 The original [README](https://github.com/1rgs/jsonformer) is included below.

# ORIGINAL: Jsonformer: A Bulletproof Way to Generate Structured JSON from Language Models.

### Problem: Getting models to output structured JSON is hard

### Solution: Only generate the content tokens and fill in the fixed tokens

[![colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/1rgs/jsonformer/blob/main/Jsonformer_example.ipynb)

![cover](img/cover4.png)

Generating structured JSON from language models is a challenging task. The
generated JSON must be syntactically correct, and it must conform to a schema
that specifies the structure of the JSON.

Current approaches to this problem are brittle and error-prone. They rely on prompt engineering, fine-tuning, and post-processing, but they still fail to generate syntactically correct JSON in many cases.

Jsonformer is a new approach to this problem. In structured data, many tokens are fixed and predictable. Jsonformer is a wrapper around Hugging Face models that fills in the fixed tokens during the generation process, and only delegates the generation of content tokens to the language model. This makes it more efficient and bulletproof than existing approaches.

This currently supports a subset of JSON Schema. Below is a list of the supported schema types:

- number
- boolean
- string
- array
- object

## Example

```python
from jsonformer import Jsonformer
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("databricks/dolly-v2-12b")
tokenizer = AutoTokenizer.from_pretrained("databricks/dolly-v2-12b")

json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"},
        "is_student": {"type": "boolean"},
        "courses": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

prompt = "Generate a person's information based on the following schema:"
jsonformer = Jsonformer(model, tokenizer, json_schema, prompt)
generated_data = jsonformer()

print(generated_data)
```

### Jsonformer works on complex schemas, even with tiny models. Here is an example of a schema with nested objects and arrays, generated by a 3B parameter model.

```python
{"type": "object", "properties": {"car": {"type": "object", "properties": {"make": {"type": "string"}, "model": {"type": "string"}, "year": {"type": "number"}, "colors": {"type": "array", "items": {"type": "string"}}, "features": {"type": "object", "properties": {"audio": {"type": "object", "properties": {"brand": {"type": "string"}, "speakers": {"type": "number"}, "hasBluetooth": {"type": "boolean"}}}, "safety": {"type": "object", "properties": {"airbags": {"type": "number"}, "parkingSensors": {"type": "boolean"}, "laneAssist": {"type": "boolean"}}}, "performance": {"type": "object", "properties": {"engine": {"type": "string"}, "horsepower": {"type": "number"}, "topSpeed": {"type": "number"}}}}}}}, "owner": {"type": "object", "properties": {"firstName": {"type": "string"}, "lastName": {"type": "string"}, "age": {"type": "number"}}}}}
```

```python
{
  car: {
    make: "audi",
    model: "model A8",
    year: 2016.0,
    colors: [
      "blue"
    ],
    features: {
      audio: {
        brand: "sony",
        speakers: 2.0,
        hasBluetooth: True
      },
      safety: {
        airbags: 2.0,
        parkingSensors: True,
        laneAssist: True
      },
      performance: {
        engine: "4.0",
        horsepower: 220.0,
        topSpeed: 220.0
      }
    }
  },
  owner: {
    firstName: "John",
    lastName: "Doe",
    age: 40.0
  }
}
```

## Features

- Bulletproof JSON generation: Jsonformer ensures that the generated JSON is always syntactically correct and conforms to the specified schema.
- Efficiency: By generating only the content tokens and filling in the fixed tokens, Jsonformer is more efficient than generating a full JSON string and parsing it.
- Flexible and extendable: Jsonformer is built on top of the Hugging Face transformers library, making it compatible with any model that supports the Hugging Face interface.

## Installation

```bash
pip install jsonformer
```

## Development

[Poetry](https://python-poetry.org/docs/#installation) is used for dependency management.

```bash
poetry install
```

```bash
poetry run python -m jsonformer.example
```

## License

Jsonformer is released under the MIT License. You are free to use, modify, and distribute this software for any purpose, commercial or non-commercial, as long as the original copyright and license notice are included.
