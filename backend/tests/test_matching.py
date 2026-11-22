"""
Automated Test Suite for Semantic Resume–Job Description Matching (Phase 10).

Covers:
1. Model loading & singleton service availability (all-MiniLM-L6-v2, 384 dimensions, CPU)
2. Successful dual-engine API execution (POST /api/match/job-description)
3. High semantic similarity for aligned domain roles
4. Low semantic similarity for cross-domain unrelated roles
5. Accurate deterministic skill gap matrix (matching, missing, additional, percentage)
6. Multi-chunk handling for long documents without truncation
7. Mathematical score bounds (0.0 <= sim <= 1.0, 0.0 <= skill_pct <= 100.0)
8. Input validation and whitespace rejection (HTTP 422)
9. Service unavailable error handling (HTTP 503)
10. Strict response schema validation against JobMatchingResponse
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.schemas.matching import (
        SkillMatchBreakdown,
        SemanticMatchResult,
        JobMatchingRequest,
        JobMatchingResponse,
        MANDATORY_MATCHING_DISCLAIMER,
    )
    from backend.app.services.semantic_matching_service import (
        get_semantic_matching_service,
        SemanticMatchingService,
    )
except ModuleNotFoundError:
    from app.main import app
    from app.schemas.matching import (
        SkillMatchBreakdown,
        SemanticMatchResult,
        JobMatchingRequest,
        JobMatchingResponse,
        MANDATORY_MATCHING_DISCLAIMER,
    )
    from app.services.semantic_matching_service import (
        get_semantic_matching_service,
        SemanticMatchingService,
    )

client = TestClient(app)

SAMPLE_PYTHON_RESUME = (
    "Senior Python Developer with 5 years of software engineering experience. "
    "Expert in Python, FastAPI, Django, PostgreSQL, and Redis. "
    "Experienced with automated testing with PyTest and deploying on AWS."
)

SAMPLE_PYTHON_JD = (
    "We are seeking a Senior Backend Engineer. Requirements: Strong proficiency in "
    "Python, FastAPI, and PostgreSQL. Hands-on experience with Docker, Kubernetes, "
    "and AWS. Experience with Redis caching is a strong plus."
)

SAMPLE_NURSING_JD = (
    "Seeking an experienced Registered Nurse (RN) for an acute hospital ward. "
    "Requirements: Bachelor of Science in Nursing (BSN), active state RN license, "
    "BLS and ACLS certifications, and 2+ years of inpatient clinical care."
)


@pytest.fixture(scope="module", autouse=True)
def initialize_matching_service():
    """Ensure the singleton SemanticMatchingService is loaded before running tests."""
    service = get_semantic_matching_service()
    if not service.is_loaded:
        success = service.load_model()
        assert success, f"Failed to load all-MiniLM-L6-v2: {service.load_error}"
    return service


# ==============================================================================
# Test Scenario 1: Model Loading & Service State
# ==============================================================================
def test_01_matching_service_loading_and_state():
    """Verify that all-MiniLM-L6-v2 loads offline into CPU memory with 384 dimensions."""
    service = get_semantic_matching_service()
    assert service.is_loaded is True
    assert service.model is not None
    assert service.tokenizer is not None
    assert service.device.type == "cpu"
    assert service.embedding_dimension == 384


# ==============================================================================
# Test Scenario 2: Successful Dual-Engine Matching Endpoint
# ==============================================================================
def test_02_match_endpoint_success():
    """Verify that POST /api/match/job-description returns HTTP 200 and dual-engine data."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_PYTHON_JD,
        "job_title": "Senior Backend Engineer",
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["job_title"] == "Senior Backend Engineer"
    assert "semantic_match" in data
    assert "skill_match" in data
    assert "suggestions" in data
    assert "disclaimer" in data
    assert MANDATORY_MATCHING_DISCLAIMER in data["disclaimer"]


# ==============================================================================
# Test Scenario 3: High Semantic Similarity for Aligned Domain Roles
# ==============================================================================
def test_03_high_semantic_similarity_aligned():
    """Verify that aligned roles (Python Engineer vs Python Job) yield high similarity (>= 0.70)."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_PYTHON_JD,
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    sem = response.json()["semantic_match"]
    assert sem["similarity_score"] >= 0.70
    assert sem["similarity_percentage"] >= 70.0
    assert sem["model"] == "all-MiniLM-L6-v2"
    assert sem["embedding_dimension"] == 384


# ==============================================================================
# Test Scenario 4: Low Semantic Similarity for Cross-Domain Roles
# ==============================================================================
def test_04_low_semantic_similarity_unrelated():
    """Verify that cross-domain roles (Python Engineer vs Nursing Job) yield low similarity (< 0.35)."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_NURSING_JD,
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    sem = response.json()["semantic_match"]
    assert sem["similarity_score"] < 0.35
    assert sem["similarity_level"] == "Low Match"


# ==============================================================================
# Test Scenario 5: Deterministic Skill Gap Matrix Accuracy
# ==============================================================================
def test_05_skill_gap_matrix_accuracy():
    """Verify exact deterministic matching, missing skill identification, and percentage calculation."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_PYTHON_JD,
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    sk = response.json()["skill_match"]
    # Resume has: Python, FastAPI, Django, PostgreSQL, Redis, AWS
    # JD has: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Redis
    # Matching should include: Python, FastAPI, PostgreSQL, Redis, AWS
    assert "Python" in sk["matching_skills"]
    assert "FastAPI" in sk["matching_skills"]
    assert "PostgreSQL" in sk["matching_skills"]
    assert "AWS" in sk["matching_skills"]

    # Missing should include: Docker, Kubernetes
    assert "Docker" in sk["missing_skills"]
    assert "Kubernetes" in sk["missing_skills"]

    # Match percentage = matched / total_jd_skills * 100
    expected_pct = round(sk["matched_count"] / sk["total_jd_skills"] * 100, 1)
    assert sk["match_percentage"] == expected_pct
    assert sk["matched_count"] > 0
    assert sk["total_jd_skills"] > 0


# ==============================================================================
# Test Scenario 6: Multi-Chunk Handling for Long Documents
# ==============================================================================
def test_06_long_document_chunking():
    """Verify that documents exceeding 300 words are segmented into multiple chunks and encoded."""
    long_resume = (SAMPLE_PYTHON_RESUME + "\n") * 10  # ~350 words
    long_jd = (SAMPLE_PYTHON_JD + "\n") * 10          # ~400 words

    payload = {
        "resume_text": long_resume,
        "job_description": long_jd,
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    sem = response.json()["semantic_match"]
    assert sem["chunk_count_resume"] >= 2
    assert sem["chunk_count_job"] >= 2
    assert 0.0 <= sem["similarity_score"] <= 1.0


# ==============================================================================
# Test Scenario 7: Mathematical Score Bounds
# ==============================================================================
def test_07_mathematical_score_bounds():
    """Verify strict mathematical bounds for both engines."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_PYTHON_JD,
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    data = response.json()
    sem_score = data["semantic_match"]["similarity_score"]
    sem_pct = data["semantic_match"]["similarity_percentage"]
    skill_pct = data["skill_match"]["match_percentage"]

    assert 0.0 <= sem_score <= 1.0
    assert 0.0 <= sem_pct <= 100.0
    assert 0.0 <= skill_pct <= 100.0


# ==============================================================================
# Test Scenario 8: Input Validation & Whitespace Rejection (HTTP 422)
# ==============================================================================
def test_08_input_validation():
    """Verify that empty, whitespace-only, and oversized payloads are rejected with HTTP 422."""
    # Empty resume
    r1 = client.post("/api/match/job-description", json={"resume_text": "", "job_description": SAMPLE_PYTHON_JD})
    assert r1.status_code == 422

    # Whitespace resume
    r2 = client.post("/api/match/job-description", json={"resume_text": "   \n\t  ", "job_description": SAMPLE_PYTHON_JD})
    assert r2.status_code == 422

    # Empty JD
    r3 = client.post("/api/match/job-description", json={"resume_text": SAMPLE_PYTHON_RESUME, "job_description": ""})
    assert r3.status_code == 422

    # Whitespace JD
    r4 = client.post("/api/match/job-description", json={"resume_text": SAMPLE_PYTHON_RESUME, "job_description": "   \n  "})
    assert r4.status_code == 422

    # Oversized text (>100k chars)
    oversized = "x" * 100001
    r5 = client.post("/api/match/job-description", json={"resume_text": oversized, "job_description": SAMPLE_PYTHON_JD})
    assert r5.status_code == 422


# ==============================================================================
# Test Scenario 9: Service Unavailable Handling (HTTP 503)
# ==============================================================================
def test_09_service_unavailable_handling():
    """Verify that endpoint returns HTTP 503 when model is unloaded and cannot be loaded."""
    service = get_semantic_matching_service()
    original_loaded = service.is_loaded

    try:
        with patch.object(service, "load_model", return_value=False):
            service.is_loaded = False
            service.load_error = "Sentence-BERT model is currently unavailable."

            payload = {
                "resume_text": SAMPLE_PYTHON_RESUME,
                "job_description": SAMPLE_PYTHON_JD,
            }
            response = client.post("/api/match/job-description", json=payload)
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()
    finally:
        service.is_loaded = original_loaded
        service.load_error = None


# ==============================================================================
# Test Scenario 10: Strict Response Schema Validation
# ==============================================================================
def test_10_response_schema_validation():
    """Verify that the API response strictly validates against Pydantic JobMatchingResponse."""
    payload = {
        "resume_text": SAMPLE_PYTHON_RESUME,
        "job_description": SAMPLE_PYTHON_JD,
        "job_title": "Full Stack Engineer",
    }
    response = client.post("/api/match/job-description", json=payload)
    assert response.status_code == 200

    parsed = JobMatchingResponse(**response.json())
    assert parsed.success is True
    assert parsed.job_title == "Full Stack Engineer"
    assert isinstance(parsed.semantic_match.similarity_score, float)
    assert isinstance(parsed.semantic_match.similarity_percentage, float)
    assert parsed.semantic_match.similarity_level in ["High Match", "Moderate Match", "Low Match"]
    assert isinstance(parsed.skill_match.matching_skills, list)
    assert isinstance(parsed.skill_match.missing_skills, list)
    assert isinstance(parsed.suggestions, list)
    assert len(parsed.suggestions) >= 1
    assert MANDATORY_MATCHING_DISCLAIMER in parsed.disclaimer
