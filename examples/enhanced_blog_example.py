"""
Enhanced Blog Post Metadata Generation Example
Demonstrates how to create meaningful content with proper prompts and schemas
"""

import json
from jsonAI.model_backends import OllamaBackend
from jsonAI.main import Jsonformer

def create_enhanced_blog_schema():
    """Create a detailed schema with descriptions and examples."""
    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "An engaging, SEO-friendly blog post title that captures the main topic",
                "examples": [
                    "10 Essential Python Tips for Data Scientists",
                    "How Machine Learning is Revolutionizing Healthcare",
                    "Building Scalable Web Applications with React and Node.js"
                ]
            },
            "content": {
                "type": "string",
                "description": "A comprehensive blog post content that provides value to readers",
                "examples": [
                    "In today's data-driven world, Python has become the go-to language for data scientists...",
                    "Machine learning algorithms are transforming healthcare by enabling predictive diagnostics...",
                    "Modern web applications require scalability, performance, and maintainability..."
                ]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant tags for SEO and categorization",
                "examples": [
                    ["python", "data-science", "programming"],
                    ["machine-learning", "healthcare", "ai"],
                    ["web-development", "react", "javascript"]
                ]
            },
            "category": {
                "type": "string",
                "enum": ["tutorial", "news", "opinion", "review", "case-study"],
                "description": "The primary category that best fits the blog post content",
                "examples": ["tutorial", "news", "opinion"]
            }
        },
        "required": ["title", "content", "category"]
    }

def create_enhanced_prompt():
    """Create a detailed prompt with context and examples."""
    return """You are a professional content strategist. Create metadata for a high-quality technical blog post about software development or technology.

Context: This blog post should provide valuable insights, practical advice, or educational content for developers and tech professionals.

Examples of excellent blog posts:
1. Title: "Mastering Async Programming in Python"
   Content: "Asynchronous programming has become essential for building responsive applications. This comprehensive guide covers event loops, coroutines, and best practices for writing efficient async code."
   Tags: ["python", "async", "concurrency", "programming"]
   Category: "tutorial"

2. Title: "The Future of AI in Software Development"
   Content: "Artificial intelligence is revolutionizing how we write, test, and deploy software. From code generation to automated testing, AI tools are becoming indispensable for modern developers."
   Tags: ["ai", "software-development", "automation", "future-tech"]
   Category: "opinion"

3. Title: "Building REST APIs with FastAPI: A Complete Guide"
   Content: "FastAPI has emerged as the go-to framework for building high-performance APIs in Python. This tutorial covers everything from basic setup to advanced features like dependency injection and background tasks."
   Tags: ["fastapi", "python", "api", "web-development"]
   Category: "tutorial"

Requirements:
- Create a NEW blog post (not one of the examples above)
- Title: Engaging, SEO-friendly, 5-15 words
- Content: First paragraph or summary, 20-50 words, informative and valuable
- Tags: 2-4 relevant, specific tags
- Category: Choose from tutorial, news, opinion, review, or case-study

IMPORTANT: Respond with actual blog post data, not a schema or template.

Generate the blog post metadata:
"""

def main():
    """Run the enhanced blog post generation example."""
    print("🎯 Enhanced Blog Post Metadata Generation")
    print("=" * 50)

    # Create Ollama backend with optimized settings
    backend = OllamaBackend(model_name="mistral", max_retries=3)

    # Get enhanced schema and prompt
    schema = create_enhanced_blog_schema()
    prompt = create_enhanced_prompt()

    # Create Jsonformer with optimized parameters
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt=prompt,
        ollama_options={
            "temperature": 0.3,  # Lower for more focused content
            "top_p": 0.9,
            "repeat_penalty": 1.2
        }
    )

    print("Generating blog post metadata with enhanced context...")

    # Generate data
    result = jsonformer.generate_data()

    print("\n📝 Generated Blog Post Metadata:")
    print("=" * 30)
    print(json.dumps(result, indent=2))

    # Validate the result has meaningful content
    if result and 'title' in result:
        title_words = result['title'].split()
        if len(title_words) >= 3 and not any(word.isdigit() for word in title_words[:3]):
            print("\n✅ Success: Generated meaningful, contextual content!")
        else:
            print("\n⚠️  Warning: Content may still need improvement")

if __name__ == "__main__":
    main()
