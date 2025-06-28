from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi.responses import PlainTextResponse

# Assuming jsonAI is installed or accessible in the Python path
from jsonAI.main import Jsonformer

# Load a small model and tokenizer for the example
# In a real application, you might load a larger model
model_name = "gpt2"
# Using gpt2 as a small example model
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


app = FastAPI()


class GenerateRequest(BaseModel):
    prompt: str
    json_schema: Optional[Dict[str, Any]] = None
    output_format: Optional[str] = "json"
    # Output type can be json, xml, or yaml
    validate_output: Optional[bool] = False  # Validate output


@app.post("/generate/")
async def generate_structured_data(request: GenerateRequest):
    """
    Generates structured data based on a prompt and schema.
    Supported formats: JSON, XML, YAML.
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
        # Log default schema usage
        print("Using default schema:", request.json_schema)

    try:
        jsonformer_instance = Jsonformer(
            model=model,
            tokenizer=tokenizer,
            json_schema=request.json_schema,
            prompt=request.prompt,
            output_format=request.output_format,
            validate_output=request.validate_output,
        )
        generated_data = jsonformer_instance()

        # FastAPI handles JSON (dict/list) automatically.
        if request.output_format == "json":
            return generated_data
        else:
            # For XML/YAML, return PlainTextResponse with the correct media type.
            if request.output_format == "xml":
                media_type = "application/xml"
            else:
                media_type = "application/yaml"
            # FIX: E501 - Broke long function call into multiple lines
            return PlainTextResponse(
                content=generated_data, media_type=media_type
            )

    except Exception as e:
        # Basic error handling
        # Log the error
        print(f"An error occurred: {e}")
        # Return a JSON error response for consistency.
        return {"error": str(e)}
