from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi.responses import PlainTextResponse

# Assuming jsonAI is installed or accessible in the Python path
from jsonAI.main import Jsonformer

# Load a small model and tokenizer for the example
# In a real application, you might load a larger model
model_name = "gpt2"  # Using gpt2 as a small example model
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


app = FastAPI()


class GenerateRequest(BaseModel):
    prompt: str
    json_schema: Optional[Dict[str, Any]] = None
    output_format: Optional[str] = "json"  # Output type (json, xml, yaml)
    validate_output: Optional[bool] = False  # Validate output


@app.post("/generate/")
async def generate_structured_data(request: GenerateRequest):
    """
    Generates structured data (JSON, XML, or YAML) based on a prompt and schema.
    """
    # Define a default schema if none is provided
    if request.json_schema is None:
        request.json_schema = {
            "type": "object",
            "properties": {
                "greeting": {"type": "string"},
                "value": {"type": "integer"}
            }
        }
        print("Using default schema:", request.json_schema)  # Log default schema usage

    try:
        jsonformer_instance = Jsonformer(
            model=model,
            tokenizer=tokenizer,
            json_schema=request.json_schema,
            prompt=request.prompt,
            output_format=request.output_format,
            validate_output=request.validate_output
        )
        generated_data = jsonformer_instance()

        # FastAPI automatically handles JSON response for dict/list
        # For XML/YAML, return plain text response
        if request.output_format == "json":
            return generated_data
        else:
            return PlainTextResponse(
                content=generated_data,
                media_type=(
                    "application/xml"
                    if request.output_format == "xml"
                    else "application/yaml"
                ),
            )

    except Exception as e:
        # Basic error handling
        print(f"An error occurred: {e}")  # Log the error
        return {"error": str(e)}


# Instructions on how to run the example
"""
To run this example:

1. Make sure you have jsonAI and necessary dependencies installed:
   pip install jsonformer
   fastapi
   uvicorn
   transformers
   torch
   jsonschema
   PyYAML

2. Save this code as fastapi_example.py

3. Run the server from your terminal in the same directory:
   uvicorn fastapi_example:app --reload

4. Open your browser or a tool like curl/Postman and send a POST request to http://127.0.0.1:8000/generate/
   with a JSON body like:
   ```json
   {
       "prompt": "Generate a simple object",
       "json_schema": {
           "type": "object",
           "properties": {
               "name": {"type": "string"},
               "age": {"type": "integer"}
           }
       },
       "output_format": "json",  // or "xml", "yaml"
       "validate_output": true   // or false
   }
   ```

   Example using default schema:
   ```json
   {
       "prompt": "Generate a simple object"
   }
   ```

   Example requesting XML output:
   ```json
   {
       "prompt": "Generate a simple object with a name and age",
       "json_schema": {
           "type": "object",
           "properties": {
               "name": {"type": "string"},
               "age": {"type": "integer"}
           }
       },
       "output_format": "xml"
   }
   ```

   Example requesting YAML output:
   ```json
   {
       "prompt": "Generate a simple object with a name and age",
       "json_schema": {
           "type": "object",
           "properties": {
               "name": {"type": "string"},
               "age": {"type": "integer"}
           }
       },
       "output_format": "yaml"
   }
   ```

   Example with validation enabled:
   ```json
   {
       "prompt": "Generate a simple object with a name and age",
       "json_schema": {
           "type": "object",
           "properties": {
               "name": {"type": "string"},
               "age": {"type": "integer"}
           },
           "required": ["name", "age"]
       },
       "validate_output": true
   }
   ```
"""
