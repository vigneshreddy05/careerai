"""
Pydantic Schemas for Phase 10: Semantic Resume–Job Description Matching.
Enforces strict validation, decoupled semantic & skill scores, and mandatory disclaimers.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


MANDATORY_MATCHING_DISCLAIMER = (
    "These scores represent mathematical semantic similarity (Sentence-BERT cosine similarity) "
    "and deterministic keyword coverage. They do not represent hiring probabilities, candidate "
    "qualification guarantees, or the likelihood of receiving an interview."
)


class SkillMatchBreakdown(BaseModel):
    """Deterministic skill extraction and overlap matrix."""
    resume_skills: List[str] = Field(..., description="Technical skills extracted from resume")
    job_description_skills: List[str] = Field(..., description="Technical skills extracted from job description")
    matching_skills: List[str] = Field(..., description="Intersection of skills in both resume and JD")
    missing_skills: List[str] = Field(..., description="Skills required in JD but absent from resume")
    additional_skills: List[str] = Field(..., description="Skills in resume not explicitly mentioned in JD")
    matched_count: int = Field(..., ge=0, description="Number of matching skills")
    total_jd_skills: int = Field(..., ge=0, description="Total technical skills identified in JD")
    match_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of required JD skills present in resume"
    )


class SemanticMatchResult(BaseModel):
    """Sentence-BERT dense vector cosine similarity analysis."""
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity between document embeddings (0.0 to 1.0)"
    )
    similarity_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Cosine similarity expressed as a percentage"
    )
    similarity_level: str = Field(
        ...,
        description="Semantic fit categorization: High (>=75%), Moderate (50-74%), Low (<50%)"
    )
    embedding_dimension: int = Field(384, description="Sentence-BERT vector dimensionality")
    model: str = Field("all-MiniLM-L6-v2", description="Embedding model used")
    chunk_count_resume: int = Field(..., ge=1, description="Number of processed resume text chunks")
    chunk_count_job: int = Field(..., ge=1, description="Number of processed job description chunks")


class JobMatchingRequest(BaseModel):
    """Input payload for comparing a resume against a job description."""
    resume_text: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Extracted plain text of candidate resume"
    )
    job_description: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Plain text of target job posting or vacancy"
    )
    job_title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional title or label for the target job role"
    )

    @field_validator("resume_text")
    @classmethod
    def validate_resume_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Resume text cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Job description cannot be empty or whitespace only.")
        return v.strip()


class JobMatchingResponse(BaseModel):
    """Comprehensive response for semantic resume-job matching."""
    success: bool = True
    job_title: Optional[str] = None
    semantic_match: SemanticMatchResult
    skill_match: SkillMatchBreakdown
    suggestions: List[str] = Field(
        default_factory=list,
        description="Tailored recommendations for addressing skill gaps and improving alignment"
    )
    disclaimer: str = Field(
        MANDATORY_MATCHING_DISCLAIMER,
        description="Advisory explaining metric interpretations"
    )
