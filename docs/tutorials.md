# JsonAI Tutorials

Comprehensive tutorials for using JsonAI in various scenarios and applications.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic JSON Generation](#basic-json-generation)
3. [Advanced Schema Design](#advanced-schema-design)
4. [CLI Usage](#cli-usage)
5. [API Integration](#api-integration)
6. [Performance Optimization](#performance-optimization)
7. [Production Deployment](#production-deployment)
8. [Real-World Examples](#real-world-examples)

---

## Getting Started

### Installation

#### Option 1: Using pip

```bash
pip install jsonai
```

#### Option 2: From source

```bash
git clone https://github.com/yourusername/JsonAI.git
cd JsonAI
poetry install
```

#### Option 3: Using Docker

```bash
docker run -p 8000:8000 jsonai:latest
```

### Quick Start

```python
from jsonAI import Jsonformer
from jsonAI.model_backends import get_model_and_tokenizer

# Get model and tokenizer
model, tokenizer = get_model_and_tokenizer("ollama", "llama2")

# Define schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"}
    }
}

# Create Jsonformer instance
jsonformer = Jsonformer(model, tokenizer, schema)

# Generate JSON
result = jsonformer.generate("Generate a person's profile")
print(result)
```

---

## Basic JSON Generation

### Tutorial 1: Simple Object Generation

Let's start with generating a simple user profile:

```python
from jsonAI import Jsonformer
from jsonAI.model_backends import get_model_and_tokenizer

# Initialize model
model, tokenizer = get_model_and_tokenizer("ollama", "llama2")

# Define a simple schema
user_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 18, "maximum": 100},
        "email": {"type": "string"},
        "is_active": {"type": "boolean"}
    },
    "required": ["name", "age"]
}

# Create Jsonformer
jsonformer = Jsonformer(model, tokenizer, user_schema)

# Generate user profile
prompt = "Generate a profile for a software engineer"
result = jsonformer.generate(prompt)

print("Generated User Profile:")
print(result)
# Output: {"name": "Alex Smith", "age": 28, "email": "alex.smith@email.com", "is_active": true}
```

### Tutorial 2: Array Generation

Generate arrays of data:

```python
# Schema for array of skills
skills_schema = {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 3,
    "maxItems": 8
}

jsonformer = Jsonformer(model, tokenizer, skills_schema)
result = jsonformer.generate("List programming skills for a full-stack developer")

print("Generated Skills:")
print(result)
# Output: ["Python", "JavaScript", "React", "Node.js", "PostgreSQL"]
```

### Tutorial 3: Enum Values

Generate data with constrained choices:

```python
# Schema with enum values
product_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "category": {
            "type": "string",
            "enum": ["electronics", "clothing", "books", "home", "sports"]
        },
        "price": {"type": "number", "minimum": 0},
        "availability": {
            "type": "string", 
            "enum": ["in_stock", "out_of_stock", "limited"]
        }
    },
    "required": ["name", "category", "price"]
}

jsonformer = Jsonformer(model, tokenizer, product_schema)
result = jsonformer.generate("Generate a product for an online store")

print("Generated Product:")
print(result)
# Output: {"name": "Wireless Headphones", "category": "electronics", "price": 79.99, "availability": "in_stock"}
```

---

## Advanced Schema Design

### Tutorial 4: Nested Objects

Create complex nested structures:

```python
# Complex nested schema
company_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "headquarters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "country": {"type": "string"},
                        "postal_code": {"type": "string"}
                    }
                },
                "coordinates": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"}
                    }
                }
            }
        },
        "employees": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "position": {"type": "string"},
                    "department": {"type": "string"},
                    "salary": {"type": "number"}
                }
            },
            "minItems": 2,
            "maxItems": 5
        }
    }
}

jsonformer = Jsonformer(model, tokenizer, company_schema)
result = jsonformer.generate("Generate information for a tech startup")

print("Generated Company:")
import json
print(json.dumps(result, indent=2))
```

### Tutorial 5: Conditional Schemas

Using anyOf, oneOf, and allOf:

```python
# Schema with conditional logic
event_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["online", "in_person"]},
        "title": {"type": "string"},
        "date": {"type": "string"}
    },
    "allOf": [
        {
            "if": {"properties": {"type": {"const": "online"}}},
            "then": {
                "properties": {
                    "platform": {"type": "string"},
                    "meeting_link": {"type": "string"}
                },
                "required": ["platform", "meeting_link"]
            }
        },
        {
            "if": {"properties": {"type": {"const": "in_person"}}},
            "then": {
                "properties": {
                    "venue": {"type": "string"},
                    "address": {"type": "string"},
                    "capacity": {"type": "integer"}
                },
                "required": ["venue", "address"]
            }
        }
    ]
}

jsonformer = Jsonformer(model, tokenizer, event_schema)

# Generate online event
online_result = jsonformer.generate("Generate an online webinar event")
print("Online Event:", online_result)

# Generate in-person event  
inperson_result = jsonformer.generate("Generate an in-person conference event")
print("In-Person Event:", inperson_result)
```

---

## CLI Usage

### Tutorial 6: Command Line Interface

JsonAI provides a powerful CLI for various operations:

#### Basic Generation

```bash
# Generate JSON from prompt and schema file
jsonai generate \
  --prompt "Generate a user profile" \
  --schema schema.json \
  --output result.json

# Generate with inline schema
jsonai generate \
  --prompt "Create a product listing" \
  --schema '{"type": "object", "properties": {"name": {"type": "string"}}}' \
  --model ollama \
  --temperature 0.2
```

#### Batch Processing

```bash
# Process multiple requests from file
jsonai batch \
  --input batch_requests.json \
  --output batch_results.json \
  --concurrent 5

# Example batch_requests.json:
{
  "requests": [
    {
      "prompt": "Generate user 1",
      "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
    },
    {
      "prompt": "Generate user 2", 
      "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
    }
  ]
}
```

#### Schema Validation

```bash
# Validate a schema file
jsonai validate --schema schema.json

# Validate generated JSON against schema
jsonai validate \
  --schema schema.json \
  --data generated.json
```

#### Multiple Output Formats

```bash
# Generate YAML output
jsonai generate \
  --prompt "Generate config data" \
  --schema config_schema.json \
  --format yaml \
  --output config.yaml

# Generate CSV output (for array schemas)
jsonai generate \
  --prompt "Generate list of employees" \
  --schema employee_list_schema.json \
  --format csv \
  --output employees.csv

# Generate XML output
jsonai generate \
  --prompt "Generate API response" \
  --schema api_schema.json \
  --format xml \
  --output response.xml
```

---

## API Integration

### Tutorial 7: REST API Usage

#### Starting the API Server

```bash
# Start the API server
jsonai serve --port 8000 --workers 4

# Or using uvicorn directly
uvicorn jsonAI.api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Python Client

```python
import requests
import json

class JsonAIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def generate(self, prompt, schema, **kwargs):
        """Generate JSON using the API."""
        response = requests.post(
            f"{self.base_url}/generate",
            json={
                "prompt": prompt,
                "schema": schema,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()
    
    def generate_batch(self, requests, max_concurrent=5):
        """Generate multiple JSONs in batch."""
        response = requests.post(
            f"{self.base_url}/generate/batch",
            json={
                "requests": requests,
                "max_concurrent": max_concurrent
            }
        )
        response.raise_for_status()
        return response.json()
    
    def validate_schema(self, schema):
        """Validate a JSON schema."""
        response = requests.post(
            f"{self.base_url}/validate",
            json=schema
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = JsonAIClient()

schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}}
    }
}

result = client.generate(
    prompt="Generate a blog post metadata",
    schema=schema,
    temperature=0.3
)

print("Generated result:", result["result"])
```

#### JavaScript Client

```javascript
class JsonAIClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async generate(prompt, schema, options = {}) {
        const response = await fetch(`${this.baseUrl}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt,
                schema,
                ...options
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async generateBatch(requests, maxConcurrent = 5) {
        const response = await fetch(`${this.baseUrl}/generate/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                requests,
                max_concurrent: maxConcurrent
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new JsonAIClient();

const schema = {
    type: 'object',
    properties: {
        name: { type: 'string' },
        price: { type: 'number' },
        inStock: { type: 'boolean' }
    }
};

client.generate('Generate a product', schema)
    .then(result => console.log(result.result))
    .catch(error => console.error('Error:', error));
```

---

## Performance Optimization

### Tutorial 8: Caching and Performance

#### Using CachedJsonformer

```python
from jsonAI.performance import CachedJsonformer
from jsonAI.model_backends import get_model_and_tokenizer

# Initialize with caching
model, tokenizer = get_model_and_tokenizer("ollama", "llama2")

# Create cached instance
cached_jsonformer = CachedJsonformer(
    model=model,
    tokenizer=tokenizer,
    schema=schema,
    cache_size=1000,
    cache_ttl=3600  # 1 hour TTL
)

# First generation (slow - not cached)
result1 = cached_jsonformer.generate("Generate a user profile")

# Second generation with same prompt (fast - cached)
result2 = cached_jsonformer.generate("Generate a user profile")

# Check cache statistics
stats = cached_jsonformer.get_cache_stats()
print("Cache Stats:", stats)
```

#### Batch Processing

```python
from jsonAI.performance import BatchProcessor, OptimizedJsonformer

# Create optimized jsonformer
optimized_jsonformer = OptimizedJsonformer(
    model=model,
    tokenizer=tokenizer,
    schema=schema,
    max_concurrent=10
)

# Prepare batch requests
requests = [
    {"prompt": f"Generate user profile {i}", "kwargs": {"temperature": 0.1}}
    for i in range(10)
]

# Process batch
results = optimized_jsonformer.generate_batch(requests)

# Check results
for result in results:
    if result["status"] == "success":
        print(f"ID: {result['id']}, Result: {result['result']}")
    else:
        print(f"ID: {result['id']}, Error: {result['error']}")
```

#### Performance Monitoring

```python
from jsonAI.performance import PerformanceMonitor

monitor = PerformanceMonitor()

# Monitor operations
monitor.start_operation("generation_test")

# Your generation code here
result = jsonformer.generate("Generate test data")

# End monitoring
duration = monitor.end_operation("generation_test")
print(f"Generation took {duration:.2f} seconds")

# Get comprehensive stats
stats = monitor.get_all_stats()
print("Performance Stats:", stats)
```

---

## Production Deployment

### Tutorial 9: Docker Deployment

#### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "jsonAI.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose Setup

```yaml
version: '3.8'

services:
  jsonai-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_WORKERS=4
      - CACHE_TTL=3600
    volumes:
      - ./models:/app/models
    restart: unless-stopped
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - jsonai-api
    restart: unless-stopped

volumes:
  ollama_data:
```

#### Deploy and Test

```bash
# Build and start services
docker-compose up -d

# Test API
curl http://localhost/health

# Generate JSON
curl -X POST http://localhost/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a test user",
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"}
      }
    }
  }'
```

---

## Real-World Examples

### Tutorial 10: E-commerce Application

Generate product catalogs for an e-commerce platform:

```python
from jsonAI import Jsonformer
from jsonAI.model_backends import get_model_and_tokenizer
import json

# Initialize
model, tokenizer = get_model_and_tokenizer("ollama", "llama2")

# Product schema
product_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "category": {
            "type": "string",
            "enum": ["electronics", "clothing", "home", "books", "sports"]
        },
        "price": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "specifications": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "model": {"type": "string"},
                "warranty": {"type": "string"}
            }
        },
        "availability": {
            "type": "object",
            "properties": {
                "in_stock": {"type": "boolean"},
                "quantity": {"type": "integer", "minimum": 0},
                "location": {"type": "string"}
            }
        },
        "reviews": {
            "type": "object",
            "properties": {
                "average_rating": {"type": "number", "minimum": 0, "maximum": 5},
                "total_reviews": {"type": "integer", "minimum": 0}
            }
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10
        }
    },
    "required": ["id", "name", "description", "category", "price", "currency"]
}

jsonformer = Jsonformer(model, tokenizer, product_schema)

# Generate different product types
categories = ["electronics", "clothing", "home", "books", "sports"]
products = []

for category in categories:
    prompt = f"Generate a {category} product for an online store with detailed specifications"
    product = jsonformer.generate(prompt, temperature=0.3)
    products.append(product)

# Save product catalog
with open("product_catalog.json", "w") as f:
    json.dump(products, f, indent=2)

print(f"Generated {len(products)} products")
for product in products:
    print(f"- {product['name']} ({product['category']}): ${product['price']}")
```

### Tutorial 11: API Response Generation

Generate consistent API responses:

```python
# API response schema
api_response_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "code": {"type": "integer"},
        "message": {"type": "string"},
        "data": {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "profile": {
                                "type": "object",
                                "properties": {
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "avatar_url": {"type": "string"},
                                    "bio": {"type": "string"}
                                }
                            },
                            "created_at": {"type": "string"},
                            "last_login": {"type": "string"}
                        }
                    }
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "current_page": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "total_items": {"type": "integer"},
                        "items_per_page": {"type": "integer"}
                    }
                }
            }
        },
        "timestamp": {"type": "string"}
    }
}

jsonformer = Jsonformer(model, tokenizer, api_response_schema)

# Generate sample API response
response = jsonformer.generate(
    "Generate a successful API response for getting a list of users with pagination",
    temperature=0.1
)

print("Generated API Response:")
print(json.dumps(response, indent=2))
```

### Tutorial 12: Test Data Generation

Generate test data for applications:

```python
# Test user schema
test_user_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "user_id": {"type": "integer", "minimum": 1000, "maximum": 9999},
            "username": {"type": "string"},
            "email": {"type": "string"},
            "age": {"type": "integer", "minimum": 18, "maximum": 80},
            "country": {"type": "string"},
            "subscription": {
                "type": "string",
                "enum": ["free", "premium", "enterprise"]
            },
            "preferences": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string", "enum": ["light", "dark"]},
                    "language": {"type": "string"},
                    "notifications": {"type": "boolean"}
                }
            },
            "created_at": {"type": "string"},
            "last_active": {"type": "string"}
        }
    },
    "minItems": 10,
    "maxItems": 20
}

jsonformer = Jsonformer(model, tokenizer, test_user_schema)

# Generate test users
test_users = jsonformer.generate(
    "Generate diverse test users for a software application with different countries and preferences",
    temperature=0.4
)

print(f"Generated {len(test_users)} test users")

# Save to file for testing
with open("test_users.json", "w") as f:
    json.dump(test_users, f, indent=2)

# Generate SQL INSERT statements
with open("test_users.sql", "w") as f:
    f.write("-- Test user data\n")
    for user in test_users:
        f.write(f"INSERT INTO users (user_id, username, email, age, country, subscription) VALUES ")
        f.write(f"({user['user_id']}, '{user['username']}', '{user['email']}', {user['age']}, '{user['country']}', '{user['subscription']}');\n")
```

### Tutorial 13: Configuration Generation

Generate application configurations:

```python
# Application config schema
config_schema = {
    "type": "object",
    "properties": {
        "application": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "environment": {"type": "string", "enum": ["development", "staging", "production"]},
                "debug": {"type": "boolean"}
            }
        },
        "database": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1000, "maximum": 65535},
                "name": {"type": "string"},
                "ssl": {"type": "boolean"},
                "pool_size": {"type": "integer", "minimum": 1, "maximum": 100}
            }
        },
        "cache": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "ttl": {"type": "integer", "minimum": 60},
                "max_size": {"type": "integer", "minimum": 100}
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "format": {"type": "string"},
                "file": {"type": "string"}
            }
        },
        "features": {
            "type": "object",
            "properties": {
                "user_registration": {"type": "boolean"},
                "email_notifications": {"type": "boolean"},
                "analytics": {"type": "boolean"}
            }
        }
    }
}

jsonformer = Jsonformer(model, tokenizer, config_schema)

# Generate configs for different environments
environments = ["development", "staging", "production"]

for env in environments:
    config = jsonformer.generate(
        f"Generate application configuration for {env} environment with appropriate settings",
        temperature=0.2
    )
    
    # Save config file
    with open(f"config_{env}.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Generated {env} configuration")
```

---

## Advanced Integration Patterns

### Tutorial 14: Streaming Generation

For large JSON generation with progress tracking:

```python
from jsonAI.async_generation import AsyncJsonformer
import asyncio

async def generate_with_progress():
    """Generate JSON with progress tracking."""
    model, tokenizer = get_model_and_tokenizer("ollama", "llama2")
    
    async_jsonformer = AsyncJsonformer(model, tokenizer, large_schema)
    
    # Custom progress callback
    def progress_callback(current_tokens, total_tokens):
        percentage = (current_tokens / total_tokens) * 100
        print(f"Progress: {percentage:.1f}% ({current_tokens}/{total_tokens} tokens)")
    
    result = await async_jsonformer.generate_async(
        prompt="Generate comprehensive data",
        progress_callback=progress_callback
    )
    
    return result

# Run async generation
result = asyncio.run(generate_with_progress())
```

### Tutorial 15: Custom Validation

Implement custom validation logic:

```python
from jsonAI.schema_validator import validate_schema
import re

def custom_email_validator(email):
    """Custom email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_generated_data(data, schema):
    """Validate generated data with custom rules."""
    # First, validate against JSON schema
    is_valid, errors = validate_schema(schema)
    if not is_valid:
        return False, errors
    
    # Custom validation rules
    custom_errors = []
    
    if "email" in data:
        if not custom_email_validator(data["email"]):
            custom_errors.append("Invalid email format")
    
    if "age" in data:
        if data["age"] < 0 or data["age"] > 150:
            custom_errors.append("Age must be between 0 and 150")
    
    return len(custom_errors) == 0, custom_errors

# Usage
result = jsonformer.generate("Generate user data")
is_valid, errors = validate_generated_data(result, schema)

if not is_valid:
    print("Validation errors:", errors)
else:
    print("Data is valid!")
```

This comprehensive tutorial guide covers all major aspects of using JsonAI, from basic generation to advanced production deployments. Each tutorial builds upon previous concepts and provides practical, real-world examples that users can adapt to their specific needs.
