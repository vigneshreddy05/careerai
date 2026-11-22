"""
Pydantic Schemas for User Registration, Authentication, and Profile Management.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for creating a new user account."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Secure user password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Candidate full name")
    current_role: Optional[str] = Field(None, max_length=100, description="Current role or student status")
    experience_years: Optional[float] = Field(None, ge=0.0, le=50.0, description="Years of professional experience")
    target_role: Optional[str] = Field(None, max_length=100, description="Desired target career role")
    save_resume_text: bool = Field(False, description="Privacy preference: opt-in to store sanitized resume text")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        # Standard email regex pattern
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Please provide a valid email address.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for authenticating an existing user."""
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserProfileUpdateRequest(BaseModel):
    """Payload for updating user profile attributes and privacy settings."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    current_role: Optional[str] = Field(None, max_length=100)
    experience_years: Optional[float] = Field(None, ge=0.0, le=50.0)
    target_role: Optional[str] = Field(None, max_length=100)
    save_resume_text: Optional[bool] = None


class UserProfileResponse(BaseModel):
    """Public safe representation of a user profile (excludes password hash and token version)."""
    id: str
    email: str
    full_name: str
    current_role: Optional[str] = None
    experience_years: Optional[float] = None
    target_role: Optional[str] = None
    save_resume_text: bool = False
    created_at: str
    updated_at: str


class AuthSuccessResponse(BaseModel):
    """Response returned upon successful registration or login."""
    success: bool = True
    token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class ProfileResponse(BaseModel):
    """Response returned for profile retrieval and update endpoints."""
    success: bool = True
    user: UserProfileResponse


class AuthMessageResponse(BaseModel):
    """Generic status response for logout and account deletion."""
    success: bool = True
    message: str
