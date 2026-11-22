from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.core.config import settings
    from backend.app.api.health import router as health_router
    from backend.app.api.auth import router as auth_router
    from backend.app.api.history import router as history_router
    from backend.app.api.resume import router as resume_router
    from backend.app.api.prediction import router as prediction_router
    from backend.app.api.matching import router as matching_router
    from backend.app.api.roadmap import router as roadmap_router
    from backend.app.api.suggestions import router as suggestions_router
    from backend.app.api.assistant import router as assistant_router
    from backend.app.api.admin import router as admin_router
    from backend.app.services.job_prediction_service import get_prediction_service
    from backend.app.services.semantic_matching_service import get_semantic_matching_service
    from backend.app.core.middleware import (
        SecurityHeadersMiddleware,
        RateLimiterMiddleware,
        rate_limiter,
        setup_exception_handlers,
        perform_startup_security_checks,
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.api.health import router as health_router
    from app.api.auth import router as auth_router
    from app.api.history import router as history_router
    from app.api.resume import router as resume_router
    from app.api.prediction import router as prediction_router
    from app.api.matching import router as matching_router
    from app.api.roadmap import router as roadmap_router
    from app.api.suggestions import router as suggestions_router
    from app.api.assistant import router as assistant_router
    from app.api.admin import router as admin_router
    from app.services.job_prediction_service import get_prediction_service
    from app.services.semantic_matching_service import get_semantic_matching_service
    from app.core.middleware import (
        SecurityHeadersMiddleware,
        RateLimiterMiddleware,
        rate_limiter,
        setup_exception_handlers,
        perform_startup_security_checks,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model checkpoints and resources once on application startup."""
    perform_startup_security_checks(settings)

    prediction_service = get_prediction_service()
    prediction_service.load_model()

    matching_service = get_semantic_matching_service()
    matching_service.load_model()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-powered resume analysis, job prediction, and career recommendations.",
    lifespan=lifespan,
)

# Add Security Headers and Rate Limiting Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, limiter=rate_limiter)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register standardized global exception handlers
setup_exception_handlers(app)


@app.get("/", summary="Root endpoint")
def root():
    """Return welcome message, application status, and API documentation link."""
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "status": "online",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
    }


# Register routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication & Profile"])
app.include_router(history_router, prefix="/api/history", tags=["Prediction History"])
app.include_router(resume_router, prefix="/api/resume", tags=["Resume Analysis"])
app.include_router(prediction_router, prefix="/api/predictions", tags=["Job Prediction"])
app.include_router(matching_router, prefix="/api/match", tags=["Semantic Matching"])
app.include_router(roadmap_router, prefix="/api/roadmap", tags=["Career Roadmap & Recommendations"])
app.include_router(suggestions_router, prefix="/api/suggestions", tags=["Resume Improvement Suggestions"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["AI Career Assistant"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin Submissions Viewer"])
