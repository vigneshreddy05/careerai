"""
Security and Authentication Utilities for CareerAI.
Implements:
1. Secure password hashing and verification via bcrypt.
2. Signed JSON Web Tokens (JWT) via PyJWT with minimum 32-character HMAC keys.
3. Stateless JWT token invalidation via version tracking and blocklists.
4. FastAPI dependency injection for protected endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from backend.app.core.config import settings
    from backend.app.core.database import get_db, DatabaseManager
except ModuleNotFoundError:
    from app.core.config import settings
    from app.core.database import get_db, DatabaseManager

# FastAPI HTTPBearer scheme
security_scheme = HTTPBearer(auto_error=True)


def get_password_hash(password: str) -> str:
    """Generate a secure salted bcrypt hash for a plain text password."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a candidate password against an existing bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    user_id: str,
    email: str,
    token_version: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Encode a signed JWT token containing user identity and token version."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email.lower(),
        "token_version": token_version,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token signature and expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: DatabaseManager = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts, verifies, and returns the authenticated user.
    Enforces immediate token invalidation on logout and account deletion.
    """
    token = credentials.credentials

    # 1. Check if token was explicitly blocklisted
    if db.is_token_blocklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated by logout. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Decode signature and expiry
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    token_version = payload.get("token_version")

    if not user_id or token_version is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Verify user exists in database
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Check token version (if user logged out elsewhere or version incremented, token is invalid)
    if user.get("token_version", 1) != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach raw token for logout endpoint convenience
    user["_current_token"] = token
    return user
