"""
Protected Admin API for Site Owner Resume Submissions & User Review.
Secured with X-Admin-Key header authentication.
"""

from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query, status, Depends

try:
    from backend.app.core.config import settings
    from backend.app.core.database import get_db, DatabaseManager
    from backend.app.schemas.admin import (
        AdminSubmissionsListResponse,
        AdminSubmissionDetailResponse,
        AdminActionResponse,
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.core.database import get_db, DatabaseManager
    from app.schemas.admin import (
        AdminSubmissionsListResponse,
        AdminSubmissionDetailResponse,
        AdminActionResponse,
    )

router = APIRouter()


def verify_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
) -> str:
    """Validate that the request carries the correct administrator access key."""
    if not x_admin_key or x_admin_key.strip() != settings.ADMIN_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin access key.",
        )
    return x_admin_key


@router.get(
    "/submissions",
    response_model=AdminSubmissionsListResponse,
    summary="List all uploaded resumes and registered users",
    description="Retrieve all submitted resumes and registered user summaries for administrative review.",
)
async def get_all_submissions(
    limit: int = Query(200, ge=1, le=1000),
    _: str = Depends(verify_admin_key),
    db: DatabaseManager = Depends(get_db),
):
    submissions = db.list_resume_submissions(limit=limit)
    users = db.list_all_users(limit=limit)

    return {
        "success": True,
        "total_submissions": len(submissions),
        "submissions": submissions,
        "total_users": len(users),
        "users": users,
    }


@router.get(
    "/submissions/{submission_id}",
    response_model=AdminSubmissionDetailResponse,
    summary="Get full details of a specific resume submission",
    description="Retrieve complete resume submission details including full extracted text.",
)
async def get_submission_detail(
    submission_id: str,
    _: str = Depends(verify_admin_key),
    db: DatabaseManager = Depends(get_db),
):
    submission = db.get_resume_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume submission '{submission_id}' not found.",
        )

    return {
        "success": True,
        "submission": submission,
    }


@router.delete(
    "/submissions/{submission_id}",
    response_model=AdminActionResponse,
    summary="Delete a resume submission",
    description="Permanently delete an uploaded resume submission record.",
)
async def delete_submission(
    submission_id: str,
    _: str = Depends(verify_admin_key),
    db: DatabaseManager = Depends(get_db),
):
    deleted = db.delete_resume_submission(submission_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume submission '{submission_id}' not found or already deleted.",
        )

    return {
        "success": True,
        "message": f"Resume submission '{submission_id}' deleted successfully.",
    }
