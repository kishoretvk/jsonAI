"""
Test cases for the tracing infrastructure.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from jsonAI.tracing import Tracer, get_tracer, trace_function, SpanHandle
from opentelemetry.trace import SpanKind, StatusCode


class TestTracer(unittest.TestCase):
    """Test cases for Tracer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracer = Tracer(service_name="test-service", debug=True)
        
    def test_init(self):
        """Test initialization of Tracer."""
        self.assertEqual(self.tracer.service_name, "test-service")
        self.assertTrue(self.tracer.debug)
        self.assertIsNotNone(self.tracer.tracer)
        
    def test_start_span_context_manager(self):
        """Test starting a span with context manager."""
        with self.tracer.start_span("test_span") as span:
            self.assertIsNotNone(span)
            self.assertTrue(span.is_recording())
            
        # Span should be ended after the context manager exits
        self.assertFalse(span.is_recording())
        
    def test_start_span_sync(self):
        """Test starting a span synchronously."""
        span_handle = self.tracer.start_span_sync("test_span")
        self.assertIsInstance(span_handle, SpanHandle)
        self.assertIsNotNone(span_handle.span)
        self.assertTrue(span_handle.span.is_recording())
        
        # End the span
        span_handle.end()
        self.assertFalse(span_handle.span.is_recording())
        
    def test_span_attributes(self):
        """Test setting attributes on a span."""
        with self.tracer.start_span("test_span") as span:
            span.set_attribute("test_attribute", "test_value")
            span.set_attribute("test_number", 42)
            span.set_attribute("test_bool", True)
            
    def test_span_events(self):
        """Test adding events to a span."""
        with self.tracer.start_span("test_span") as span:
            span.add_event("test_event")
            span.add_event("test_event_with_attributes", {"key": "value"})
            
    def test_span_status(self):
        """Test setting span status."""
        with self.tracer.start_span("test_span") as span:
            span.set_status(StatusCode.OK)
            
        with self.tracer.start_span("error_span") as span:
            span.set_status(StatusCode.ERROR, "Something went wrong")
            
    def test_span_exception(self):
        """Test recording exceptions in spans."""
        with self.assertRaises(ValueError):
            with self.tracer.start_span("test_span") as span:
                raise ValueError("Test exception")
                
    def test_get_trace_context(self):
        """Test getting trace context."""
        with self.tracer.start_span("test_span") as span:
            context = self.tracer.get_trace_context(span)
            self.assertIn("trace_id", context)
            self.assertIn("span_id", context)
            self.assertIn("trace_flags", context)
            
    def test_inject_extract_context(self):
        """Test injecting and extracting context."""
        headers = {"Content-Type": "application/json"}
        injected_headers = self.tracer.inject_context(headers)
        self.assertEqual(injected_headers, headers)  # No-op implementation
        
        extracted_context = self.tracer.extract_context(headers)
        self.assertEqual(extracted_context, {})  # No-op implementation
        
    def test_get_global_tracer(self):
        """Test getting the global tracer."""
        tracer1 = get_tracer("service1")
        tracer2 = get_tracer("service2")
        # Should return the same instance
        self.assertIs(tracer1, tracer2)
        
    def test_trace_function_decorator(self):
        """Test the trace function decorator."""
        @trace_function("test_function")
        def test_function(param1, param2=None):
            return f"result: {param1}, {param2}"
            
        result = test_function("value1", param2="value2")
        self.assertEqual(result, "result: value1, value2")
        
    def test_trace_function_with_exception(self):
        """Test the trace function decorator with an exception."""
        @trace_function("test_function")
        def test_function():
            raise ValueError("Test error")
            
        with self.assertRaises(ValueError):
            test_function()
            
    def test_trace_async_function(self):
        """Test tracing an async function."""
        @trace_function("async_test_function")
        async def async_test_function():
            await asyncio.sleep(0.01)
            return "async result"
            
        async def run_test():
            result = await async_test_function()
            self.assertEqual(result, "async result")
            
        asyncio.run(run_test())
        
    def test_flush(self):
        """Test flushing traces."""
        # This should not raise an exception
        self.tracer.flush()
        
    def test_span_handle_context_manager(self):
        """Test using SpanHandle as a context manager."""
        span_handle = self.tracer.start_span_sync("test_span")
        with span_handle as span:
            span.set_attribute("test_attr", "test_value")
        # Span should be ended after context manager exits
        self.assertFalse(span_handle.span.is_recording())


if __name__ == "__main__":
    unittest.main()