"""
Security Middleware Configuration
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware


def setup_security_middleware(app: FastAPI) -> None:
    """
    Setup security middleware for the application
    """
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=[
            "localhost", 
            "127.0.0.1", 
            "*.vercel.app", 
            "*.onrender.com", 
            "*.ngrok-free.app"
        ]
    )


async def add_security_headers(request: Request, call_next) -> Response:
    """
    Add security headers to all responses
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


async def add_hsts_header(request: Request, call_next) -> Response:
    """
    Add HSTS header to all responses
    """
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
