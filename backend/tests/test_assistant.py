"""
Comprehensive Automated Test Suite for Feature #5: AI Career Assistant Chatbot.
Validates local Ollama health status, context grounding, guided advisor fallback,
and input validation without external dependencies.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantContextPayload,
    AssistantStatusResponse,
    ChatMessage,
    ASSISTANT_ETHICAL_DISCLAIMER,
)
from backend.app.services.assistant_service import AssistantService

client = TestClient(app)


def test_01_assistant_status_endpoint():
    """Verify GET /api/assistant/status returns valid health and model schema."""
    res = client.get("/api/assistant/status")
    assert res.status_code == 200
    data = res.json()

    assert "ollama_available" in data
    assert isinstance(data["ollama_available"], bool)
    assert "ollama_base_url" in data
    assert "11434" in data["ollama_base_url"]
    assert "configured_model" in data
    assert "status" in data
    assert data["status"] in ["connected", "offline"]


@pytest.mark.asyncio
async def test_02_guided_advisor_fallback_skills_intent():
    """Verify Guided Career Advisor provides contextual advice on skill gaps."""
    context = AssistantContextPayload(
        detected_skills=["Python", "SQL", "Git"],
        target_role="Backend Software Engineer",
        missing_skills=["FastAPI", "Docker", "Redis"],
        top_predicted_domain="INFORMATION-TECHNOLOGY",
        top_prediction_confidence=0.88,
        roadmap_duration="30-day",
        readiness_score=78,
    )

    reply, followups = AssistantService.generate_guided_response(
        message="What skills should I learn first to bridge my skill gap?",
        context=context,
    )

    assert "Backend Software Engineer" in reply
    assert "FastAPI" in reply
    assert len(followups) == 3
    assert any("project" in f.lower() or "interview" in f.lower() for f in followups)


@pytest.mark.asyncio
async def test_03_guided_advisor_portfolio_intent():
    """Verify Guided Career Advisor suggests production-grade project concepts."""
    context = AssistantContextPayload(
        detected_skills=["React", "JavaScript", "HTML", "CSS"],
        target_role="Frontend Software Engineer",
        missing_skills=["TypeScript", "Next.js", "Tailwind CSS"],
    )

    reply, followups = AssistantService.generate_guided_response(
        message="Suggest a portfolio project idea to impress recruiters",
        context=context,
    )

    assert "Project" in reply
    assert "React" in reply
    assert len(followups) == 3


@pytest.mark.asyncio
async def test_04_guided_advisor_xyz_bullet_intent():
    """Verify Guided Career Advisor explains Google XYZ formula with concrete examples."""
    context = AssistantContextPayload(
        detected_skills=["Python", "FastAPI"],
        target_role="Backend Software Engineer",
    )

    reply, followups = AssistantService.generate_guided_response(
        message="How do I write strong resume bullets using the XYZ formula?",
        context=context,
    )

    assert "XYZ Formula" in reply
    assert "Accomplished [X]" in reply
    assert "Passive (Weak)" in reply or "Weak" in reply
    assert len(followups) == 3


def test_05_chat_api_endpoint_guided_execution():
    """Verify POST /api/assistant/chat delivers immediate grounded response."""
    payload = {
        "message": "Prepare me for interview questions for my target role",
        "conversation_history": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi! How can I help with your career?"},
        ],
        "context": {
            "detected_skills": ["Python", "FastAPI", "PostgreSQL"],
            "target_role": "Backend Software Engineer",
            "missing_skills": ["Docker", "Kubernetes"],
            "top_predicted_domain": "INFORMATION-TECHNOLOGY",
            "top_prediction_confidence": 0.82,
            "roadmap_duration": "30-day",
            "readiness_score": 85,
        },
        "use_local_llm": False,  # Explicitly test instant CPU-guided mode
    }

    res = client.post("/api/assistant/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["engine_used"] == "careerai-guided-advisor"
    assert "Backend Software Engineer" in data["reply"]
    assert len(data["suggested_followups"]) == 3
    assert data["disclaimer"] == ASSISTANT_ETHICAL_DISCLAIMER


def test_06_chat_input_validation():
    """Verify empty prompt is rejected with HTTP 400."""
    res = client.post("/api/assistant/chat", json={"message": "   "})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_07_no_pii_in_system_prompt():
    """Verify that system prompt builder strictly excludes PII."""
    context = AssistantContextPayload(
        detected_skills=["Java", "Spring Boot"],
        target_role="Java Developer",
        missing_skills=["Microservices", "Kafka"],
    )

    prompt = AssistantService._build_grounded_system_prompt(context)

    assert "Java" in prompt
    assert "Microservices" in prompt
    # Ensure no personal PII keys are referenced
    assert "phone" not in prompt.lower()
    assert "email" not in prompt.lower()
    assert "address" not in prompt.lower()
    assert "SSN" not in prompt
