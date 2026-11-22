"""
Pydantic Schemas for Protected Admin Submissions Viewer & Analytics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AdminUserSummary(BaseModel):
    """Sanitized user overview for administrative review."""
    id: str
    email: str
    full_name: str
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    experience_years: Optional[float] = None
    save_resume_text: bool = False
    created_at: str


class AdminSubmissionSummary(BaseModel):
    """Resume submission metadata for administrative cards and tables."""
    id: str
    submitted_at: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    filename: str
    file_type: str
    word_count: int = 0
    contact: Dict[str, Any] = Field(default_factory=dict)
    skills: List[str] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_text: Optional[str] = None


class AdminSubmissionsListResponse(BaseModel):
    """Response containing list of uploaded resumes and registered users."""
    success: bool = True
    total_submissions: int = 0
    submissions: List[AdminSubmissionSummary] = Field(default_factory=list)
    total_users: int = 0
    users: List[AdminUserSummary] = Field(default_factory=list)


class AdminSubmissionDetailResponse(BaseModel):
    """Full detail of a single resume submission including full extracted text."""
    success: bool = True
    submission: AdminSubmissionSummary


class AdminActionResponse(BaseModel):
    """Generic action confirmation response."""
    success: bool = True
    message: str
