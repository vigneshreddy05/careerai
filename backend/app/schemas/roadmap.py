"""
Pydantic Schemas for Phase 11: Career Recommendations & Personalized Learning Roadmap.
Enforces realistic milestone scoping, verified canonical resources, and ethical guardrails.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


ETHICAL_ROADMAP_DISCLAIMER = (
    "This roadmap focuses on foundational tool proficiency and practical hands-on portfolio "
    "implementation. It does not promise hiring, job placement, or senior-level expertise within "
    "30 or 60 days."
)


class LearningResource(BaseModel):
    """Canonical, verified free learning resource."""
    title: str = Field(..., description="Descriptive title of the resource")
    platform: str = Field(..., description="Provider or hosting platform (e.g., Official Documentation, MDN, freeCodeCamp)")
    resource_type: str = Field(
        ...,
        description="Format type: 'Official Documentation', 'Interactive Tutorial', or 'Open-Access Guide'"
    )
    url: str = Field(..., description="Live, canonical URL to the verified resource")
    is_free: bool = Field(True, description="Strictly verified as 100% free of charge")


class RoadmapMilestone(BaseModel):
    """Weekly structured learning milestone."""
    week: int = Field(..., ge=1, le=8, description="Milestone week number (1 to 4 for 30-day, 1 to 8 for 60-day)")
    title: str = Field(..., description="Clear milestone objective title")
    focus_area: str = Field(..., description="Primary domain or technology focus")
    learning_objectives: List[str] = Field(..., description="Actionable knowledge items to master")
    target_skills: List[str] = Field(..., description="Specific missing skills addressed in this week")
    practical_exercise: str = Field(..., description="Hands-on coding exercise or lab task")
    deliverable: str = Field(..., description="Verifiable output or artifact created by the learner")
    resources: List[LearningResource] = Field(default_factory=list, description="Verified free learning materials")


class PersonalizedRoadmap(BaseModel):
    """Complete personalized learning plan tailored to candidate gaps."""
    role_title: str = Field(..., description="Target career role")
    duration: str = Field(..., description="Plan duration: '30-day' or '60-day'")
    target_level: str = Field(..., description="Realistic achievable level (e.g., 'Foundational Tool Proficiency' or 'Portfolio Implementation')")
    existing_skills_leveraged: List[str] = Field(..., description="Skills candidate already has that apply to this role")
    skills_to_acquire: List[str] = Field(..., description="Target missing skills prioritized across milestones")
    milestones: List[RoadmapMilestone] = Field(..., description="Structured weekly progression")
    capstone_project: str = Field(..., description="End-of-roadmap portfolio project description")
    ethical_disclaimer: str = Field(ETHICAL_ROADMAP_DISCLAIMER, description="Mandatory realistic expectation advisory")


class CareerRoleRecommendation(BaseModel):
    """Individual career path recommendation derived from candidate analysis."""
    role_title: str = Field(..., description="Standardized professional job title")
    category: str = Field(..., description="Broader industry domain (aligned with DistilBERT taxonomy)")
    match_type: str = Field(
        ...,
        description="'Strong Match' (high skill overlap / core domain), 'Alternative Career Path' (lateral expansion), or 'Exploratory Track' (broader foundational learning required)"
    )
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Skill overlap coverage percentage")
    matched_skills: List[str] = Field(..., description="Candidate skills directly applicable to this role")
    missing_skills: List[str] = Field(..., description="Key technical requirements candidate would need to learn")
    transferable_skills: List[str] = Field(
        default_factory=list,
        description="Candidate detected skills that are outside this role's core requirements"
    )
    reasoning: str = Field(..., description="Transparent explanation of why this role is recommended")
    recommended_duration: str = Field(..., description="'30-day' for near-term ramp-up or '60-day' for broader transition")


class CareerRecommendationsRequest(BaseModel):
    """Input payload for generating personalized career recommendations."""
    resume_skills: List[str] = Field(default_factory=list, description="List of technical skills extracted from candidate resume")
    predicted_categories: Optional[List[str]] = Field(None, description="Top predicted categories from DistilBERT")
    experience_years: Optional[float] = Field(None, ge=0.0, le=50.0, description="Estimated years of employment experience")


class CareerRecommendationsResponse(BaseModel):
    """Response containing ranked career paths."""
    success: bool = True
    recommendations: List[CareerRoleRecommendation] = Field(default_factory=list)
    total_analyzed_roles: int = Field(..., ge=1)
    disclaimer: str = Field(ETHICAL_ROADMAP_DISCLAIMER)


class RoadmapGenerationRequest(BaseModel):
    """Input payload for generating a 30-day or 60-day personalized roadmap."""
    target_role: str = Field(..., min_length=2, max_length=150, description="Target career role")
    resume_skills: List[str] = Field(default_factory=list, description="Skills candidate currently possesses")
    duration: str = Field("30-day", description="'30-day' or '60-day'")
    custom_missing_skills: Optional[List[str]] = Field(None, description="Specific skills identified from job matching")

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean not in ["30-day", "60-day", "30", "60"]:
            raise ValueError("Duration must be '30-day' or '60-day'.")
        return "60-day" if "60" in clean else "30-day"


class RoadmapGenerationResponse(BaseModel):
    """Response containing personalized milestones and resources."""
    success: bool = True
    roadmap: PersonalizedRoadmap
