"""
Authentication and User Profile Management API Router.
Implements:
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
- PUT  /api/auth/profile
- DELETE /api/auth/account
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

try:
    from backend.app.schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        UserProfileUpdateRequest,
        UserProfileResponse,
        AuthSuccessResponse,
        ProfileResponse,
        AuthMessageResponse,
    )
    from backend.app.core.database import get_db, DatabaseManager
    from backend.app.core.security import (
        get_password_hash,
        verify_password,
        create_access_token,
        get_current_user,
    )
except ModuleNotFoundError:
    from app.schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        UserProfileUpdateRequest,
        UserProfileResponse,
        AuthSuccessResponse,
        ProfileResponse,
        AuthMessageResponse,
    )
    from app.core.database import get_db, DatabaseManager
    from app.core.security import (
        get_password_hash,
        verify_password,
        create_access_token,
        get_current_user,
    )

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register(
    payload: UserRegisterRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Register a new candidate profile with bcrypt-hashed credentials and generate an access token."""
    existing_user = db.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(payload.password)

    user_data = {
        "id": user_id,
        "email": payload.email,
        "hashed_password": hashed_pwd,
        "full_name": payload.full_name,
        "current_role": payload.current_role,
        "experience_years": payload.experience_years,
        "target_role": payload.target_role,
        "save_resume_text": payload.save_resume_text,
    }

    created_user = db.create_user(user_data)
    token = create_access_token(
        user_id=created_user["id"],
        email=created_user["email"],
        token_version=created_user["token_version"]
    )

    return AuthSuccessResponse(
        success=True,
        token=token,
        token_type="bearer",
        user=UserProfileResponse(**created_user),
    )


@router.post(
    "/login",
    response_model=AuthSuccessResponse,
    summary="Authenticate user and obtain JWT token"
)
async def login(
    payload: UserLoginRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Authenticate an existing candidate and issue a signed session JWT."""
    user = db.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        token_version=user.get("token_version", 1)
    )

    return AuthSuccessResponse(
        success=True,
        token=token,
        token_type="bearer",
        user=UserProfileResponse(**user),
    )


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    summary="Log out and invalidate active session token"
)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Invalidate the current session token immediately via both token version increment
    and explicit token blocklist registration.
    """
    token = current_user.get("_current_token")
    if token:
        db.blocklist_token(token)

    db.increment_token_version(current_user["id"])

    return AuthMessageResponse(
        success=True,
        message="Successfully logged out. Session token has been invalidated."
    )


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Retrieve current user profile"
)
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve verified profile information for the authenticated user."""
    return ProfileResponse(
        success=True,
        user=UserProfileResponse(**current_user)
    )


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Update candidate profile information and privacy settings"
)
async def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Update editable profile fields and data retention preferences."""
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        return ProfileResponse(
            success=True,
            user=UserProfileResponse(**current_user)
        )

    updated_user = db.update_user(current_user["id"], updates)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return ProfileResponse(
        success=True,
        user=UserProfileResponse(**updated_user)
    )


@router.delete(
    "/account",
    response_model=AuthMessageResponse,
    summary="Permanently delete user account and associated credentials"
)
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Permanently purge candidate account from database and invalidate active token.
    Fulfills Privacy & Data Deletion rights.
    """
    token = current_user.get("_current_token")
    if token:
        db.blocklist_token(token)

    deleted = db.delete_user(current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account could not be found."
        )

    return AuthMessageResponse(
        success=True,
        message="User account and associated credentials have been permanently deleted."
    )
