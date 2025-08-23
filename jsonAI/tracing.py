"""
Tracing infrastructure for JsonAI using OpenTelemetry.

This module provides distributed tracing capabilities for monitoring
and debugging JsonAI workflows and operations.
"""

from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager
import logging
import time
import uuid
from datetime import datetime
from dataclasses import dataclass, field

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)


@dataclass
class TraceContext:
    """Context for tracking trace information."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "running"
    events: list = field(default_factory=list)


class Tracer:
    """Tracing infrastructure for JsonAI."""
    
    def __init__(self, service_name: str = "jsonai", debug: bool = False):
        self.service_name = service_name
        self.debug = debug
        self.tracer = None
        self._initialize_tracer()
        self.active_spans = {}
        
    def _initialize_tracer(self):
        """Initialize the OpenTelemetry tracer."""
        try:
            # Create a resource to represent the service
            resource = Resource(attributes={
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: "0.15.2",
            })
            
            # Create a tracer provider
            provider = TracerProvider(resource=resource)
            
            # Add a console exporter for development/debugging
            if self.debug:
                processor = BatchSpanProcessor(ConsoleSpanExporter())
                provider.add_span_processor(processor)
            
            # Add OTLP exporter for production (if endpoint is configured)
            try:
                otlp_exporter = OTLPSpanExporter()
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(otlp_processor)
            except Exception as e:
                if self.debug:
                    logger.debug(f"OTLP exporter not configured: {e}")
            
            # Set the tracer provider
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)
            
            if self.debug:
                logger.debug("OpenTelemetry tracer initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracer: {e}")
            # Fallback to a no-op tracer
            self.tracer = trace.get_tracer(__name__)
            
    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None, 
                   span_kind: SpanKind = SpanKind.INTERNAL):
        """Context manager for starting and ending a span."""
        if attributes is None:
            attributes = {}
            
        span = self.tracer.start_span(name, attributes=attributes, kind=span_kind)
        try:
            # Add the span to active spans
            span_id = str(span.get_span_context().span_id)
            self.active_spans[span_id] = span
            
            yield span
        except Exception as e:
            # Record the exception in the span
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            # End the span
            if span.is_recording():
                span.end()
            # Remove from active spans
            if span_id in self.active_spans:
                del self.active_spans[span_id]
                
    def start_span_sync(self, name: str, attributes: Optional[Dict[str, Any]] = None,
                       span_kind: SpanKind = SpanKind.INTERNAL) -> 'SpanHandle':
        """Start a span synchronously and return a handle to manage it."""
        if attributes is None:
            attributes = {}
            
        span = self.tracer.start_span(name, attributes=attributes, kind=span_kind)
        span_id = str(span.get_span_context().span_id)
        self.active_spans[span_id] = span
        
        return SpanHandle(span, self)
        
    async def start_span_async(self, name: str, attributes: Optional[Dict[str, Any]] = None,
                              span_kind: SpanKind = SpanKind.INTERNAL):
        """Start a span asynchronously and return a handle to manage it."""
        # For async, we'll use the same implementation as sync for now
        return self.start_span_sync(name, attributes, span_kind)
        
    def add_event(self, span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to a span."""
        if attributes is None:
            attributes = {}
        span.add_event(name, attributes)
        
    def set_status(self, span, status_code: StatusCode, description: Optional[str] = None):
        """Set the status of a span."""
        span.set_status(Status(status_code, description))
        
    def set_attribute(self, span, key: str, value: Any):
        """Set an attribute on a span."""
        span.set_attribute(key, value)
        
    def get_trace_context(self, span) -> Dict[str, Any]:
        """Get the trace context for a span."""
        context = span.get_span_context()
        return {
            "trace_id": hex(context.trace_id)[2:],  # Remove '0x' prefix
            "span_id": hex(context.span_id)[2:],    # Remove '0x' prefix
            "trace_flags": context.trace_flags
        }
        
    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for distributed tracing."""
        # This would typically use opentelemetry.propagate to inject context
        # For now, we'll return the headers unchanged
        return headers
        
    def extract_context(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract trace context from headers."""
        # This would typically use opentelemetry.propagate to extract context
        # For now, we'll return an empty context
        return {}
        
    def flush(self):
        """Flush any pending spans."""
        try:
            trace.get_tracer_provider().force_flush()
        except Exception as e:
            logger.error(f"Failed to flush traces: {e}")


class SpanHandle:
    """Handle for managing a span."""
    
    def __init__(self, span, tracer: Tracer):
        self.span = span
        self.tracer = tracer
        self.span_id = str(span.get_span_context().span_id)
        
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span."""
        self.tracer.add_event(self.span, name, attributes)
        
    def set_status(self, status_code: StatusCode, description: Optional[str] = None):
        """Set the status of the span."""
        self.tracer.set_status(self.span, status_code, description)
        
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the span."""
        self.tracer.set_attribute(self.span, key, value)
        
    def end(self):
        """End the span."""
        if self.span.is_recording():
            self.span.end()
        # Remove from active spans
        if self.span_id in self.tracer.active_spans:
            del self.tracer.active_spans[self.span_id]
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            # Record the exception in the span
            self.span.record_exception(exc_val)
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        self.end()


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "jsonai", debug: bool = False) -> Tracer:
    """Get or create a global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name, debug)
    return _global_tracer


def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing function execution."""
    def decorator(func):
        nonlocal name
        if name is None:
            name = f"{func.__module__}.{func.__name__}"
            
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_span(name, attributes) as span:
                try:
                    # Add function arguments as attributes (be careful with sensitive data)
                    if tracer.debug:
                        span.set_attribute("function.args.count", len(args))
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                    
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_span(name, attributes) as span:
                try:
                    # Add function arguments as attributes (be careful with sensitive data)
                    if tracer.debug:
                        span.set_attribute("function.args.count", len(args))
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                    
        # Check if the function is async
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return wrapper
            
    return decorator