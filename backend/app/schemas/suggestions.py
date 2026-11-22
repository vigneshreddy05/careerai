"""
Pydantic Schemas for Feature #4: Resume Improvement Suggestions Engine.
Provides structured, prioritized, actionable suggestions, rewrite templates,
and deterministic structural readiness scoring.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


RESUME_READINESS_DISCLAIMER = (
    "This readiness score represents a deterministic structural completeness and formatting heuristic "
    "evaluating detected resume sections, quantifiable impact metrics, and technical keywords. "
    "It does not calibrate hiring probabilities, candidate qualification guarantees, or interview likelihood."
)


class ActionRewriteExample(BaseModel):
    """Concrete before/after rewrite template demonstrating high-impact phrasing."""
    context: str = Field(..., description="Context of the bullet point, e.g., 'Web Development' or 'Machine Learning'")
    before: str = Field(..., description="Passive or unquantified example bullet")
    after: str = Field(..., description="Action-verb-driven, metric-focused example bullet")
    explanation: str = Field(..., description="Why the rewritten version is more impactful")


class SuggestionItem(BaseModel):
    """A prioritized, actionable suggestion for resume improvement."""
    id: str = Field(..., description="Unique suggestion identifier")
    category: str = Field(
        ...,
        description="Category: Contact & Header, Impact & Action Verbs, Skills & Keyword Organization, Projects & Experience, ATS Readability & Formatting"
    )
    priority: str = Field(..., description="Priority level: High, Medium, or Low")
    title: str = Field(..., description="Short descriptive title of the recommendation")
    issue: str = Field(..., description="Clear explanation of the detected omission or weakness")
    recommendation: str = Field(..., description="Concrete steps the candidate should take to resolve the issue")
    action_type: str = Field("rewrite", description="Action classification: add, rewrite, reorganize, or verify")
    examples: List[ActionRewriteExample] = Field(default_factory=list, description="Concrete rewrite templates if applicable")


class CategoryScore(BaseModel):
    """Structural completeness score for an individual resume category."""
    category: str = Field(..., description="Category label")
    score: int = Field(..., ge=0, description="Points awarded")
    max_score: int = Field(..., ge=1, description="Maximum possible points in category")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Category percentage score")
    status: str = Field(..., description="Status: Complete, Needs Improvement, or Critical Gap")
    summary: str = Field(..., description="Brief assessment of the section")


class ResumeReadinessBreakdown(BaseModel):
    """Overall resume structural completeness score and category breakdown."""
    overall_score: int = Field(..., ge=0, le=100, description="Total completeness score (0-100)")
    readiness_tier: str = Field(
        ...,
        description="Tier: Strong Structural Foundation (85-100), Moderate Completeness (60-84), or Requires Significant Improvement (0-59)"
    )
    disclaimer: str = Field(RESUME_READINESS_DISCLAIMER, description="Mandatory ethical disclaimer")
    category_scores: List[CategoryScore] = Field(default_factory=list)


class SuggestionsRequest(BaseModel):
    """Input payload containing parsed resume data and optional targeting information."""
    filename: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    skills: Optional[Dict[str, Any]] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[Dict[str, Any]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    statistics: Optional[Dict[str, Any]] = None
    extracted_text: Optional[str] = None
    target_role: Optional[str] = None
    custom_missing_skills: Optional[List[str]] = Field(default_factory=list)
    job_description: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """Response payload containing categorized suggestions and structural readiness breakdown."""
    success: bool = True
    readiness_score: ResumeReadinessBreakdown
    suggestions: List[SuggestionItem]
    summary: Dict[str, int] = Field(
        ...,
        description="Counts of suggestions by priority: total, high, medium, low"
    )
    target_role: Optional[str] = None
    analyzed_at: str
