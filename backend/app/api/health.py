from fastapi import APIRouter

try:
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check endpoint")
def health_check():
    """Return health status and basic application metadata."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
