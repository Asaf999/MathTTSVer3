"""OpenAPI documentation configuration."""

from typing import Dict, Any


def get_openapi_config() -> Dict[str, Any]:
    """Get OpenAPI configuration."""
    return {
        "title": "MathTTS API",
        "description": """
# MathTTS API v3

LaTeX to Speech conversion API for mathematical expressions.

## Features

- **LaTeX Expression Processing**: Convert complex mathematical expressions to natural speech
- **Multiple TTS Providers**: Support for Edge-TTS, gTTS, and pyttsx3
- **Smart Caching**: Intelligent caching system for improved performance
- **Pattern-Based Conversion**: 541+ mathematical patterns for accurate conversion
- **Authentication**: JWT-based authentication and API key support
- **Rate Limiting**: Configurable rate limiting per IP, user, or API key
- **Monitoring**: Prometheus metrics and health checks

## Authentication

This API supports two authentication methods:

### 1. JWT Bearer Token
For user-based authentication:
```
POST /api/v1/auth/login
Authorization: Bearer <token>
```

### 2. API Key
For service-to-service authentication:
```
X-API-Key: <api-key>
```

## Rate Limits

- **Anonymous**: 60 requests/minute
- **Authenticated Users**: 1000 requests/hour
- **API Keys**: Custom limits per key

## Quick Start

1. Get an access token:
```bash
curl -X POST /api/v1/auth/login \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=testuser&password=user123"
```

2. Convert a LaTeX expression:
```bash
curl -X POST /api/v1/expressions/process \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json" \\
  -d '{"latex": "\\\\frac{1}{2}"}'
```

## Mathematical Domains

The API supports expressions from various mathematical domains:
- Algebra
- Calculus
- Linear Algebra
- Statistics
- Set Theory
- Logic
- Number Theory
- And more...

## Error Handling

All errors follow a consistent format:
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "request_id": "correlation-id"
}
```

## Support

For issues or questions, please contact the development team.
        """,
        "version": "3.0.0",
        "contact": {
            "name": "MathTTS Development Team",
            "email": "support@mathtts.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "servers": [
            {
                "url": "https://api.mathtts.com",
                "description": "Production server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        "tags": [
            {
                "name": "authentication",
                "description": "User authentication and authorization"
            },
            {
                "name": "expressions",
                "description": "LaTeX expression processing"
            },
            {
                "name": "patterns",
                "description": "Pattern management"
            },
            {
                "name": "voices",
                "description": "TTS voice management"
            },
            {
                "name": "health",
                "description": "Health checks and monitoring"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT authentication token"
                },
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for service authentication"
                }
            }
        }
    }


def get_custom_openapi_schema(app) -> Dict[str, Any]:
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Add custom configuration
    config = get_openapi_config()
    openapi_schema.update(config)
    
    # Add response examples
    openapi_schema["components"]["schemas"]["HTTPValidationError"]["example"] = {
        "detail": [
            {
                "loc": ["body", "latex"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    
    # Add authentication examples
    if "Token" in openapi_schema["components"]["schemas"]:
        openapi_schema["components"]["schemas"]["Token"]["example"] = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema