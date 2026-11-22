"""
API Router for Career Recommendations and Personalized Learning Roadmaps (Phase 11).
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

try:
    from backend.app.schemas.roadmap import (
        CareerRecommendationsRequest,
        CareerRecommendationsResponse,
        RoadmapGenerationRequest,
        RoadmapGenerationResponse,
    )
    from backend.app.services.roadmap_service import get_roadmap_service
except ModuleNotFoundError:
    from app.schemas.roadmap import (
        CareerRecommendationsRequest,
        CareerRecommendationsResponse,
        RoadmapGenerationRequest,
        RoadmapGenerationResponse,
    )
    from app.services.roadmap_service import get_roadmap_service

router = APIRouter()


@router.post(
    "/recommendations",
    response_model=CareerRecommendationsResponse,
    summary="Generate personalized career recommendations",
    description="Analyze candidate skills and DistilBERT predictions to recommend strong matches and alternative career paths.",
)
def get_career_recommendations(request: CareerRecommendationsRequest):
    """Generate explainable career role recommendations based on candidate profile."""
    try:
        service = get_roadmap_service()
        response = service.recommend_career_roles(
            resume_skills=request.resume_skills,
            predicted_categories=request.predicted_categories,
            experience_years=request.experience_years,
        )
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating career recommendations: {exc}",
        ) from exc


@router.post(
    "/generate",
    response_model=RoadmapGenerationResponse,
    summary="Generate personalized 30-day or 60-day learning roadmap",
    description="Synthesize structured weekly milestones with practical deliverables and verified free learning resources.",
)
def generate_roadmap(request: RoadmapGenerationRequest):
    """Generate structured 30-day or 60-day learning roadmap tailored to candidate skill gaps."""
    try:
        service = get_roadmap_service()
        response = service.generate_roadmap(
            target_role=request.target_role,
            resume_skills=request.resume_skills,
            duration=request.duration,
            custom_missing_skills=request.custom_missing_skills,
        )
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating personalized roadmap: {exc}",
        ) from exc


@router.get(
    "/available-roles",
    response_model=List[str],
    summary="Get available benchmark career paths",
    description="Retrieve the canonical list of benchmark career roles supported by CareerAI.",
)
def get_available_roles():
    """Return available benchmark roles."""
    service = get_roadmap_service()
    return service.get_available_roles()
