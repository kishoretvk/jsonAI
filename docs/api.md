# JsonAI API Reference

Complete API documentation for the JsonAI REST API service.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production deployments, implement API key authentication as described in the deployment guide.

## Content Type

All API endpoints accept and return `application/json` unless otherwise specified.

## Rate Limiting

Default rate limiting is 10 requests per minute per IP address. This can be configured in production deployments.

## API Endpoints

### Health Check

#### GET `/health`

Check the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.14.0",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

---

### JSON Generation

#### POST `/generate`

Generate structured JSON based on a prompt and schema.

**Request Body:**
```json
{
  "prompt": "Generate a user profile for a software developer",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "integer", "minimum": 18},
      "skills": {
        "type": "array",
        "items": {"type": "string"}
      },
      "experience": {
        "type": "object",
        "properties": {
          "years": {"type": "integer"},
          "level": {"type": "string", "enum": ["junior", "mid", "senior"]}
        }
      }
    },
    "required": ["name", "age", "skills"]
  },
  "model_name": "ollama",
  "model_path": null,
  "max_tokens": 1000,
  "temperature": 0.1,
  "debug": false
}
```

**Parameters:**
- `prompt` (string, required): The prompt for JSON generation
- `schema` (object, required): JSON schema to follow
- `model_name` (string, optional): Model backend to use (default: "ollama")
- `model_path` (string, optional): Path to model file
- `max_tokens` (integer, optional): Maximum tokens to generate
- `temperature` (float, optional): Generation temperature (default: 0.1)
- `debug` (boolean, optional): Enable debug mode (default: false)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "name": "Alex Johnson",
    "age": 28,
    "skills": ["Python", "JavaScript", "React", "Node.js"],
    "experience": {
      "years": 5,
      "level": "mid"
    }
  },
  "status": "success",
  "duration": 2.45,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Generation successful
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Generation failed

---

### Async JSON Generation

#### POST `/generate/async`

Generate JSON asynchronously for better performance with concurrent requests.

**Request Body:** Same as `/generate`

**Response:** Same as `/generate`

**Status Codes:** Same as `/generate`

---

### Batch JSON Generation

#### POST `/generate/batch`

Generate JSON for multiple requests in a single batch operation.

**Request Body:**
```json
{
  "requests": [
    {
      "prompt": "Generate a user profile",
      "schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "age": {"type": "integer"}
        }
      }
    },
    {
      "prompt": "Generate a product description",
      "schema": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "price": {"type": "number"}
        }
      }
    }
  ],
  "max_concurrent": 5
}
```

**Parameters:**
- `requests` (array, required): List of generation requests
- `max_concurrent` (integer, optional): Maximum concurrent requests (default: 5)

**Response:**
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "result": {
        "name": "John Doe",
        "age": 30
      },
      "status": "success",
      "duration": 1.23,
      "timestamp": "2024-01-01T12:00:00.000Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "result": {
        "title": "Premium Laptop",
        "price": 1299.99
      },
      "status": "success",
      "duration": 1.45,
      "timestamp": "2024-01-01T12:00:01.000Z"
    }
  ],
  "total_count": 2,
  "success_count": 2,
  "error_count": 0,
  "total_duration": 2.68
}
```

**Status Codes:**
- `200 OK` - Batch processing completed
- `400 Bad Request` - Invalid batch request
- `500 Internal Server Error` - Batch processing failed

---

### Schema Validation

#### POST `/validate`

Validate a JSON schema for correctness.

**Request Body:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer", "minimum": 0}
  },
  "required": ["name"]
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Error Response:**
```json
{
  "valid": false,
  "errors": [
    "Invalid property type at path 'age'",
    "Missing required property 'name'"
  ],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Validation completed
- `400 Bad Request` - Invalid schema format
- `500 Internal Server Error` - Validation failed

---

### Statistics

#### GET `/stats`

Get API performance and cache statistics.

**Response:**
```json
{
  "performance_stats": {
    "generate_550e8400-e29b-41d4-a716-446655440000": {
      "count": 1,
      "avg_duration": 2.45,
      "min_duration": 2.45,
      "max_duration": 2.45,
      "total_duration": 2.45
    }
  },
  "cache_stats": {
    "ollama:null": {
      "schema_cache": {
        "size": 10,
        "maxsize": 500,
        "hits": 25,
        "misses": 35
      },
      "prompt_cache": {
        "size": 15,
        "maxsize": 500,
        "ttl": 3600,
        "hits": 40,
        "misses": 20
      }
    }
  },
  "uptime": "Service uptime tracking not implemented"
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `500 Internal Server Error` - Failed to retrieve statistics

---

### Cache Management

#### DELETE `/cache`

Clear all API caches (model cache, jsonformer cache, etc.).

**Response:**
```json
{
  "status": "success",
  "message": "All caches cleared"
}
```

**Status Codes:**
- `200 OK` - Caches cleared successfully
- `500 Internal Server Error` - Failed to clear caches

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Common Error Codes

- `400 Bad Request` - Invalid request parameters or schema
- `401 Unauthorized` - Missing or invalid authentication (if enabled)
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server-side error
- `503 Service Unavailable` - Service temporarily unavailable

---

## Schema Types

The API supports all JSON Schema types:

### Primitive Types

```json
{
  "type": "string"
}

{
  "type": "integer",
  "minimum": 0,
  "maximum": 100
}

{
  "type": "number",
  "minimum": 0.0
}

{
  "type": "boolean"
}

{
  "type": "null"
}
```

### Arrays

```json
{
  "type": "array",
  "items": {"type": "string"},
  "minItems": 1,
  "maxItems": 10
}
```

### Objects

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer"}
  },
  "required": ["name"],
  "additionalProperties": false
}
```

### Enums

```json
{
  "type": "string",
  "enum": ["small", "medium", "large"]
}
```

### Complex Nested Schemas

```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "profile": {
          "type": "object",
          "properties": {
            "preferences": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "category": {"type": "string"},
                  "enabled": {"type": "boolean"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## Client Examples

### Python

```python
import requests

# Basic generation
response = requests.post('http://localhost:8000/generate', json={
    'prompt': 'Generate a user profile',
    'schema': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        }
    }
})

result = response.json()
print(result['result'])
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function generateJSON() {
  try {
    const response = await axios.post('http://localhost:8000/generate', {
      prompt: 'Generate a user profile',
      schema: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          age: { type: 'integer' }
        }
      }
    });
    
    console.log(response.data.result);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

generateJSON();
```

### cURL

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a user profile",
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
      }
    }
  }'
```

---

## Performance Considerations

### Request Optimization

1. **Use Batch Requests:** For multiple generations, use `/generate/batch`
2. **Cache Strategy:** Similar schemas and prompts are cached automatically
3. **Async Endpoints:** Use `/generate/async` for better concurrency
4. **Temperature Settings:** Lower temperature (0.1-0.3) for more consistent results

### Response Time Factors

1. **Schema Complexity:** More complex schemas take longer to generate
2. **Model Size:** Larger models produce better results but are slower
3. **Prompt Length:** Longer prompts may increase generation time
4. **Cache Hits:** Cached results return immediately

### Best Practices

1. **Schema Design:** Keep schemas as simple as possible while meeting requirements
2. **Prompt Engineering:** Clear, specific prompts produce better results
3. **Error Handling:** Always handle potential errors and timeouts
4. **Rate Limiting:** Respect API rate limits in client implementations

---

## WebSocket Support (Future)

WebSocket support for real-time streaming generation is planned for future releases:

```javascript
// Future WebSocket API
const ws = new WebSocket('ws://localhost:8000/generate/stream');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'token') {
    console.log('New token:', data.token);
  } else if (data.type === 'complete') {
    console.log('Generation complete:', data.result);
  }
};

ws.send(JSON.stringify({
  prompt: 'Generate a user profile',
  schema: { /* schema here */ }
}));
```

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- Interactive Documentation: `/docs`
- ReDoc Documentation: `/redoc`
- Raw OpenAPI JSON: `/openapi.json`

This allows automatic client generation for any programming language using tools like:
- Swagger Codegen
- OpenAPI Generator
- Postman Collection Import
