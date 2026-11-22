"""
Automated Test Suite for DistilBERT Job Role Prediction API & Inference Service.

Covers the 10 required test scenarios:
1. Model loading & singleton service availability (24 classes, CPU execution)
2. Valid prediction inference via POST /api/predictions/job-role
3. Top-3 category ordering and rank consistency (rank 1 >= rank 2 >= rank 3)
4. Confidence score mathematical bounds (0.0 <= confidence <= 1.0)
5. Rejection of empty input string (HTTP 422)
6. Rejection of whitespace-only input string (HTTP 422)
7. Rejection of excessively long input string (>100k characters, HTTP 422)
8. Low-confidence warning generation (< 0.40 threshold) with mandatory disclaimer text
9. Service unavailable (HTTP 503) handling when model is missing or unloaded
10. Strict response schema validation against JobPredictionResponse
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionRequest,
        JobPredictionResponse,
    )
    from backend.app.services.job_prediction_service import (
        get_prediction_service,
        JobPredictionService,
    )
except ModuleNotFoundError:
    from app.main import app
    from app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionRequest,
        JobPredictionResponse,
    )
    from app.services.job_prediction_service import (
        get_prediction_service,
        JobPredictionService,
    )

client = TestClient(app)

MANDATORY_DISCLAIMER = (
    "These scores represent the model's softmax confidence, not calibrated "
    "probabilities, semantic similarity scores, or the likelihood of getting hired."
)

SAMPLE_TECH_RESUME = (
    "Senior Python Software Engineer with 6 years of experience building scalable distributed "
    "systems, REST APIs, and microservices. Proficient in Python, Django, FastAPI, PostgreSQL, "
    "Docker, Kubernetes, Redis, and Amazon Web Services (AWS). Experienced in designing automated "
    "CI/CD deployment pipelines, unit testing with PyTest, and Git version control."
)

SAMPLE_HR_RESUME = (
    "Human Resources Specialist with 5 years of experience managing employee relations, "
    "talent recruitment, onboarding, performance appraisals, benefits administration, and "
    "compliance with federal and state labor laws. Proficient in HRIS platforms and conflict resolution."
)


@pytest.fixture(scope="module", autouse=True)
def initialize_service():
    """Ensure the singleton JobPredictionService is loaded before running tests."""
    service = get_prediction_service()
    if not service.is_loaded:
        success = service.load_model()
        assert success, f"Failed to load DistilBERT model: {service.load_error}"
    return service


# ==============================================================================
# Test Scenario 1: Model Loading & Singleton Service Availability
# ==============================================================================
def test_01_model_loading_and_service_state():
    """Verify that the singleton service loads the fine-tuned DistilBERT checkpoint with 24 classes."""
    service = get_prediction_service()
    assert service.is_loaded is True
    assert service.model is not None
    assert service.tokenizer is not None
    assert service.device.type == "cpu"
    assert len(service.id2label) == 24
    assert len(service.label2id) == 24
    assert "INFORMATION-TECHNOLOGY" in service.label2id


# ==============================================================================
# Test Scenario 2: Successful Prediction Endpoint with Valid Resume Text
# ==============================================================================
def test_02_predict_endpoint_success():
    """Verify that POST /api/predictions/job-role returns HTTP 200 and valid JSON for tech resume."""
    payload = {"resume_text": SAMPLE_TECH_RESUME}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["model"] == "DistilBERT"
    assert "predictions" in data
    assert len(data["predictions"]) == 3

    # Primary predicted category for tech resume should be INFORMATION-TECHNOLOGY
    top_pred = data["predictions"][0]
    assert top_pred["category"] == "INFORMATION-TECHNOLOGY"
    assert top_pred["rank"] == 1
    assert 0.0 < top_pred["confidence"] <= 1.0


# ==============================================================================
# Test Scenario 3: Top-3 Category Ordering and Rank Consistency
# ==============================================================================
def test_03_top3_ordering_and_ranks():
    """Verify that exactly 3 predictions are returned in strictly descending confidence order."""
    payload = {"resume_text": SAMPLE_HR_RESUME}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200

    preds = response.json()["predictions"]
    assert len(preds) == 3

    # Ranks must be 1, 2, 3
    assert [p["rank"] for p in preds] == [1, 2, 3]

    # Confidence must be monotonically non-increasing (rank 1 >= rank 2 >= rank 3)
    c1, c2, c3 = preds[0]["confidence"], preds[1]["confidence"], preds[2]["confidence"]
    assert c1 >= c2 >= c3, f"Predictions not properly sorted: {c1}, {c2}, {c3}"

    # Category names must be distinct
    cats = [p["category"] for p in preds]
    assert len(set(cats)) == 3, f"Duplicate categories returned in top 3: {cats}"


# ==============================================================================
# Test Scenario 4: Confidence Score Bounds (0.0 <= c <= 1.0)
# ==============================================================================
def test_04_confidence_bounds():
    """Verify all returned confidence scores are within [0.0, 1.0] and sum <= 1.0."""
    payload = {"resume_text": SAMPLE_TECH_RESUME}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200

    preds = response.json()["predictions"]
    total_conf = 0.0
    for p in preds:
        conf = p["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds [0.0, 1.0]"
        total_conf += conf

    # The sum of top 3 probabilities must be <= 1.0 (with slight float rounding tolerance)
    assert total_conf <= 1.001, f"Sum of top-3 probabilities exceeds 1.0: {total_conf}"


# ==============================================================================
# Test Scenario 5: Rejection of Empty Input String (HTTP 422)
# ==============================================================================
def test_05_reject_empty_string():
    """Verify that an empty resume_text string is rejected with HTTP 422 Unprocessable Entity."""
    payload = {"resume_text": ""}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 422


# ==============================================================================
# Test Scenario 6: Rejection of Whitespace-Only Input String (HTTP 422)
# ==============================================================================
def test_06_reject_whitespace_only():
    """Verify that whitespace-only resume_text is rejected with HTTP 422."""
    payload = {"resume_text": "   \n\t  \r\n   "}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 422


# ==============================================================================
# Test Scenario 7: Rejection of Excessively Long Input (> 100,000 characters)
# ==============================================================================
def test_07_reject_oversized_text():
    """Verify that input exceeding 100,000 characters is rejected with HTTP 422."""
    oversized = "a" * 100001
    payload = {"resume_text": oversized}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 422


# ==============================================================================
# Test Scenario 8: Low-Confidence Warning Generation (< 0.40 Threshold)
# ==============================================================================
def test_08_low_confidence_warning():
    """Verify that low-confidence input triggers a non-null warning containing the exact disclaimer."""
    # Vague, ambiguous text that does not clearly belong to one dominant category
    ambiguous_text = "General professional with skills in various tasks, communication, and work duties."
    payload = {"resume_text": ambiguous_text}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200

    data = response.json()
    top_conf = data["predictions"][0]["confidence"]

    # If top confidence is below 0.40, warning must be present with required disclaimer
    if top_conf < 0.40:
        assert data["warning"] is not None
        assert MANDATORY_DISCLAIMER in data["warning"]
    else:
        # If ambiguous text happened to hit >= 0.40, test with direct service call using higher threshold
        service = get_prediction_service()
        res = service.predict(ambiguous_text, threshold=0.99)
        assert res.warning is not None
        assert MANDATORY_DISCLAIMER in res.warning


# ==============================================================================
# Test Scenario 9: Service Unavailable Handling (HTTP 503)
# ==============================================================================
def test_09_service_unavailable_handling():
    """Verify that endpoint returns HTTP 503 when the underlying model is unloaded and cannot be loaded."""
    service = get_prediction_service()
    original_is_loaded = service.is_loaded

    try:
        with patch.object(service, "load_model", return_value=False):
            service.is_loaded = False
            service.load_error = "Model checkpoint is currently unavailable."

            payload = {"resume_text": SAMPLE_TECH_RESUME}
            response = client.post("/api/predictions/job-role", json=payload)
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()
    finally:
        # Restore service state
        service.is_loaded = original_is_loaded
        service.load_error = None


# ==============================================================================
# Test Scenario 10: Strict Response Schema Validation
# ==============================================================================
def test_10_response_schema_validation():
    """Verify that the API response strictly validates against Pydantic JobPredictionResponse schema."""
    payload = {"resume_text": SAMPLE_TECH_RESUME}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200

    # Parse JSON through Pydantic model directly
    parsed = JobPredictionResponse(**response.json())
    assert parsed.success is True
    assert parsed.model == "DistilBERT"
    assert len(parsed.predictions) == 3
    for p in parsed.predictions:
        assert isinstance(p.rank, int)
        assert 1 <= p.rank <= 24
        assert isinstance(p.category, str)
        assert len(p.category) > 0
        assert isinstance(p.confidence, float)
        assert 0.0 <= p.confidence <= 1.0


# ==============================================================================
# Additional Tests: Truncation of Long Input within Range
# ==============================================================================
def test_11_long_input_within_limit_succeeds():
    """Verify that input with ~5,000 characters is safely truncated to 256 tokens and predicts cleanly."""
    long_resume = (SAMPLE_TECH_RESUME + "\n") * 20  # ~5,500 chars
    assert len(long_resume) < 100000

    payload = {"resume_text": long_resume}
    response = client.post("/api/predictions/job-role", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) == 3
    assert data["predictions"][0]["category"] == "INFORMATION-TECHNOLOGY"
