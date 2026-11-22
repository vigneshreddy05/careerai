"""
Pydantic Schemas for Feature #5: AI Career Assistant Chatbot.
Provides request/response models for local Ollama interaction,
deterministic career advisor fallback, and context-grounded mentorship.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


ASSISTANT_ETHICAL_DISCLAIMER = (
    "CareerAI Assistant guidance is intended for career exploration and skill development planning. "
    "Predictions and recommendations represent mathematical heuristics and language model reasoning, "
    "not calibrated hiring probabilities, candidate competence guarantees, or employment offers."
)


class ChatMessage(BaseModel):
    """A single turn in the conversation."""
    role: str = Field(..., description="Message author role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=4000, description="Message text content")


class AssistantContextPayload(BaseModel):
    """
    Sanitized, PII-scrubbed structured candidate context for grounding assistant replies.
    Never contains raw resume text, contact numbers, email, or physical addresses.
    """
    detected_skills: List[str] = Field(default_factory=list, description="Extracted candidate technical skills")
    top_predicted_domain: Optional[str] = Field(None, description="DistilBERT top predicted career domain")
    top_prediction_confidence: Optional[float] = Field(None, description="Confidence score of top domain prediction")
    target_role: Optional[str] = Field(None, description="Candidate target role or benchmark career role")
    missing_skills: List[str] = Field(default_factory=list, description="Target role or JD skill gap items")
    roadmap_duration: Optional[str] = Field(None, description="Active learning roadmap duration (e.g., '30-day' or '60-day')")
    readiness_score: Optional[int] = Field(None, description="Resume structural readiness score (0-100)")


class AssistantChatRequest(BaseModel):
    """Input payload for communicating with the Career Assistant."""
    message: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation turns for multi-turn conversational context (last 6 messages)"
    )
    context: Optional[AssistantContextPayload] = Field(
        None,
        description="Structured candidate context for grounded advice"
    )
    use_local_llm: bool = Field(
        True,
        description="Whether to attempt local Ollama inference before falling back to guided advisor"
    )


class AssistantChatResponse(BaseModel):
    """Structured response from the Career Assistant."""
    success: bool = True
    reply: str = Field(..., description="Assistant answer formatted in markdown")
    engine_used: str = Field(..., description="Engine used: 'ollama:qwen2.5:3b' or 'careerai-guided-advisor'")
    ollama_available: bool = Field(..., description="Whether local Ollama instance was reachable")
    suggested_followups: List[str] = Field(
        default_factory=list,
        description="3 contextually relevant follow-up questions"
    )
    disclaimer: str = Field(
        ASSISTANT_ETHICAL_DISCLAIMER,
        description="Mandatory ethical guidance disclaimer"
    )


class AssistantStatusResponse(BaseModel):
    """Health and model availability status of the local assistant runtime."""
    ollama_available: bool
    ollama_base_url: str
    configured_model: str
    available_models: List[str] = Field(default_factory=list)
    status: str = Field(..., description="'connected' if local Ollama responds, else 'offline'")
