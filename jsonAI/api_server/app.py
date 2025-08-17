from __future__ import annotations
import os
import io
import json
import hashlib
from typing import Any, Dict, AsyncIterator, Optional

from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

# Observability: Prometheus metrics and OpenTelemetry tracing
import time
import socket
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response as StarletteResponse

# OpenTelemetry setup (env-driven)
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHTTPSpanExporter
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from jsonAI.api_server.security import OIDCConfig, OIDCValidator
from jsonAI.api_server.schemas import CsvSchema, XmlSchema
from jsonAI.type_generator import TypeGenerator
from jsonAI.model_backends import ModelBackend
from jsonAI.schema_validator import SchemaValidator


# --------- App init & security ---------

app = FastAPI(title="GenerativeJson Test Data Service", version="0.1.0")

# ----- Observability configuration (env-driven) -----
OBS_ENABLE_METRICS = os.getenv("OBS_ENABLE_METRICS", "true").lower() == "true"
OBS_ENABLE_TRACING = os.getenv("OBS_ENABLE_TRACING", "true").lower() == "true"

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

if OBS_ENABLE_TRACING:
    # OTEL environment variables expected:
    # OTEL_EXPORTER_OTLP_ENDPOINT (e.g., http://otel-collector:4318)
    # OTEL_SERVICE_NAME (default: generativejson-api)
    # Optional: OTEL_EXPORTER_OTLP_HEADERS (key1=val1,key2=val2)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    service_name = os.getenv("OTEL_SERVICE_NAME", "generativejson-api")
    headers_str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    otlp_headers: dict[str, str] | None = None
    if headers_str:
        # Convert "k=v,k2=v2" -> dict
        parts = [p for p in headers_str.split(",") if p]
        otlp_headers = {}
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                otlp_headers[k.strip()] = v.strip()

    resource = Resource.create({
        SERVICE_NAME: service_name,
        "host.name": socket.gethostname(),
        "service.version": "0.1.0",
    })
    tracer_provider = TracerProvider(resource=resource)
    if otlp_endpoint:
        span_exporter: OTLPHTTPSpanExporter = OTLPHTTPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces", headers=otlp_headers)
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI/ASGI
    app.add_middleware(OpenTelemetryMiddleware)  # type: ignore[arg-type]
    FastAPIInstrumentor.instrument_app(app)

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
    json_schema: Dict[str, Any]
    json_options: Optional[Dict[str, Any]] = Field(default=None, description="seed, count etc.")

class CsvGenRequest(BaseModel):
    only_field: CsvSchema
    csv_options: Optional[Dict[str, Any]] = Field(default=None, description="rows, delimiter, header, seed etc.")

class XmlGenerateRequest(BaseModel):
    xml_schema: XmlSchema
    xml_generation_options: Optional[Dict[str, Any]] = None

class ValidateJsonRequest(BaseModel):
    schema: Dict[str, Any]
    data: Any

class ValidateCsvRequest(BaseModel):
    csv_schema: CsvSchema
    sample: str | None = None
    path: str | None = None

class ValidateXmlRequest(BaseModel):
    xml_schema: XmlSchema
    sample: str | None = None
    path: str | None = None


# --------- Utilities ---------

def _deterministic_random(seed: int) -> int:
    # very light helper for deterministic variations
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _get_backend() -> ModelBackend:
    # Use DummyBackend for default/test purposes. Replace with env-driven backend selection as needed.
    from jsonAI.model_backends import DummyBackend
    backend: ModelBackend = DummyBackend()
    return backend


# --------- Routes ---------

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

if OBS_ENABLE_METRICS:
    @app.get("/metrics")
    async def metrics() -> StarletteResponse:
        # Expose Prometheus metrics text format
        return StarletteResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/generate/json")
async def generate_json(req: JsonGenerateRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/generate/json").observe(duration)
    input_schema = req.json_schema
    json_options: Dict[str, Any] = req.json_options or {}
    json_seed_value: int = int(json_options.get("seed", 42))
    count = int(json_options.get("count", 1))

    # Deterministic path: use Jsonformer directly for objects/arrays, or TypeGenerator for primitives
    from jsonAI.main import Jsonformer
    backend = _get_backend()

    results: list[Any] = []
    for i in range(count):
        # For determinism, mix seed with i
        _ = _deterministic_random(json_seed_value + i)
        jf = Jsonformer(backend, input_schema, prompt="Generate structured data for tests", debug=False)
        data = jf.generate_data()
        results.append(data)

    if OBS_ENABLE_METRICS:
        # record status after work completes
        REQUEST_COUNT.labels(method="POST", path="/generate/json", status="200").inc()

    if count == 1:
        return JSONResponse(content={"data": results[0]})
    return JSONResponse(content={"data": results})

@app.post("/generate/csv")
async def generate_csv(req: CsvGenRequest, request: Request, _: Dict[str, Any] = Depends(require_auth)) -> Response:
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/generate/csv").observe(duration)
    input_schema: Any = req.only_field
    csv_options: Dict[str, Any] = req.csv_options or {}
    num_rows: int = int(csv_options.get("rows", getattr(input_schema, "rows", 1)))
    csv_delimiter: str = csv_options.get("delimiter", getattr(input_schema, "delimiter", ","))
    csv_header: bool = bool(csv_options.get("header", getattr(input_schema, "header", True)))
    csv_seed: int = int(csv_options.get("seed", 42))

    # Simple deterministic CSV emitter using TypeGenerator primitives
    backend = _get_backend()
    tg = TypeGenerator(model_backend=backend, debug=lambda *_args, **_kw: None)

    def row_iter() -> AsyncIterator[bytes]:
        # async generator wrapper around a sync generator for FastAPI
        async def _aiter():
            if csv_header:
                header_line = csv_delimiter.join([c.name for c in input_schema.columns]) + "\n"
                yield header_line.encode("utf-8")
            for i in range(num_rows):
                # deterministic per-row seed application (not calling global RNG)
                _ = _deterministic_random(csv_seed + i)
                values: list[str] = []
                for col in input_schema.columns:
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
                yield (csv_delimiter.join(values) + "\n").encode("utf-8")
        return _aiter()

    if OBS_ENABLE_METRICS:
        REQUEST_COUNT.labels(method="POST", path="/generate/csv", status="200").inc()
    return StreamingResponse(row_iter(), media_type="text/csv")

@app.post("/generate/xml")
async def generate_xml(req: XmlGenerateRequest, _: Dict[str, Any] = Depends(require_auth)) -> PlainTextResponse:
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/generate/xml").observe(duration)
    input_schema = req.xml_schema
    xml_generation_options = req.xml_generation_options or {}
    xml_seed_value: int = int(xml_generation_options.get("seed", 42))
    _ = _deterministic_random(xml_seed_value)

    # Minimal deterministic XML emission (v1): emit root and first occurrence of children
    buf = io.StringIO()
    buf.write(f"<{input_schema.root}>")
    # naive one-level traversal
    for el in input_schema.elements:
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
    buf.write(f"</{input_schema.root}>")
    if OBS_ENABLE_METRICS:
        REQUEST_COUNT.labels(method="POST", path="/generate/xml", status="200").inc()
    return PlainTextResponse(content=buf.getvalue(), media_type="application/xml")

@app.post("/validate/json")
async def validate_json(req: ValidateJsonRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/validate/json").observe(duration)
    validator = SchemaValidator()
    try:
        validator.validate(req.data, req.schema)
        if OBS_ENABLE_METRICS:
            REQUEST_COUNT.labels(method="POST", path="/validate/json", status="200").inc()
        return JSONResponse(content={"valid": True})
    except Exception as e:
        if OBS_ENABLE_METRICS:
            REQUEST_COUNT.labels(method="POST", path="/validate/json", status="400").inc()
        return JSONResponse(content={"valid": False, "errors": [str(e)]}, status_code=400)

@app.post("/validate/csv")
async def validate_csv(req: ValidateCsvRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    import csv
    import io
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/validate/csv").observe(duration)
    # Improved CSV validation using Python's csv module
    if req.sample is None:
        raise HTTPException(status_code=400, detail="sample is required for CSV validation")
    errors: list[str] = []
    delimiter = req.csv_schema.delimiter
    expected_cols = [c.name for c in req.csv_schema.columns]
    try:
        reader = csv.reader(io.StringIO(req.sample), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return JSONResponse(content={"valid": False, "errors": ["empty sample"]}, status_code=400)
        start_idx = 0
        if req.csv_schema.header:
            header = rows[0]
            if header != expected_cols:
                errors.append(f"header mismatch: expected {expected_cols}, got {header}")
            start_idx = 1
        for i, row in enumerate(rows[start_idx:], start=start_idx):
            if len(row) != len(expected_cols):
                errors.append(f"row {i} column count mismatch: expected {len(expected_cols)}, got {len(row)}")
    except Exception as e:
        errors.append(f"CSV parsing error: {e}")
    if errors:
        if OBS_ENABLE_METRICS:
            REQUEST_COUNT.labels(method="POST", path="/validate/csv", status="400").inc()
        return JSONResponse(content={"valid": False, "errors": errors}, status_code=400)
    if OBS_ENABLE_METRICS:
        REQUEST_COUNT.labels(method="POST", path="/validate/csv", status="200").inc()
    return JSONResponse(content={"valid": True})

@app.post("/validate/xml")
async def validate_xml(req: ValidateXmlRequest, _: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    import xml.etree.ElementTree as ET
    start = time.perf_counter()
    try:
        # business logic below
        pass
    finally:
        duration = time.perf_counter() - start
        if OBS_ENABLE_METRICS:
            REQUEST_LATENCY.labels(method="POST", path="/validate/xml").observe(duration)
    # XML validation using xml.etree.ElementTree
    if not req.sample:
        if OBS_ENABLE_METRICS:
            REQUEST_COUNT.labels(method="POST", path="/validate/xml", status="400").inc()
        return JSONResponse(content={"valid": False, "errors": ["missing sample"]}, status_code=400)
    errors = []
    try:
        root = ET.fromstring(req.sample)
        if root.tag != req.xml_schema.root:
            errors.append(f"root element mismatch: expected '{req.xml_schema.root}', got '{root.tag}'")
    except ET.ParseError as e:
        errors.append(f"XML parsing error: {e}")
    if errors:
        if OBS_ENABLE_METRICS:
            REQUEST_COUNT.labels(method="POST", path="/validate/xml", status="400").inc()
        return JSONResponse(content={"valid": False, "errors": errors}, status_code=400)
    if OBS_ENABLE_METRICS:
        REQUEST_COUNT.labels(method="POST", path="/validate/xml", status="200").inc()
    return JSONResponse(content={"valid": True})
