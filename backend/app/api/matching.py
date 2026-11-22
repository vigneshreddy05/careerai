"""
API Router for Semantic Resume–Job Description Matching (Phase 10).
Delivers Sentence-BERT cosine similarity, deterministic skill gap matrix,
and tailored suggestions.
"""

from fastapi import APIRouter, HTTPException, status

try:
    from backend.app.schemas.matching import (
        JobMatchingRequest,
        JobMatchingResponse,
    )
    from backend.app.services.semantic_matching_service import get_semantic_matching_service
except ModuleNotFoundError:
    from app.schemas.matching import (
        JobMatchingRequest,
        JobMatchingResponse,
    )
    from app.services.semantic_matching_service import get_semantic_matching_service

router = APIRouter()


@router.post(
    "/job-description",
    response_model=JobMatchingResponse,
    summary="Match resume against job description",
    description="Compute Sentence-BERT cosine similarity and deterministic skill gap breakdown on CPU.",
)
def match_resume_to_job(request: JobMatchingRequest):
    """
    Execute dual-engine semantic matching between candidate resume text
    and target job description text.
    """
    service = get_semantic_matching_service()

    if not service.is_loaded:
        loaded = service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=service.load_error or "Semantic matching model is currently unavailable.",
            )

    try:
        response = service.match(
            resume_text=request.resume_text,
            job_description=request.job_description,
            job_title=request.job_title,
        )
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(run_err),
        ) from run_err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during semantic matching: {err}",
        ) from err
