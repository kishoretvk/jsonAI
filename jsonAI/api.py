"""
FastAPI REST API for JsonAI.

This module provides a REST API interface for JSON generation using FastAPI,
with support for synchronous and asynchronous operations, batch processing,
and comprehensive error handling.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
import asyncio
import uuid
from datetime import datetime
import logging

from .main import Jsonformer
from .async_jsonformer import FullAsyncJsonformer as AsyncJsonformer
from .performance import OptimizedJsonformer, PerformanceMonitor
# from .model_backends import get_model_and_tokenizer  # removed: symbol not present; adapted below

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI(
    title="JsonAI API",
    description="REST API for structured JSON generation using LLMs",
    version="0.15.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global performance monitor
performance_monitor = PerformanceMonitor()

# Request/Response Models
class GenerationRequest(BaseModel):
    """Request model for JSON generation."""
    prompt: str = Field(..., description="The prompt for JSON generation")
    schema: Dict[str, Any] = Field(..., description="JSON schema to follow")
    model_name: str = Field(default="ollama", description="Model backend to use")
    model_path: Optional[str] = Field(default=None, description="Path to model")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.1, description="Generation temperature")
    debug: bool = Field(default=False, description="Enable debug mode")

class BatchGenerationRequest(BaseModel):
    """Request model for batch JSON generation."""
    requests: List[GenerationRequest] = Field(..., description="List of generation requests")
    max_concurrent: int = Field(default=5, description="Maximum concurrent requests")

class GenerationResponse(BaseModel):
    """Response model for JSON generation."""
    id: str = Field(..., description="Unique identifier for the request")
    result: Dict[str, Any] = Field(..., description="Generated JSON result")
    status: str = Field(..., description="Request status")
    duration: Optional[float] = Field(None, description="Generation duration in seconds")
    timestamp: str = Field(..., description="Response timestamp")

class BatchGenerationResponse(BaseModel):
    """Response model for batch JSON generation."""
    results: List[GenerationResponse] = Field(..., description="List of generation results")
    total_count: int = Field(..., description="Total number of requests")
    success_count: int = Field(..., description="Number of successful requests")
    error_count: int = Field(..., description="Number of failed requests")
    total_duration: float = Field(..., description="Total processing duration")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Health check timestamp")

class StatsResponse(BaseModel):
    """Statistics response model."""
    performance_stats: Dict[str, Any] = Field(..., description="Performance statistics")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")
    uptime: str = Field(..., description="Service uptime")

# Global variables for model management
_model_cache = {}
_jsonformer_cache = {}

async def get_jsonformer(request: GenerationRequest) -> Union[Jsonformer, OptimizedJsonformer]:
    """Get or create a Jsonformer instance for the request."""
    cache_key = f"{request.model_name}:{request.model_path}"
    
    if cache_key not in _jsonformer_cache:
        try:
            # Get model and tokenizer
            if cache_key not in _model_cache:
                # Resolve model/tokenizer based on provider
                if request.model_name.lower() == "ollama":
                    from .model_backends import OllamaBackend, DummyTokenizer
                    model = OllamaBackend(model_name=request.model_path or "llama3")
                    tokenizer = DummyTokenizer()
                elif request.model_name.lower() == "transformers":
                    # Placeholder: user must provide actual model/tokenizer elsewhere
                    raise ValueError("Transformers backend requires a provided model/tokenizer")
                elif request.model_name.lower() == "openai":
                    from .model_backends import OpenAIBackend, DummyTokenizer
                    model = OpenAIBackend(api_key=request.model_path or "")
                    tokenizer = DummyTokenizer()
                else:
                    # Fallback dummy backend for tests
                    from .model_backends import DummyBackend
                    backend = DummyBackend()
                    model = backend
                    tokenizer = backend.tokenizer
                _model_cache[cache_key] = (model, tokenizer)
            else:
                model, tokenizer = _model_cache[cache_key]
            
            # Create optimized jsonformer (expects model_backend + schema + prompt)
            # Wrap provided (model, tokenizer) in a backend-like object if needed
            from .model_backends import ModelBackend, DummyBackend
            if isinstance(model, ModelBackend):
                backend = model
            else:
                # If 'model' is not a ModelBackend, fall back to DummyBackend for compatibility
                backend = DummyBackend()
            # OptimizedJsonformer inherits Jsonformer signature (model_backend, json_schema, prompt, ...)
            jsonformer = OptimizedJsonformer(
                model=backend,
                tokenizer=tokenizer,
                schema=request.schema,
                cache_size=1000,
                cache_ttl=3600
            )
            
            _jsonformer_cache[cache_key] = jsonformer
            
        except Exception as e:
            logger.error("Failed to create Jsonformer: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize model: {str(e)}"
            )
    
    return _jsonformer_cache[cache_key]

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic service information."""
    return HealthResponse(
        status="running",
        version="0.15.0",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.15.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/generate", response_model=GenerationResponse)
async def generate_json(request: GenerationRequest):
    """Generate JSON based on prompt and schema."""
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Get jsonformer instance
        jsonformer = await get_jsonformer(request)
        
        # Start performance monitoring
        performance_monitor.start_operation(f"generate_{request_id}")
        
        # Generate JSON
        result = jsonformer.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            debug=request.debug
        )
        
        # End performance monitoring
        duration = performance_monitor.end_operation(f"generate_{request_id}")
        
        return GenerationResponse(
            id=request_id,
            result=result,
            status="success",
            duration=duration,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error("Generation failed for request %s: %s", request_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )

@app.post("/generate/async", response_model=GenerationResponse)
async def generate_json_async(request: GenerationRequest):
    """Generate JSON asynchronously."""
    request_id = str(uuid.uuid4())
    
    try:
        # Get model and tokenizer
        cache_key = f"{request.model_name}:{request.model_path}"
        
        if cache_key not in _model_cache:
            if request.model_name.lower() == "ollama":
                from .model_backends import OllamaBackend, DummyTokenizer
                model = OllamaBackend(model_name=request.model_path or "llama3")
                tokenizer = DummyTokenizer()
            elif request.model_name.lower() == "openai":
                from .model_backends import OpenAIBackend, DummyTokenizer
                model = OpenAIBackend(api_key=request.model_path or "")
                tokenizer = DummyTokenizer()
            else:
                from .model_backends import DummyBackend
                backend = DummyBackend()
                model = backend
                tokenizer = backend.tokenizer
            _model_cache[cache_key] = (model, tokenizer)
        else:
            model, tokenizer = _model_cache[cache_key]
        
        # Create async jsonformer
        # Our AsyncJsonformer in async_jsonformer.py is FullAsyncJsonformer aliased as AsyncJsonformer
        async_jsonformer = AsyncJsonformer(
            model_backend=model,
            json_schema=request.schema,
            prompt=request.prompt
        )
        
        # Start performance monitoring
        async with performance_monitor.async_timer(f"async_generate_{request_id}"):
            result = await async_jsonformer.generate_async(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                debug=request.debug
            )
        
        return GenerationResponse(
            id=request_id,
            result=result,
            status="success",
            duration=None,  # Will be filled by monitoring
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error("Async generation failed for request %s: %s", request_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Async generation failed: {str(e)}"
        )

@app.post("/generate/batch", response_model=BatchGenerationResponse)
async def generate_json_batch(batch_request: BatchGenerationRequest):
    """Generate JSON for multiple requests in batch."""
    start_time = datetime.now()
    total_requests = len(batch_request.requests)
    
    try:
        # Process all requests
        results = []
        success_count = 0
        error_count = 0
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(batch_request.max_concurrent)
        
        async def process_single_request(req: GenerationRequest) -> GenerationResponse:
            nonlocal success_count, error_count
            
            async with semaphore:
                request_id = str(uuid.uuid4())
                
                try:
                    jsonformer = await get_jsonformer(req)
                    
                    # Start performance monitoring
                    performance_monitor.start_operation(f"batch_generate_{request_id}")
                    
                    # Generate in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: jsonformer.generate(
                            prompt=req.prompt,
                            max_tokens=req.max_tokens,
                            temperature=req.temperature,
                            debug=req.debug
                        )
                    )
                    
                    duration = performance_monitor.end_operation(f"batch_generate_{request_id}")
                    success_count += 1
                    
                    return GenerationResponse(
                        id=request_id,
                        result=result,
                        status="success",
                        duration=duration,
                        timestamp=datetime.now().isoformat()
                    )
                    
                except Exception as e:
                    error_count += 1
                    logger.error("Batch request %s failed: %s", request_id, str(e))
                    
                    return GenerationResponse(
                        id=request_id,
                        result={"error": str(e)},
                        status="error",
                        duration=None,
                        timestamp=datetime.now().isoformat()
                    )
        
        # Process all requests concurrently
        tasks = [process_single_request(req) for req in batch_request.requests]
        results = await asyncio.gather(*tasks)
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        return BatchGenerationResponse(
            results=results,
            total_count=total_requests,
            success_count=success_count,
            error_count=error_count,
            total_duration=total_duration
        )
        
    except Exception as e:
        logger.error("Batch processing failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get API performance and cache statistics."""
    try:
        # Get performance stats
        perf_stats = performance_monitor.get_all_stats()
        
        # Get cache stats from cached jsonformers
        cache_stats = {}
        for key, jsonformer in _jsonformer_cache.items():
            if hasattr(jsonformer, 'get_cache_stats'):
                cache_stats[key] = jsonformer.get_cache_stats()
        
        return StatsResponse(
            performance_stats=perf_stats,
            cache_stats=cache_stats if cache_stats else None,
            uptime="Service uptime tracking not implemented"
        )
        
    except Exception as e:
        logger.error("Failed to get statistics: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.delete("/cache")
async def clear_cache():
    """Clear all caches."""
    try:
        # Clear model cache
        _model_cache.clear()
        
        # Clear jsonformer cache and their internal caches
        for jsonformer in _jsonformer_cache.values():
            if hasattr(jsonformer, 'clear_cache'):
                jsonformer.clear_cache()
        
        _jsonformer_cache.clear()
        
        return {"status": "success", "message": "All caches cleared"}
        
    except Exception as e:
        logger.error("Failed to clear cache: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

@app.post("/validate")
async def validate_schema(schema: Dict[str, Any]):
    """Validate a JSON schema."""
    try:
        # Adapt to SchemaValidator class in schema_validator.py
        from .schema_validator import SchemaValidator
        validator = SchemaValidator()
        is_valid = validator.validate(schema, {"type": "object"}, raise_on_error=False)
        errors = None if is_valid else "Schema did not validate against a basic object type"
        
        return {
            "valid": is_valid,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Schema validation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Schema validation failed: {str(e)}"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup."""
    logger.info("JsonAI API starting up...")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("JsonAI API shutting down...")
    
    # Clear all caches
    _model_cache.clear()
    _jsonformer_cache.clear()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
