"""
API Router for Feature #5: AI Career Assistant Chatbot.
Provides endpoints for local Ollama health probing and grounded conversational career mentorship.
"""

from fastapi import APIRouter, HTTPException, status

try:
    from backend.app.schemas.assistant import (
        AssistantChatRequest,
        AssistantChatResponse,
        AssistantStatusResponse,
    )
    from backend.app.services.assistant_service import AssistantService
except ModuleNotFoundError:
    from app.schemas.assistant import (
        AssistantChatRequest,
        AssistantChatResponse,
        AssistantStatusResponse,
    )
    from app.services.assistant_service import AssistantService

router = APIRouter()


@router.get(
    "/status",
    response_model=AssistantStatusResponse,
    summary="Probe local Ollama daemon status",
    description="Checks whether local Ollama (127.0.0.1:11434) is reachable and returns configured model information.",
)
async def get_assistant_status():
    """Probe local Ollama health status and return model metadata."""
    try:
        return await AssistantService.check_ollama_status()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check assistant status: {err}",
        ) from err


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    summary="Send a message to the AI Career Assistant",
    description="Processes user prompt with candidate profile grounding via local Ollama or CPU Guided Advisor.",
)
async def chat_with_assistant(request: AssistantChatRequest):
    """
    Process user query and return grounded career mentorship response.
    Automatically falls back to Guided Career Advisor if Ollama is unreachable.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty.",
        )

    try:
        return await AssistantService.process_chat_message(request)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing assistant query: {err}",
        ) from err
