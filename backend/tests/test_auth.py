"""
Comprehensive Automated Test Suite for Feature #1: User Authentication & Profile Management.
Covers:
1. User Registration (POST /api/auth/register)
2. Duplicate Email Rejection (HTTP 400)
3. Password & Email Validation (HTTP 422)
4. Password Hashing Verification (bcrypt)
5. User Login (POST /api/auth/login)
6. Invalid Credentials Handling (HTTP 401)
7. Profile Retrieval (GET /api/auth/me)
8. Unauthenticated Access Protection (HTTP 401/403)
9. Profile Attribute & Privacy Updates (PUT /api/auth/profile)
10. Logout & Immediate Token Invalidation (HTTP 401 on reused token)
11. Account Deletion & Permanent Purge (DELETE /api/auth/account)
"""

import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.core.database import get_db
    from backend.app.core.security import verify_password
except ModuleNotFoundError:
    from app.main import app
    from app.core.database import get_db
    from app.core.security import verify_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure a clean database state before each test."""
    db = get_db()
    db.reset_database()
    yield
    db.reset_database()


# ==============================================================================
# Test Scenario 1: User Registration Success
# ==============================================================================
def test_01_register_success():
    """Verify successful candidate registration returns JWT token and safe profile."""
    payload = {
        "email": "candidate@example.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Doe",
        "current_role": "Computer Science Student",
        "experience_years": 1.5,
        "target_role": "Full Stack Software Engineer",
        "save_resume_text": False,
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert len(data["token"]) > 30

    user = data["user"]
    assert user["email"] == "candidate@example.com"
    assert user["full_name"] == "Jane Doe"
    assert user["current_role"] == "Computer Science Student"
    assert user["experience_years"] == 1.5
    assert user["target_role"] == "Full Stack Software Engineer"
    assert user["save_resume_text"] is False
    assert "hashed_password" not in user
    assert "token_version" not in user


# ==============================================================================
# Test Scenario 2: Duplicate Email Rejection
# ==============================================================================
def test_02_duplicate_email_rejection():
    """Verify that registering with an already existing email returns HTTP 400."""
    payload = {
        "email": "unique@example.com",
        "password": "Password123!",
        "full_name": "First User",
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    # Second registration with same email (case-insensitive)
    payload_dup = {
        "email": "UNIQUE@example.com",
        "password": "DifferentPassword123!",
        "full_name": "Second User",
    }
    r2 = client.post("/api/auth/register", json=payload_dup)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


# ==============================================================================
# Test Scenario 3: Registration Input Validation
# ==============================================================================
def test_03_registration_validation():
    """Verify that invalid email or short password is rejected with HTTP 422."""
    # Invalid email
    r1 = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "full_name": "Test User",
    })
    assert r1.status_code == 422

    # Password too short (< 8 chars)
    r2 = client.post("/api/auth/register", json={
        "email": "user@example.com",
        "password": "short",
        "full_name": "Test User",
    })
    assert r2.status_code == 422


# ==============================================================================
# Test Scenario 4: Bcrypt Password Hashing
# ==============================================================================
def test_04_bcrypt_password_hashing():
    """Verify that stored password in DB is a genuine salted bcrypt hash."""
    raw_password = "MySuperSecretPassword2026!"
    payload = {
        "email": "hashed@example.com",
        "password": raw_password,
        "full_name": "Security Tester",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201

    db = get_db()
    stored_user = db.get_user_by_email("hashed@example.com")
    assert stored_user is not None
    assert stored_user["hashed_password"] != raw_password
    assert stored_user["hashed_password"].startswith("$2b$") or stored_user["hashed_password"].startswith("$2a$")
    assert verify_password(raw_password, stored_user["hashed_password"]) is True
    assert verify_password("WrongPassword!", stored_user["hashed_password"]) is False


# ==============================================================================
# Test Scenario 5: User Login Success
# ==============================================================================
def test_05_login_success():
    """Verify valid credentials return a functioning JWT token."""
    # Register first
    client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "LoginPass123!",
        "full_name": "Login Tester",
    })

    # Log in
    login_res = client.post("/api/auth/login", json={
        "email": "LOGIN@example.com",  # verify case insensitivity
        "password": "LoginPass123!",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["email"] == "login@example.com"


# ==============================================================================
# Test Scenario 6: Invalid Credentials Rejection
# ==============================================================================
def test_06_invalid_credentials_rejection():
    """Verify non-existent user or incorrect password returns HTTP 401."""
    # Non-existent user
    r1 = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "SomePassword123!",
    })
    assert r1.status_code == 401

    # Wrong password
    client.post("/api/auth/register", json={
        "email": "wrongpwd@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Test User",
    })
    r2 = client.post("/api/auth/login", json={
        "email": "wrongpwd@example.com",
        "password": "IncorrectPassword999!",
    })
    assert r2.status_code == 401


# ==============================================================================
# Test Scenario 7: Profile Retrieval (/me)
# ==============================================================================
def test_07_profile_retrieval_me():
    """Verify GET /api/auth/me returns the logged in user profile."""
    reg = client.post("/api/auth/register", json={
        "email": "me@example.com",
        "password": "MyPassword123!",
        "full_name": "Current User",
        "current_role": "Backend Developer",
    })
    token = reg.json()["token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user = res.json()["user"]
    assert user["email"] == "me@example.com"
    assert user["full_name"] == "Current User"
    assert user["current_role"] == "Backend Developer"


# ==============================================================================
# Test Scenario 8: Unauthenticated Access Protection
# ==============================================================================
def test_08_unauthenticated_access_protection():
    """Verify protected endpoints reject missing or invalid tokens."""
    # Missing token
    r1 = client.get("/api/auth/me")
    assert r1.status_code in [401, 403]

    # Malformed token
    r2 = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert r2.status_code == 401


# ==============================================================================
# Test Scenario 9: Profile Update
# ==============================================================================
def test_09_profile_update():
    """Verify PUT /api/auth/profile updates candidate attributes and privacy preferences."""
    reg = client.post("/api/auth/register", json={
        "email": "update@example.com",
        "password": "Password123!",
        "full_name": "Old Name",
        "experience_years": 1.0,
    })
    token = reg.json()["token"]

    update_payload = {
        "full_name": "New Name",
        "current_role": "Mid-Level Engineer",
        "experience_years": 3.0,
        "target_role": "Lead Architect",
        "save_resume_text": True,
    }
    update_res = client.put(
        "/api/auth/profile",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    updated = update_res.json()["user"]
    assert updated["full_name"] == "New Name"
    assert updated["current_role"] == "Mid-Level Engineer"
    assert updated["experience_years"] == 3.0
    assert updated["target_role"] == "Lead Architect"
    assert updated["save_resume_text"] is True


# ==============================================================================
# Test Scenario 10: Logout & Token Invalidation
# ==============================================================================
def test_10_logout_token_invalidation():
    """Verify POST /api/auth/logout invalidates token so subsequent calls return HTTP 401."""
    reg = client.post("/api/auth/register", json={
        "email": "logout@example.com",
        "password": "Password123!",
        "full_name": "Logout User",
    })
    token = reg.json()["token"]

    # Profile retrieval works prior to logout
    r1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200

    # Execute logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Immediate token invalidation check: using the old token must now fail with 401
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401
    assert "invalidated" in r2.json()["detail"].lower()


# ==============================================================================
# Test Scenario 11: Account Deletion Token Invalidation & Data Purge
# ==============================================================================
def test_11_account_deletion():
    """Verify DELETE /api/auth/account purges user data and invalidates token immediately."""
    reg = client.post("/api/auth/register", json={
        "email": "delete@example.com",
        "password": "Password123!",
        "full_name": "Delete Me",
    })
    token = reg.json()["token"]
    user_id = reg.json()["user"]["id"]

    # Delete account
    del_res = client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Token must be invalidated
    r1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 401

    # User record must be completely gone from database
    db = get_db()
    assert db.get_user_by_id(user_id) is None
    assert db.get_user_by_email("delete@example.com") is None
