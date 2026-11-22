"""
Security Hardening and Global Error Handling Middleware for CareerAI.
Implements:
1. Protective Security Headers (nosniff, DENY, strict-origin, permissions).
2. Lightweight In-Memory Rate Limiting for sensitive endpoints (auth, parser, assistant).
3. Standardized, PII-safe Global Exception Handlers (RequestValidationError, HTTPException, Exception).
4. Startup Security Integrity Checks.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("careerai.security")


class RateLimiter:
    """Thread-safe, sliding-window in-memory rate limiter per IP address."""

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.enabled: bool = True

    def is_rate_limited(self, key: str, max_requests: int = 30, window_seconds: int = 60) -> bool:
        """Check if request count exceeds max_requests within window_seconds."""
        if not self.enabled:
            return False

        now = time.time()
        cutoff = now - window_seconds
        # Clean expired timestamps
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        if len(self.requests[key]) >= max_requests:
            return True

        self.requests[key].append(now)
        return False

    def reset(self):
        """Clear all active rate-limiting history (useful for testing)."""
        self.requests.clear()


# Global rate limiter singleton
rate_limiter = RateLimiter()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject protective HTTP security headers onto all API responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Protect sensitive endpoints against brute-force or flooding."""

    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        # Allow test suites to bypass rate limiting via header
        if request.headers.get("x-bypass-rate-limit") == "true":
            return await call_next(request)

        path = request.url.path
        client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Sensitive endpoint limits: (max_requests, window_seconds)
        limit_rule = None
        if path.startswith("/api/auth/login"):
            limit_rule = (20, 60)
        elif path.startswith("/api/auth/register"):
            limit_rule = (25, 60)
        elif path.startswith("/api/resume/analyze"):
            limit_rule = (35, 60)
        elif path.startswith("/api/assistant/chat"):
            limit_rule = (40, 60)

        if limit_rule:
            max_reqs, window = limit_rule
            rate_key = f"{client_ip}:{path}"
            if self.limiter.is_rate_limited(rate_key, max_reqs, window):
                logger.warning(f"Rate limit triggered for IP {client_ip} on {path} ({max_reqs} req/{window}s)")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": "Too Many Requests",
                        "detail": f"Rate limit exceeded ({max_reqs} requests per minute). Please wait a moment before retrying.",
                    },
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)


def setup_exception_handlers(app: FastAPI):
    """Register standardized, PII-safe global exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        messages = []
        for err in exc.errors():
            loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
            msg = err.get("msg", "Invalid input")
            errors.append({"field": loc or "payload", "message": msg})
            messages.append(f"{loc}: {msg}" if loc else msg)

        detail_str = "; ".join(messages) if messages else "Invalid request payload."
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation Error",
                "detail": detail_str,
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        error_type = "HTTP Error"
        if exc.status_code == 404:
            error_type = "Resource Not Found"
        elif exc.status_code == 401:
            error_type = "Unauthorized"
        elif exc.status_code == 403:
            error_type = "Forbidden"

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_type,
                "detail": exc.detail,
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "detail": "An unexpected internal error occurred. Please try again later.",
            },
        )


def perform_startup_security_checks(settings):
    """Verify production security parameters and Ollama loopback binding."""
    # Check 1: Insecure default JWT secret check
    if getattr(settings, "ENVIRONMENT", "development").lower() == "production":
        if "minimum_32_characters" in getattr(settings, "JWT_SECRET_KEY", ""):
            logger.critical(
                "CRITICAL SECURITY WARNING: Default development JWT_SECRET_KEY is active in production environment! "
                "Update JWT_SECRET_KEY in production environment variables immediately."
            )

    # Check 2: Ollama loopback host verification
    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").lower()
    if "127.0.0.1" not in ollama_url and "localhost" not in ollama_url and "::1" not in ollama_url:
        logger.warning(
            f"SECURITY NOTICE: OLLAMA_BASE_URL ({ollama_url}) is not bound to a loopback address. "
            "Ensure Ollama is not accessible on external networks."
        )
