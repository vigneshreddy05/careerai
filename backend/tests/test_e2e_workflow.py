"""
Feature #10: Full Application End-to-End Integration Test Suite.
Simulates a complete real candidate lifecycle across all CareerAI modules in sequence:
1. Registration & Authentication (JWT + bcrypt + privacy preference)
2. Resume Parsing & Text Extraction (in-memory PyMuPDF)
3. Resume Improvement Suggestions & Structural Readiness Scoring
4. Job Role Categorization via fine-tuned DistilBERT
5. Semantic Job Matching & Skill Gap Matrix via Sentence-BERT
6. Career Role Recommendations with overlap metrics
7. Personalized 30-Day and 60-Day Learning Roadmap Generation
8. Conversational AI Career Assistant (grounded in candidate profile)
9. History Persistence, Privacy Enforcement, Dashboard Analytics, and Workspace Restoration
10. Account Deletion with cascading purge and token revocation
"""

import io
import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.core.middleware import rate_limiter

client = TestClient(app)


def create_test_pdf(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for upload testing."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


RESUME_CONTENT = """
Alex Morgan
Email: alex.morgan@example.com
Phone: +1 (555) 019-2834
LinkedIn: https://linkedin.com/in/alexmorgan
GitHub: https://github.com/alexmorgan

Professional Summary:
Full Stack Software Engineer with 4 years of experience building scalable backend APIs and reactive frontends.

Technical Skills:
Programming Languages: Python, TypeScript, JavaScript, SQL
Frameworks & Libraries: FastAPI, React, Next.js, Django
Databases: PostgreSQL, Redis, MongoDB
Cloud & DevOps: Docker, Kubernetes, AWS, CI/CD, Git

Education:
Bachelor of Technology in Computer Science
Stanford University (2018 - 2022) | CGPA: 3.8 / 4.0

Work Experience:
Software Engineer at CloudTech Systems (Jan 2022 - Present)
- Architected 14 asynchronous RESTful endpoints in FastAPI with PostgreSQL, cutting average query latency by 35% under 500 concurrent requests.
- Engineered reusable React and TypeScript components, improving user engagement by 28%.

Personal Projects:
Distributed Task Processing Pipeline
- Implemented an asynchronous job queue using Python, Redis, and Docker with automated PyTest coverage.
"""

TARGET_JOB_DESCRIPTION = """
Senior Backend Software Engineer
Requirements:
We are looking for a Backend Engineer with strong Python and FastAPI experience.
Must have hands-on expertise in PostgreSQL, Redis caching, Docker containerization, and AWS deployment.
Knowledge of Kafka, Kubernetes, and CI/CD pipelines is a strong plus.
"""


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure clean database and rate limiter state before and after test execution."""
    rate_limiter.reset()
    db = get_db()
    db.reset_database()
    yield
    rate_limiter.reset()
    db.reset_database()


def test_complete_candidate_lifecycle_e2e():
    """
    Execute the entire CareerAI lifecycle end-to-end through public HTTP APIs.
    Validates complete data flow across authentication, parsing, prediction,
    semantic matching, roadmaps, assistant, history analytics, and privacy guarantees.
    """
    # -------------------------------------------------------------------------
    # Step 1: User Registration with Privacy Mode (save_resume_text=False)
    # -------------------------------------------------------------------------
    reg_payload = {
        "email": "alex.morgan@example.com",
        "password": "SecurePassword2026!",
        "full_name": "Alex Morgan",
        "save_resume_text": False,  # Strict privacy mode
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    auth_data = reg_res.json()
    token = auth_data["token"]
    assert token is not None
    assert auth_data["user"]["email"] == "alex.morgan@example.com"
    assert auth_data["user"]["save_resume_text"] is False

    auth_headers = {
        "Authorization": f"Bearer {token}",
        "x-bypass-rate-limit": "true",
    }

    # -------------------------------------------------------------------------
    # Step 2: Login and Profile Verification
    # -------------------------------------------------------------------------
    login_res = client.post("/api/auth/login", json={
        "email": "alex.morgan@example.com",
        "password": "SecurePassword2026!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["token"] is not None

    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["full_name"] == "Alex Morgan"

    # -------------------------------------------------------------------------
    # Step 3: Resume In-Memory Upload & Parsing (PyMuPDF)
    # -------------------------------------------------------------------------
    pdf_bytes = create_test_pdf(RESUME_CONTENT)
    files = {"file": ("alex_morgan_resume.pdf", pdf_bytes, "application/pdf")}

    parse_res = client.post("/api/resume/analyze", files=files, headers=auth_headers)
    assert parse_res.status_code == 200, f"Parse failed: {parse_res.text}"
    parsed_data = parse_res.json()

    assert parsed_data["success"] is True
    assert parsed_data["filename"] == "alex_morgan_resume.pdf"
    assert parsed_data["file_type"] == "PDF"
    assert parsed_data["contact_info"]["email"] == "alex.morgan@example.com"
    assert "Python" in parsed_data["skills"]["all_skills"]
    assert "FastAPI" in parsed_data["skills"]["all_skills"]
    assert parsed_data["statistics"]["skill_count"] >= 5
    extracted_text = parsed_data["extracted_text"]
    assert len(extracted_text) > 100

    # -------------------------------------------------------------------------
    # Step 4: Resume Improvement Suggestions & Structural Readiness Score
    # -------------------------------------------------------------------------
    sugg_payload = {
        "filename": parsed_data["filename"],
        "contact_info": parsed_data["contact_info"],
        "skills": parsed_data["skills"],
        "education": parsed_data["education"],
        "experience": parsed_data["experience"],
        "projects": parsed_data["projects"],
        "statistics": parsed_data["statistics"],
        "extracted_text": extracted_text,
        "target_role": "Backend Software Engineer",
    }
    sugg_res = client.post("/api/suggestions/analyze", json=sugg_payload, headers=auth_headers)
    assert sugg_res.status_code == 200
    sugg_data = sugg_res.json()

    assert sugg_data["success"] is True
    assert 0 <= sugg_data["readiness_score"]["overall_score"] <= 100
    assert len(sugg_data["readiness_score"]["category_scores"]) == 5
    assert len(sugg_data["suggestions"]) > 0

    # -------------------------------------------------------------------------
    # Step 5: DistilBERT 24-Class Job Role Prediction
    # -------------------------------------------------------------------------
    pred_res = client.post("/api/predictions/job-role", json={"resume_text": extracted_text}, headers=auth_headers)
    assert pred_res.status_code == 200
    pred_data = pred_res.json()

    assert pred_data["success"] is True
    assert pred_data["model"] == "DistilBERT"
    assert len(pred_data["predictions"]) == 3
    top_pred = pred_data["predictions"][0]
    assert "category" in top_pred
    assert 0.0 <= top_pred["confidence"] <= 1.0

    # -------------------------------------------------------------------------
    # Step 6: Sentence-BERT Semantic Matching against Job Description
    # -------------------------------------------------------------------------
    match_payload = {
        "resume_text": extracted_text,
        "job_description": TARGET_JOB_DESCRIPTION,
        "job_title": "Senior Backend Software Engineer",
    }
    match_res = client.post("/api/match/job-description", json=match_payload, headers=auth_headers)
    assert match_res.status_code == 200
    match_data = match_res.json()

    assert match_data["success"] is True
    assert 0.0 <= match_data["semantic_match"]["similarity_score"] <= 1.0
    assert match_data["semantic_match"]["model"] == "all-MiniLM-L6-v2"
    assert "Python" in match_data["skill_match"]["matching_skills"] or "FastAPI" in match_data["skill_match"]["matching_skills"]
    assert match_data["skill_match"]["match_percentage"] > 0

    # -------------------------------------------------------------------------
    # Step 7: Explainable Career Role Recommendations
    # -------------------------------------------------------------------------
    recs_payload = {
        "resume_skills": parsed_data["skills"]["all_skills"],
        "predicted_categories": [top_pred["category"]],
        "experience_years": 4.0,
    }
    recs_res = client.post("/api/roadmap/recommendations", json=recs_payload, headers=auth_headers)
    assert recs_res.status_code == 200
    recs_data = recs_res.json()

    assert recs_data["success"] is True
    assert len(recs_data["recommendations"]) > 0
    top_role_rec = recs_data["recommendations"][0]
    target_role = top_role_rec["role_title"]

    # -------------------------------------------------------------------------
    # Step 8: Personalized 30-Day and 60-Day Roadmap Generation
    # -------------------------------------------------------------------------
    for duration in ["30-day", "60-day"]:
        roadmap_payload = {
            "target_role": target_role,
            "resume_skills": parsed_data["skills"]["all_skills"],
            "duration": duration,
            "custom_missing_skills": match_data["skill_match"]["missing_skills"],
        }
        roadmap_res = client.post("/api/roadmap/generate", json=roadmap_payload, headers=auth_headers)
        assert roadmap_res.status_code == 200
        roadmap_data = roadmap_res.json()
        assert roadmap_data["success"] is True
        roadmap = roadmap_data["roadmap"]
        expected_milestones = 4 if duration == "30-day" else 8
        assert len(roadmap["milestones"]) == expected_milestones
        all_milestone_resources = [res for m in roadmap["milestones"] for res in m["resources"]]
        assert len(all_milestone_resources) > 0

    # -------------------------------------------------------------------------
    # Step 9: Conversational AI Career Assistant Query
    # -------------------------------------------------------------------------
    assistant_payload = {
        "message": f"What projects should I build to master {target_role}?",
        "conversation_history": [],
        "context": {
            "detected_skills": parsed_data["skills"]["all_skills"],
            "target_role": target_role,
            "missing_skills": match_data["skill_match"]["missing_skills"],
            "top_predicted_domain": top_pred["category"],
            "top_prediction_confidence": top_pred["confidence"],
            "roadmap_duration": "30-day",
            "readiness_score": sugg_data["readiness_score"]["overall_score"],
        },
        "use_local_llm": False,  # Instant CPU Guided Advisor
    }
    chat_res = client.post("/api/assistant/chat", json=assistant_payload, headers=auth_headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["success"] is True
    assert len(chat_data["reply"]) > 50
    assert len(chat_data["suggested_followups"]) == 3

    # -------------------------------------------------------------------------
    # Step 10: Persistent History Snapshot & Privacy Validation
    # -------------------------------------------------------------------------
    history_save_payload = {
        "filename": parsed_data["filename"],
        "skills": parsed_data["skills"],
        "education_summary": parsed_data["education"][0]["degree"] if parsed_data["education"] else None,
        "experience_years": 4.0,
        "top_prediction": pred_data,
        "latest_match": match_data,
        "latest_roadmap": roadmap_data,
        "extracted_text": extracted_text,  # Supplied, but should be discarded because save_resume_text=False
        "full_snapshot": {
            "analysisData": parsed_data,
            "predictionData": pred_data,
            "matchingData": match_data,
            "suggestionsData": sugg_data,
        },
    }
    save_hist_res = client.post("/api/history/save", json=history_save_payload, headers=auth_headers)
    assert save_hist_res.status_code == 200
    record_id = save_hist_res.json()["record_id"]

    # Retrieve Detail and Verify Strict Privacy: extracted_text MUST be None
    detail_res = client.get(f"/api/history/{record_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    saved_record = detail_res.json()["record"]
    assert saved_record["filename"] == "alex_morgan_resume.pdf"
    assert saved_record["extracted_text"] is None, "Privacy violation: extracted_text was stored despite save_resume_text=False"
    assert saved_record["full_snapshot"]["analysisData"]["extracted_text"] is None

    # Check History List
    list_res = client.get("/api/history", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # Check Dashboard Analytics Endpoint
    analytics_res = client.get("/api/history/analytics", headers=auth_headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_analyses"] == 1
    assert analytics_data["unique_skills_count"] >= 5
    assert len(analytics_data["score_progression"]) == 1

    # -------------------------------------------------------------------------
    # Step 11: Cascading User Deletion & Immediate Token Revocation
    # -------------------------------------------------------------------------
    del_res = client.delete("/api/auth/account", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Token must now be rejected (token blocklist / deleted user)
    rejected_res = client.get("/api/auth/me", headers=auth_headers)
    assert rejected_res.status_code == 401

    # History record must be permanently purged
    db = get_db()
    assert db.get_history_record_by_id(record_id) is None
