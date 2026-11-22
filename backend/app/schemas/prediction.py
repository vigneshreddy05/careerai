from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class JobCategoryPrediction(BaseModel):
    """Individual predicted job category with confidence score."""
    rank: int = Field(..., ge=1, le=24, description="Rank order of the prediction (1 to 3)")
    category: str = Field(..., description="Canonical job category name")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax confidence score (mathematical linguistic similarity, NOT hiring probability)"
    )


class JobPredictionRequest(BaseModel):
    """Input payload for job-role prediction."""
    resume_text: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Extracted plain text from the resume"
    )

    @field_validator("resume_text")
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Resume text cannot be empty or whitespace only.")
        return v.strip()


class JobPredictionResponse(BaseModel):
    """Standardized response schema for job-role prediction."""
    success: bool = True
    model: str = "DistilBERT"
    predictions: List[JobCategoryPrediction] = Field(
        ...,
        description="Top 3 predicted categories ranked by confidence"
    )
    warning: Optional[str] = Field(
        None,
        description="Low-confidence warning or diagnostic advisory if top confidence < threshold"
    )
