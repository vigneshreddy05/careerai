"""
Pydantic Schemas for Feature #2, #3, #6, & #7: Persistent User Data, History & Analytics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HistorySaveRequest(BaseModel):
    """Payload to persist or sync current analysis session snapshot."""
    record_id: Optional[str] = Field(None, description="Existing record ID if updating an active session")
    filename: str = Field(..., description="Resume filename")
    skills: Dict[str, Any] = Field(default_factory=dict, description="Extracted skill dictionary and lists")
    education_summary: Optional[str] = Field(None, description="Concise education credential overview")
    experience_years: Optional[float] = Field(None, ge=0.0, le=50.0, description="Estimated total experience in years")
    top_prediction: Optional[Dict[str, Any]] = Field(None, description="Top predicted category, confidence, and ranks")
    latest_match: Optional[Dict[str, Any]] = Field(None, description="Latest Sentence-BERT job description matching result")
    latest_roadmap: Optional[Dict[str, Any]] = Field(None, description="Latest generated progression roadmap summary")
    extracted_text: Optional[str] = Field(None, description="Sanitized extracted resume text (only stored if user opted in)")
    full_snapshot: Optional[Dict[str, Any]] = Field(None, description="Full in-memory application context snapshot for 1-click restore")


class HistoryItemSummary(BaseModel):
    """Summary record representation for history listing cards/tables."""
    id: str
    user_id: str
    filename: str
    created_at: str
    updated_at: str
    skill_count: int = 0
    top_role: Optional[str] = None
    top_confidence: Optional[float] = None
    latest_job_title: Optional[str] = None
    latest_match_score: Optional[float] = None
    target_roadmap_role: Optional[str] = None
    has_extracted_text: bool = False


class HistoryListResponse(BaseModel):
    """Response containing list of past saved resume analyses."""
    success: bool = True
    records: List[HistoryItemSummary] = Field(default_factory=list)
    total: int = 0


class HistoryDetailResponse(BaseModel):
    """Full detail of a saved historical record including workspace snapshot."""
    success: bool = True
    record: Dict[str, Any]


class HistorySaveResponse(BaseModel):
    """Response confirming successful history persistence."""
    success: bool = True
    record_id: str
    message: str = "Analysis record saved successfully."


class HistoryActionResponse(BaseModel):
    """Response returned upon deleting one or all history records."""
    success: bool = True
    message: str
    deleted_count: Optional[int] = None


class SkillFrequencyItem(BaseModel):
    """Technical skill occurrence across candidate history."""
    skill: str
    count: int


class DomainDistributionItem(BaseModel):
    """Frequency and share of top predicted career categories across history."""
    domain: str
    count: int
    percentage: float


class ScoreProgressionItem(BaseModel):
    """Chronological evaluation score point for visualization."""
    record_id: str
    date: str
    filename: str
    top_role: Optional[str] = None
    top_confidence: Optional[float] = None
    semantic_score: Optional[float] = None
    skill_coverage: Optional[float] = None
    readiness_score: Optional[int] = None


class HistoryAnalyticsResponse(BaseModel):
    """Aggregated historical analytics and trends for authenticated user."""
    success: bool = True
    total_analyses: int = 0
    unique_skills_count: int = 0
    top_skills: List[SkillFrequencyItem] = Field(default_factory=list)
    domain_distribution: List[DomainDistributionItem] = Field(default_factory=list)
    score_progression: List[ScoreProgressionItem] = Field(default_factory=list)
    latest_analysis: Optional[HistoryItemSummary] = None
