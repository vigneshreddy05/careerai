"""
API Router for Feature #4: Resume Improvement Suggestions.
Delivers deterministic structural readiness scoring, categorized actionable suggestions,
and concrete before-and-after rewrite templates.
"""

from fastapi import APIRouter, HTTPException, status

try:
    from backend.app.schemas.suggestions import (
        SuggestionsRequest,
        SuggestionsResponse,
    )
    from backend.app.services.suggestions_service import SuggestionsService
except ModuleNotFoundError:
    from app.schemas.suggestions import (
        SuggestionsRequest,
        SuggestionsResponse,
    )
    from app.services.suggestions_service import SuggestionsService

router = APIRouter()


@router.post(
    "/analyze",
    response_model=SuggestionsResponse,
    summary="Generate resume improvement suggestions and structural readiness score",
    description="Analyzes parsed resume structure to produce prioritized actionable recommendations, rewrite templates, and a 0-100 completeness breakdown.",
)
def analyze_resume_suggestions(request: SuggestionsRequest):
    """
    Produce prioritized actionable feedback across:
    1. Contact & Header Completeness
    2. Impact & Action-Verb Bullet Quality
    3. Technical Skills & Keyword Organization
    4. Projects & Experience Presentation
    5. ATS Readability & Formatting
    """
    try:
        response = SuggestionsService.analyze_resume_improvements(request)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating resume suggestions: {err}",
        ) from err
