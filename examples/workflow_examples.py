"""
Example workflow configurations for JsonAI

This file contains comprehensive examples of workflow automation scenarios
including API testing, data generation, and integration workflows.
"""

# Example 1: API Testing Workflow
api_testing_workflow = {
    "name": "api_testing_workflow",
    "version": "1.0",
    "description": "Comprehensive API testing workflow with data generation",
    "variables": {
        "api_base_url": "https://jsonplaceholder.typicode.com",
        "environment": "dev",
        "max_retries": 3
    },
    "steps": [
        {
            "id": "generate_user_data",
            "name": "Generate Test User Data",
            "type": "json_generation",
            "config": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string"},
                        "website": {"type": "string", "format": "uri"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "suite": {"type": "string"},
                                "city": {"type": "string"},
                                "zipcode": {"type": "string"},
                                "geo": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "string"},
                                        "lng": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "company": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "catchPhrase": {"type": "string"},
                                "bs": {"type": "string"}
                            }
                        }
                    },
                    "required": ["name", "username", "email"]
                },
                "prompt": "Generate a realistic user profile for API testing",
                "output_variable": "test_user_data"
            }
        },
        {
            "id": "create_user_api_test",
            "name": "Test Create User API",
            "type": "api_request",
            "depends_on": ["generate_user_data"],
            "config": {
                "method": "POST",
                "url": "${api_base_url}/users",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": "${test_user_data}",
                "expected_status": 201,
                "output_variable": "create_user_response"
            },
            "retry_count": 3,
            "timeout": 30
        },
        {
            "id": "validate_user_creation",
            "name": "Validate User Creation Response",
            "type": "data_validation",
            "depends_on": ["create_user_api_test"],
            "config": {
                "data_variable": "create_user_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "body": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                                "email": {"type": "string", "format": "email"}
                            },
                            "required": ["id", "name", "email"]
                        },
                        "status_code": {"type": "integer", "enum": [201]}
                    }
                },
                "fail_on_invalid": True
            }
        },
        {
            "id": "get_user_api_test",
            "name": "Test Get User API",
            "type": "api_request",
            "depends_on": ["validate_user_creation"],
            "config": {
                "method": "GET",
                "url": "${api_base_url}/users/1",
                "headers": {
                    "Accept": "application/json"
                },
                "expected_status": 200,
                "output_variable": "get_user_response"
            }
        },
        {
            "id": "cleanup_test_data",
            "name": "Cleanup Test Data",
            "type": "cleanup",
            "depends_on": ["get_user_api_test"],
            "config": {
                "variables": ["test_user_data", "create_user_response"]
            },
            "on_failure": "always"
        }
    ],
    "error_handling": {
        "retry_count": 3,
        "timeout": 300,
        "on_failure": "continue"
    },
    "notifications": {
        "on_success": {
            "type": "webhook",
            "url": "https://hooks.slack.com/workflow/success"
        },
        "on_failure": {
            "type": "email",
            "to": "dev-team@company.com",
            "subject": "API Testing Workflow Failed"
        }
    }
}

# Example 2: Data Pipeline Workflow
data_pipeline_workflow = {
    "name": "data_pipeline_workflow",
    "version": "1.0",
    "description": "Data generation and transformation pipeline",
    "variables": {
        "batch_size": 100,
        "output_format": "json"
    },
    "steps": [
        {
            "id": "generate_customer_data",
            "name": "Generate Customer Data Batch",
            "type": "json_generation",
            "config": {
                "schema": {
                    "type": "array",
                    "maxItems": 100,
                    "items": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string", "format": "uuid"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "age": {"type": "integer", "minimum": 18, "maximum": 100},
                            "subscription_tier": {
                                "type": "string",
                                "enum": ["basic", "premium", "enterprise"]
                            },
                            "created_at": {"type": "string", "format": "date-time"},
                            "total_spent": {"type": "number", "minimum": 0}
                        },
                        "required": ["customer_id", "first_name", "last_name", "email"]
                    }
                },
                "prompt": "Generate ${batch_size} realistic customer records for a SaaS platform",
                "output_variable": "customer_data"
            },
            "parallel": True
        },
        {
            "id": "filter_premium_customers",
            "name": "Filter Premium Customers",
            "type": "data_transformation",
            "depends_on": ["generate_customer_data"],
            "config": {
                "input_variable": "customer_data",
                "transformation": {
                    "type": "filter",
                    "condition": {
                        "type": "equals",
                        "field": "subscription_tier",
                        "value": "premium"
                    }
                },
                "output_variable": "premium_customers"
            }
        },
        {
            "id": "validate_customer_data",
            "name": "Validate Customer Data Quality",
            "type": "data_validation",
            "depends_on": ["generate_customer_data"],
            "config": {
                "data_variable": "customer_data",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["customer_id", "email"]
                    }
                },
                "fail_on_invalid": False
            }
        },
        {
            "id": "send_to_api",
            "name": "Send Data to API",
            "type": "api_request",
            "depends_on": ["validate_customer_data", "filter_premium_customers"],
            "config": {
                "method": "POST",
                "url": "https://api.crm.com/customers/batch",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer ${api_token}"
                },
                "body": "${customer_data}",
                "expected_status": 200
            },
            "conditions": {
                "step_success": "validate_customer_data"
            }
        }
    ]
}

# Example 3: Load Testing Workflow
load_testing_workflow = {
    "name": "load_testing_workflow",
    "version": "1.0",
    "description": "Load testing workflow with parallel requests",
    "variables": {
        "target_url": "https://api.example.com",
        "concurrent_users": 50,
        "requests_per_user": 10
    },
    "steps": [
        {
            "id": "generate_test_data_batch",
            "name": "Generate Test Data for Load Testing",
            "type": "json_generation",
            "config": {
                "schema": {
                    "type": "array",
                    "maxItems": 500,
                    "items": {
                        "type": "object",
                        "properties": {
                            "request_id": {"type": "string", "format": "uuid"},
                            "payload": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["create", "read", "update"]},
                                    "data": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "prompt": "Generate ${concurrent_users * requests_per_user} test requests for load testing",
                "output_variable": "load_test_data"
            }
        },
        {
            "id": "parallel_load_test",
            "name": "Execute Parallel Load Test",
            "type": "parallel",
            "depends_on": ["generate_test_data_batch"],
            "config": {
                "steps": [
                    {
                        "id": "load_test_batch_1",
                        "type": "api_request",
                        "config": {
                            "method": "POST",
                            "url": "${target_url}/test",
                            "body": "${load_test_data}",
                            "timeout": 60
                        }
                    }
                ]
            },
            "parallel": True
        }
    ]
}

# Example 4: CI/CD Integration Workflow
cicd_workflow = {
    "name": "cicd_integration_workflow",
    "version": "1.0",
    "description": "CI/CD pipeline integration with API testing",
    "variables": {
        "git_branch": "main",
        "environment": "staging",
        "deploy_url": "https://staging.api.com"
    },
    "steps": [
        {
            "id": "wait_for_deployment",
            "name": "Wait for Deployment",
            "type": "delay",
            "config": {
                "seconds": 30
            }
        },
        {
            "id": "health_check",
            "name": "API Health Check",
            "type": "api_request",
            "depends_on": ["wait_for_deployment"],
            "config": {
                "method": "GET",
                "url": "${deploy_url}/health",
                "expected_status": 200,
                "output_variable": "health_response"
            },
            "retry_count": 5,
            "timeout": 10
        },
        {
            "id": "run_smoke_tests",
            "name": "Run Smoke Tests",
            "type": "api_test_collection",
            "depends_on": ["health_check"],
            "config": {
                "collection_path": "./collections/smoke_tests.json",
                "collection_type": "postman",
                "environment": "${environment}",
                "output_variable": "smoke_test_results"
            }
        },
        {
            "id": "validate_smoke_tests",
            "name": "Validate Smoke Test Results",
            "type": "conditional",
            "depends_on": ["run_smoke_tests"],
            "config": {
                "condition": {
                    "type": "greater_than",
                    "field": "success_rate",
                    "value": 0.95
                }
            }
        },
        {
            "id": "notify_success",
            "name": "Notify Deployment Success",
            "type": "notification",
            "depends_on": ["validate_smoke_tests"],
            "config": {
                "type": "slack",
                "message": "🚀 Deployment to ${environment} successful! All smoke tests passed.",
                "channel": "#deployments"
            },
            "conditions": {
                "step_success": "validate_smoke_tests"
            }
        },
        {
            "id": "notify_failure",
            "name": "Notify Deployment Failure",
            "type": "notification",
            "depends_on": ["validate_smoke_tests"],
            "config": {
                "type": "slack",
                "message": "❌ Deployment to ${environment} failed! Smoke tests did not pass.",
                "channel": "#deployments"
            },
            "conditions": {
                "step_failure": "validate_smoke_tests"
            }
        }
    ],
    "schedule": {
        "type": "cron",
        "expression": "0 */2 * * *"  # Every 2 hours
    }
}

# Example 5: E-commerce Testing Workflow
ecommerce_workflow = {
    "name": "ecommerce_testing_workflow",
    "version": "1.0",
    "description": "End-to-end e-commerce API testing workflow",
    "variables": {
        "store_url": "https://api.store.com",
        "admin_token": "admin_secret_token"
    },
    "steps": [
        {
            "id": "generate_product_data",
            "name": "Generate Product Data",
            "type": "json_generation",
            "config": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "price": {"type": "number", "minimum": 0.01},
                        "category": {"type": "string", "enum": ["electronics", "clothing", "books"]},
                        "inventory": {"type": "integer", "minimum": 0, "maximum": 1000},
                        "sku": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["name", "price", "category", "sku"]
                },
                "prompt": "Generate a realistic product for an e-commerce store",
                "output_variable": "product_data"
            }
        },
        {
            "id": "create_product",
            "name": "Create Product via API",
            "type": "api_request",
            "depends_on": ["generate_product_data"],
            "config": {
                "method": "POST",
                "url": "${store_url}/products",
                "headers": {
                    "Authorization": "Bearer ${admin_token}",
                    "Content-Type": "application/json"
                },
                "body": "${product_data}",
                "expected_status": 201,
                "output_variable": "created_product"
            }
        },
        {
            "id": "generate_customer_data",
            "name": "Generate Customer Data",
            "type": "json_generation",
            "depends_on": ["create_product"],
            "config": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "minLength": 8},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                                "state": {"type": "string"},
                                "zip": {"type": "string"},
                                "country": {"type": "string"}
                            }
                        }
                    },
                    "required": ["email", "password", "first_name", "last_name"]
                },
                "prompt": "Generate customer registration data",
                "output_variable": "customer_data"
            }
        },
        {
            "id": "register_customer",
            "name": "Register Customer",
            "type": "api_request",
            "depends_on": ["generate_customer_data"],
            "config": {
                "method": "POST",
                "url": "${store_url}/customers/register",
                "headers": {"Content-Type": "application/json"},
                "body": "${customer_data}",
                "expected_status": 201,
                "output_variable": "registered_customer"
            }
        },
        {
            "id": "login_customer",
            "name": "Login Customer",
            "type": "api_request",
            "depends_on": ["register_customer"],
            "config": {
                "method": "POST",
                "url": "${store_url}/auth/login",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "email": "${customer_data.email}",
                    "password": "${customer_data.password}"
                },
                "expected_status": 200,
                "output_variable": "login_response"
            }
        },
        {
            "id": "add_to_cart",
            "name": "Add Product to Cart",
            "type": "api_request",
            "depends_on": ["login_customer"],
            "config": {
                "method": "POST",
                "url": "${store_url}/cart/items",
                "headers": {
                    "Authorization": "Bearer ${login_response.body.token}",
                    "Content-Type": "application/json"
                },
                "body": {
                    "product_id": "${created_product.body.id}",
                    "quantity": 1
                },
                "expected_status": 200,
                "output_variable": "cart_response"
            }
        },
        {
            "id": "checkout",
            "name": "Checkout Process",
            "type": "api_request",
            "depends_on": ["add_to_cart"],
            "config": {
                "method": "POST",
                "url": "${store_url}/orders/checkout",
                "headers": {
                    "Authorization": "Bearer ${login_response.body.token}",
                    "Content-Type": "application/json"
                },
                "body": {
                    "payment_method": "credit_card",
                    "shipping_address": "${customer_data.address}"
                },
                "expected_status": 201,
                "output_variable": "order_response"
            }
        },
        {
            "id": "verify_order",
            "name": "Verify Order Creation",
            "type": "data_validation",
            "depends_on": ["checkout"],
            "config": {
                "data_variable": "order_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "body": {
                            "type": "object",
                            "properties": {
                                "order_id": {"type": "string"},
                                "status": {"type": "string", "enum": ["pending", "confirmed"]},
                                "total": {"type": "number", "minimum": 0}
                            },
                            "required": ["order_id", "status", "total"]
                        }
                    }
                }
            }
        },
        {
            "id": "cleanup_test_order",
            "name": "Cleanup Test Order",
            "type": "api_request",
            "depends_on": ["verify_order"],
            "config": {
                "method": "DELETE",
                "url": "${store_url}/orders/${order_response.body.order_id}",
                "headers": {
                    "Authorization": "Bearer ${admin_token}"
                },
                "expected_status": 204
            },
            "on_failure": "continue"
        }
    ],
    "error_handling": {
        "retry_count": 2,
        "timeout": 60
    }
}

# Export all examples
WORKFLOW_EXAMPLES = {
    "api_testing": api_testing_workflow,
    "data_pipeline": data_pipeline_workflow,
    "load_testing": load_testing_workflow,
    "cicd_integration": cicd_workflow,
    "ecommerce_testing": ecommerce_workflow
}