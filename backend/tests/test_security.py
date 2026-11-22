"""
Comprehensive Automated Test Suite for Feature #8 & #9: Security & Error Handling.
Covers:
1. Protective Security Headers validation (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy).
2. Clean HTTP 422 RequestValidationError structured payload without stack traces.
3. Protected routes rejecting invalid/tampered/expired JWTs with HTTP 401.
4. In-memory Rate Limiting triggering HTTP 429 Too Many Requests on burst attempts and resetting.
5. Resume upload validation rejecting corrupted/invalid files safely.
6. Rate limiter bypass header support for automated testing.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.middleware import rate_limiter
from backend.app.core.database import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Ensure clean rate-limiter and database state for security tests."""
    rate_limiter.reset()
    db = get_db()
    db.reset_database()
    yield
    rate_limiter.reset()
    db.reset_database()


def test_01_security_headers_present():
    """Verify that all standard security headers are injected into API responses."""
    res = client.get("/api/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert headers.get("X-XSS-Protection") == "1; mode=block"


def test_02_validation_error_structured_response():
    """Verify malformed JSON payload returns structured HTTP 422 without raw tracebacks."""
    # Send invalid registration body missing required 'password' and 'full_name'
    res = client.post("/api/auth/register", json={"email": "invalid-email-format"})
    assert res.status_code == 422
    data = res.json()

    assert data["success"] is False
    assert data["error"] == "Validation Error"
    assert "detail" in data
    assert "errors" in data
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0

    # Ensure no internal file paths or tracebacks are leaked
    error_str = str(data)
    assert "Traceback (most recent call last)" not in error_str
    assert "site-packages" not in error_str
    assert "backend/app" not in error_str


def test_03_tampered_jwt_rejected():
    """Verify protected endpoints reject forged, malformed, or tampered JWT tokens."""
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.fakesignature123"

    # Test /api/auth/me
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_me.status_code == 401
    assert "detail" in res_me.json()

    # Test /api/history
    res_hist = client.get("/api/history", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_hist.status_code == 401


def test_04_rate_limiting_login_burst():
    """Verify that exceeding rate limit on /api/auth/login triggers HTTP 429 Too Many Requests."""
    rate_limiter.reset()

    # Make 20 rapid login attempts (the limit is 20 per minute)
    for i in range(20):
        res = client.post("/api/auth/login", json={
            "email": f"user{i}@example.com",
            "password": "wrongpassword"
        })
        # Should return 401 or 404 (invalid credentials), NOT 429 yet
        assert res.status_code in [400, 401, 404]

    # The 21st attempt from the same client IP should trigger rate limiting (HTTP 429)
    res_blocked = client.post("/api/auth/login", json={
        "email": "user21@example.com",
        "password": "wrongpassword"
    })
    assert res_blocked.status_code == 429
    data = res_blocked.json()
    assert data["success"] is False
    assert data["error"] == "Too Many Requests"
    assert "Retry-After" in res_blocked.headers

    # Verify rate limiter reset clears the restriction
    rate_limiter.reset()
    res_after_reset = client.post("/api/auth/login", json={
        "email": "user22@example.com",
        "password": "wrongpassword"
    })
    assert res_after_reset.status_code in [400, 401, 404]


def test_05_rate_limit_test_bypass_header():
    """Verify that requests with x-bypass-rate-limit header bypass rate limiting."""
    rate_limiter.reset()

    # Fill rate limit bucket
    for i in range(20):
        client.post("/api/auth/login", json={"email": "u@test.com", "password": "p"})

    # Next attempt without header is blocked
    assert client.post("/api/auth/login", json={"email": "u@test.com", "password": "p"}).status_code == 429

    # Same attempt with x-bypass-rate-limit header succeeds past rate limiter
    bypassed_res = client.post(
        "/api/auth/login",
        json={"email": "u@test.com", "password": "p"},
        headers={"x-bypass-rate-limit": "true"}
    )
    assert bypassed_res.status_code in [400, 401, 404]


def test_06_corrupted_file_upload_rejection_no_leak():
    """Verify that invalid resume uploads return safe 400 Bad Request without leaking internal paths."""
    corrupted_bytes = b"Not a real PDF or DOCX file content"
    files = {"file": ("fake_resume.pdf", corrupted_bytes, "application/pdf")}

    res = client.post("/api/resume/analyze", files=files)
    assert res.status_code == 400
    data = res.json()

    assert "detail" in data
    # Ensure no internal python stack traces or system file descriptors are exposed
    assert "Traceback" not in data["detail"]
    assert "C:\\" not in data["detail"]
    assert "/home/" not in data["detail"]
