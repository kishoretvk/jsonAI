"""
Comprehensive Example: Using jsonAI with OpenAI backend and multiple schemas (Stripe and others)

Usage:
    Set your OpenAI API key and (optionally) API URL via environment variables or CLI args:
        export OPENAI_API_KEY=sk-...
        export OPENAI_API_BASE=https://api.openai.com/v1
    python openai_example.py --api-key ... --api-url ... --model gpt-3.5-turbo

Requires: jsonAI, openai

This script demonstrates:
- Generating data for multiple schemas (Stripe: tax_rates, usage_records, etc.)
- Passing custom prompts for each schema
- Printing all results for review
"""

import os
import argparse
import json
from pathlib import Path
from jsonAI.model_backends import OpenAIBackend
from jsonAI.main import Jsonformer

SCHEMA_DIR = Path(__file__).parent / "stripe_schemas"
SCHEMA_FILES = [
    "tax_rates.schema.json",
    "usage_records.schema.json",
    "stripe_schema.dev.json",
    "stripe_schema.qa.json",
    "stripe_schema.cte.json",
    "stripe_schema.perf.json",
    "stripe_schema.prod.json",
]

EXAMPLES = [
    {
        "schema_file": "tax_rates.schema.json",
        "prompt": "Generate a Stripe tax rate object"
    },
    {
        "schema_file": "usage_records.schema.json",
        "prompt": "Generate a Stripe usage record object"
    },
    {
        "schema_file": "stripe_schema.dev.json",
        "prompt": "Generate a Stripe schema example for DEV"
    },
    {
        "schema_file": "stripe_schema.qa.json",
        "prompt": "Generate a Stripe schema example for QA"
    },
    {
        "schema_file": "stripe_schema.cte.json",
        "prompt": "Generate a Stripe schema example for CTE"
    },
    {
        "schema_file": "stripe_schema.perf.json",
        "prompt": "Generate a Stripe schema example for Performance"
    },
    {
        "schema_file": "stripe_schema.prod.json",
        "prompt": "Generate a Stripe schema example for Production"
    },
]

def main():
    parser = argparse.ArgumentParser(description="jsonAI OpenAI Comprehensive Example")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--api-url", default=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"), help="OpenAI API base URL")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model name")
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("OpenAI API key must be provided via --api-key or OPENAI_API_KEY env var.")

    backend = OpenAIBackend(
        api_key=args.api_key,
        api_base=args.api_url,
        model=args.model,
    )

    for example in EXAMPLES:
        schema_path = SCHEMA_DIR / example["schema_file"]
        if not schema_path.exists():
            print(f"Schema file not found: {schema_path}")
            continue
        with open(schema_path, "r") as f:
            schema = json.load(f)
        jf = Jsonformer(
            model_backend=backend,
            json_schema=schema,
            prompt=example["prompt"],
            output_format="json",
            validate_output=True,
            debug=False,
        )
        print(f"\n=== {example['prompt']} ({example['schema_file']}) ===")
        try:
            result = jf.generate_data()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error generating data for {example['schema_file']}: {e}")

if __name__ == "__main__":
    main()
