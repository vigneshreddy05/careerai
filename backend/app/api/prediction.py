"""
Job Role Prediction API Endpoint for CareerAI
Accepts extracted resume text and returns the top-3 predicted job categories
with confidence scores and optional low-confidence warnings.
"""

from fastapi import APIRouter, HTTPException, status

try:
    from backend.app.schemas.prediction import (
        JobPredictionRequest,
        JobPredictionResponse,
    )
    from backend.app.services.job_prediction_service import get_prediction_service
except ModuleNotFoundError:
    from app.schemas.prediction import (
        JobPredictionRequest,
        JobPredictionResponse,
    )
    from app.services.job_prediction_service import get_prediction_service

router = APIRouter()


@router.post(
    "/job-role",
    response_model=JobPredictionResponse,
    summary="Predict job role category from resume text",
    description="Classify extracted resume text into top-3 professional categories using fine-tuned DistilBERT.",
)
def predict_job_role(request: JobPredictionRequest):
    """
    Run sequence classification on extracted resume text using the loaded DistilBERT model.
    Returns the top-3 predicted categories with confidence scores and low-confidence warnings.
    """
    service = get_prediction_service()

    if not service.is_loaded:
        # Attempt just-in-time load if startup load failed or was deferred
        loaded = service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=service.load_error or "Job prediction model is currently unavailable.",
            )

    try:
        response = service.predict(resume_text=request.resume_text)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(run_err),
        ) from run_err
    except Exception as err:
        # Avoid leaking internal system paths or tracebacks
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while computing job-role predictions. Please try again.",
        ) from err
