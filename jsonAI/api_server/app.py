from __future__ import annotations
import os
import io
import json
import hashlib
from typing import Any, Dict, AsyncIterator

from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from jsonAI.api_server.security import OIDCConfig, OIDCValidator
from jsonAI.api_server.schemas import CsvSchema, XmlSchema
from jsonAI.type_generator import TypeGenerator
from jsonAI.model_backends import ModelBackend
from jsonAI.schema_validator import SchemaValidator


# --------- App init & security ---------

app = FastAPI(title="GenerativeJson Test Data Service", version="0.1.0")

_oidc_config: OIDCConfig | None = None
_oidc_validator: OIDCValidator | None = None

def get_validator() -> OIDCValidator:
    global _oidc_config, _oidc_validator
    if _oidc_validator is None:
        _oidc_config = OIDCConfig()
        _oidc_validator = OIDCValidator(_oidc_config)
    return _oidc_validator

async def require_auth(request: Request, validator: OIDCValidator = Depends(get_validator)) -> Dict[str, Any]:
    return await validator.validate_request(request)


# --------- Request models ---------

class JsonGenerateRequest(BaseModel):
    schema: Dict[str, Any]
    options: Dict[str, Any] | None = Field(default=None, description="seed, count etc.")

class CsvGenerateRequest(BaseModel):
    csvSchema: CsvSchema
    options: Dict[str, Any] | None = None

class XmlGenerateRequest(BaseModel):
    xmlSchema: XmlSchema
    options: Dict[str, Any] | None = None

class ValidateJsonRequest(BaseModel):
    schema: Dict[str, Any]
    data: Any

class ValidateCsvRequest(BaseModel):
    csvSchema: CsvSchema
    sample: str | None = None
    path: str | None = None

class ValidateXmlRequest(BaseModel):
    xmlSchema: XmlSchema
    sample: str | None = None
    path: str | None = None


# --------- Utilities ---------

def _deterministic_random(seed: int) -> int:
    # very light helper for deterministic variations
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _get_backend() -> ModelBackend:
    # In this phase we rely on existing ModelBackend implementations;
    # for deterministic Sprint 1, we will mainly use TypeGenerator deterministic branches.
    # Assuming there exists a simple ModelBackend in the repo for basic calls.
    from jsonAI.model_backends import ModelBackend  # type: ignore
    # For now, we require a provided backend by env, or a dummy one can be implemented later.
    # Placeholder: raise if not configured.
    # In practice, you may wire a default DeterministicBackend.
    backend: ModelBackend = ModelBackend()  # type: ignore
    return backend


# --------- Routes ---------

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/generate/json")
async def generate_json(req: JsonGenerateRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    schema = req.schema
    options = req.options or {}
    seed = int(options.get("seed", 42))
    count = int(options.get("count", 1))

    # Deterministic path: use Jsonformer directly for objects/arrays, or TypeGenerator for primitives
    from jsonAI.main import Jsonformer
    backend = _get_backend()

    results: list[Any] = []
    for i in range(count):
        # For determinism, mix seed with i
        _ = _deterministic_random(seed + i)
        jf = Jsonformer(backend, schema, prompt="Generate structured data for tests", debug=False)
        data = jf.generate_data()
        results.append(data)

    if count == 1:
        return JSONResponse(content={"data": results[0]})
    return JSONResponse(content={"data": results})

@app.post("/generate/csv")
async def generate_csv(req: CsvGenerateRequest, request: Request, _: Dict[str, Any] = Depends(require_auth)) -> Response:
    schema = req.csvSchema
    options = req.options or {}
    rows = int(options.get("rows", schema.rows))
    delimiter = options.get("delimiter", schema.delimiter)
    header = bool(options.get("header", schema.header))
    seed = int(options.get("seed", 42))

    # Simple deterministic CSV emitter using TypeGenerator primitives
    backend = _get_backend()
    tg = TypeGenerator(model_backend=backend, debug=lambda *_args, **_kw: None)

    def row_iter() -> AsyncIterator[bytes]:  # type: ignore[override]
        # async generator wrapper around a sync generator for FastAPI
        async def _aiter():
            if header:
                header_line = delimiter.join([c.name for c in schema.columns]) + "\n"
                yield header_line.encode("utf-8")
            for i in range(rows):
                # deterministic per-row seed application (not calling global RNG)
                _ = _deterministic_random(seed + i)
                values: list[str] = []
                for col in schema.columns:
                    t = col.type
                    if t == "string":
                        values.append("example")
                    elif t == "integer":
                        values.append(str(1))
                    elif t == "number":
                        values.append(str(1.0))
                    elif t == "boolean":
                        values.append("true")
                    elif t == "date":
                        values.append("2024-01-01")
                    elif t == "datetime":
                        values.append("2024-01-01T00:00:00Z")
                    elif t == "uuid":
                        values.append("00000000-0000-4000-8000-000000000000")
                    elif t == "enum" and col.enumValues:
                        values.append(col.enumValues[0])
                    else:
                        values.append("example")
                yield (delimiter.join(values) + "\n").encode("utf-8")
        return _aiter()

    return StreamingResponse(row_iter(), media_type="text/csv")

@app.post("/generate/xml")
async def generate_xml(req: XmlGenerateRequest, _: Dict[str, Any] = Depends(require_auth)) -> PlainTextResponse:
    schema = req.xmlSchema
    options = req.options or {}
    seed = int(options.get("seed", 42))
    _ = _deterministic_random(seed)

    # Minimal deterministic XML emission (v1): emit root and first occurrence of children
    buf = io.StringIO()
    buf.write(f"<{schema.root}>")
    # naive one-level traversal
    for el in schema.elements:
        buf.write(f"<{el.name}>")
        if el.type == "string":
            buf.write("example")
        elif el.type == "integer":
            buf.write("1")
        elif el.type == "number":
            buf.write("1.0")
        elif el.type == "boolean":
            buf.write("true")
        elif el.type == "date":
            buf.write("2024-01-01")
        elif el.type == "datetime":
            buf.write("2024-01-01T00:00:00Z")
        elif el.type == "uuid":
            buf.write("00000000-0000-4000-8000-000000000000")
        elif el.type == "enum" and el.enumValues:
            buf.write(str(el.enumValues[0]))
        else:
            buf.write("example")
        buf.write(f"</{el.name}>")
    buf.write(f"</{schema.root}>")
    return PlainTextResponse(content=buf.getvalue(), media_type="application/xml")

@app.post("/validate/json")
async def validate_json(req: ValidateJsonRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    validator = SchemaValidator()
    try:
        validator.validate(req.data, req.schema)
        return JSONResponse(content={"valid": True})
    except Exception as e:
        return JSONResponse(content={"valid": False, "errors": [str(e)]}, status_code=400)

@app.post("/validate/csv")
async def validate_csv(req: ValidateCsvRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    # Minimal CSV validation: header match and column count per row
    if req.sample is None:
        raise HTTPException(status_code=400, detail="sample is required for CSV validation in v1")
    lines = [ln for ln in req.sample.splitlines() if ln.strip() != ""]
    if not lines:
        return JSONResponse(content={"valid": False, "errors": ["empty sample"]}, status_code=400)

    delimiter = req.csvSchema.delimiter
    expected_cols = [c.name for c in req.csvSchema.columns]
    errors: list[str] = []

    start_idx = 0
    if req.csvSchema.header:
        header = lines[0].split(delimiter)
        if header != expected_cols:
            errors.append(f"header mismatch: expected {expected_cols}, got {header}")
        start_idx = 1

    for i in range(start_idx, len(lines)):
        parts = lines[i].split(delimiter)
        if len(parts) != len(expected_cols):
            errors.append(f"row {i} column count mismatch: expected {len(expected_cols)}, got {len(parts)}")

    if errors:
        return JSONResponse(content={"valid": False, "errors": errors}, status_code=400)
    return JSONResponse(content={"valid": True})

@app.post("/validate/xml")
async def validate_xml(req: ValidateXmlRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    # Minimal XML validation placeholder (v1). Proper XSD validation arrives in v2.
    if not req.sample:
        return JSONResponse(content={"valid": False, "errors": ["missing sample"]}, status_code=400)
    if f"</{req.xmlSchema.root}>" not in req.sample:
        return JSONResponse(content={"valid": False, "errors": ["root element mismatch"]}, status_code=400)
    return JSONResponse(content={"valid": True})
