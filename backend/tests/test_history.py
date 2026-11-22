"""
Comprehensive Automated Test Suite for Feature #2 & #3:
Persistent User Data, Resume Analysis Storage & Prediction History.
Covers:
1. Saving history for authenticated user (POST /api/history/save)
2. Strict Privacy Enforcement (extracted_text = None when save_resume_text is False)
3. Opt-in Privacy Enforcement (extracted_text saved when save_resume_text is True)
4. Listing history records (GET /api/history) ordered newest first
5. Full detail retrieval (GET /api/history/{id})
6. Cross-user isolation (User B cannot read User A's record -> HTTP 403)
7. Cross-user deletion isolation (User B cannot delete User A's record -> HTTP 403)
8. Individual record deletion (DELETE /api/history/{id})
9. Clear all history records (DELETE /api/history)
10. Cascading purge on user account deletion
11. Unauthenticated request protection (HTTP 401)
"""

import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.core.database import get_db
except ModuleNotFoundError:
    from app.main import app
    from app.core.database import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure a clean database state before each test."""
    db = get_db()
    db.reset_database()
    yield
    db.reset_database()


def register_user(email: str, password: str = "Password123!", save_resume_text: bool = False) -> str:
    """Helper to register and return a valid JWT token."""
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test Candidate",
        "save_resume_text": save_resume_text,
    })
    assert res.status_code == 201
    return res.json()["token"]


SAMPLE_HISTORY_PAYLOAD = {
    "filename": "Jane_Doe_Resume_2026.pdf",
    "skills": {
        "all_skills": ["Python", "React", "PostgreSQL", "Docker", "Git"],
        "programming_languages": ["Python"],
        "frameworks_and_libraries": ["React"],
    },
    "education_summary": "B.S. in Computer Science",
    "experience_years": 2.5,
    "top_prediction": {
        "category": "INFORMATION-TECHNOLOGY",
        "confidence": 0.884,
        "predictions": [
            {"rank": 1, "category": "INFORMATION-TECHNOLOGY", "confidence": 0.884},
            {"rank": 2, "category": "ENGINEERING", "confidence": 0.082},
            {"rank": 3, "category": "DATA-SCIENCE", "confidence": 0.034},
        ],
    },
    "latest_match": {
        "job_title": "Full Stack Software Engineer",
        "semantic_score": 0.852,
        "match_percentage": 71.4,
    },
    "latest_roadmap": {
        "target_role": "Full Stack Software Engineer",
        "duration": "30-day",
    },
    "extracted_text": "Sensitive raw resume content containing confidential work notes and contact info.",
    "full_snapshot": {
        "filename": "Jane_Doe_Resume_2026.pdf",
        "extracted_text": "Sensitive raw resume content containing confidential work notes and contact info.",
        "skills": ["Python", "React"],
    },
}


# ==============================================================================
# Test Scenario 1: Save History Record (Default Privacy: save_resume_text=False)
# ==============================================================================
def test_01_save_history_privacy_enforced():
    """Verify that when save_resume_text=False, extracted_text is stripped and stored as None."""
    token = register_user("privacy_user@example.com", save_resume_text=False)

    save_res = client.post(
        "/api/history/save",
        json=SAMPLE_HISTORY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert save_res.status_code == 200
    data = save_res.json()
    assert data["success"] is True
    record_id = data["record_id"]

    # Retrieve record from DB directly or via GET
    db = get_db()
    stored = db.get_history_record_by_id(record_id)
    assert stored is not None
    assert stored["filename"] == "Jane_Doe_Resume_2026.pdf"
    assert stored["experience_years"] == 2.5
    assert len(stored["skills"]["all_skills"]) == 5

    # PRIVACY VERIFICATION: extracted_text must be None!
    assert stored["extracted_text"] is None
    if stored.get("full_snapshot"):
        assert stored["full_snapshot"].get("extracted_text") is None


# ==============================================================================
# Test Scenario 2: Save History Record (Opt-In Privacy: save_resume_text=True)
# ==============================================================================
def test_02_save_history_opted_in():
    """Verify that when save_resume_text=True, sanitized text is preserved."""
    token = register_user("optin_user@example.com", save_resume_text=True)

    save_res = client.post(
        "/api/history/save",
        json=SAMPLE_HISTORY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert save_res.status_code == 200
    record_id = save_res.json()["record_id"]

    db = get_db()
    stored = db.get_history_record_by_id(record_id)
    assert stored is not None
    assert stored["extracted_text"] == SAMPLE_HISTORY_PAYLOAD["extracted_text"]


# ==============================================================================
# Test Scenario 3: List History Records (Ordered Newest First)
# ==============================================================================
def test_03_list_history_ordered():
    """Verify GET /api/history returns user records with summaries ordered newest-first."""
    token = register_user("history_list@example.com")

    # Save record 1
    p1 = dict(SAMPLE_HISTORY_PAYLOAD, filename="resume_v1.pdf")
    client.post("/api/history/save", json=p1, headers={"Authorization": f"Bearer {token}"})

    # Save record 2
    p2 = dict(SAMPLE_HISTORY_PAYLOAD, filename="resume_v2.pdf")
    client.post("/api/history/save", json=p2, headers={"Authorization": f"Bearer {token}"})

    list_res = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["success"] is True
    assert data["total"] == 2
    assert len(data["records"]) == 2

    # Check summary fields
    first = data["records"][0]
    assert first["filename"] == "resume_v2.pdf"
    assert first["skill_count"] == 5
    assert first["top_role"] == "INFORMATION-TECHNOLOGY"
    assert first["top_confidence"] == 0.884
    assert first["latest_job_title"] == "Full Stack Software Engineer"


# ==============================================================================
# Test Scenario 4: Retrieve Detail Record
# ==============================================================================
def test_04_get_history_detail():
    """Verify GET /api/history/{id} returns the full snapshot for workspace reloading."""
    token = register_user("detail_user@example.com")
    save_res = client.post(
        "/api/history/save",
        json=SAMPLE_HISTORY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"}
    )
    record_id = save_res.json()["record_id"]

    res = client.get(f"/api/history/{record_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    rec = res.json()["record"]
    assert rec["id"] == record_id
    assert rec["filename"] == "Jane_Doe_Resume_2026.pdf"
    assert "skills" in rec
    assert "top_prediction" in rec
    assert "latest_roadmap" in rec


# ==============================================================================
# Test Scenario 5: Cross-User Isolation (Security Check)
# ==============================================================================
def test_05_cross_user_isolation():
    """Verify User B cannot view or delete User A's history record (HTTP 403)."""
    token_a = register_user("user_a@example.com")
    token_b = register_user("user_b@example.com")

    # User A saves record
    save_res = client.post(
        "/api/history/save",
        json=SAMPLE_HISTORY_PAYLOAD,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    record_id = save_res.json()["record_id"]

    # User B attempts to view User A's record
    get_res = client.get(f"/api/history/{record_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_res.status_code == 403
    assert "permission" in get_res.json()["detail"].lower()

    # User B attempts to delete User A's record
    del_res = client.delete(f"/api/history/{record_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_res.status_code == 403
    assert "permission" in del_res.json()["detail"].lower()


# ==============================================================================
# Test Scenario 6: Delete Individual Record
# ==============================================================================
def test_06_delete_individual_record():
    """Verify DELETE /api/history/{id} removes only the target record."""
    token = register_user("delete_test@example.com")

    p1 = dict(SAMPLE_HISTORY_PAYLOAD, filename="doc1.pdf")
    r1 = client.post("/api/history/save", json=p1, headers={"Authorization": f"Bearer {token}"}).json()["record_id"]
    p2 = dict(SAMPLE_HISTORY_PAYLOAD, filename="doc2.pdf")
    r2 = client.post("/api/history/save", json=p2, headers={"Authorization": f"Bearer {token}"}).json()["record_id"]

    # Delete r1
    del_res = client.delete(f"/api/history/{r1}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200

    # r1 should now return 404
    get_r1 = client.get(f"/api/history/{r1}", headers={"Authorization": f"Bearer {token}"})
    assert get_r1.status_code == 404

    # r2 still exists
    get_r2 = client.get(f"/api/history/{r2}", headers={"Authorization": f"Bearer {token}"})
    assert get_r2.status_code == 200


# ==============================================================================
# Test Scenario 7: Clear All History
# ==============================================================================
def test_07_clear_all_history():
    """Verify DELETE /api/history purges all records for the calling user."""
    token = register_user("clear_all@example.com")
    client.post("/api/history/save", json=SAMPLE_HISTORY_PAYLOAD, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/history/save", json=SAMPLE_HISTORY_PAYLOAD, headers={"Authorization": f"Bearer {token}"})

    clear_res = client.delete("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert clear_res.status_code == 200
    assert clear_res.json()["deleted_count"] >= 2

    # Listing should now be empty
    list_res = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 0


# ==============================================================================
# Test Scenario 8: Cascading Purge on User Account Deletion
# ==============================================================================
def test_08_cascading_purge_on_account_deletion():
    """Verify that deleting a user account also purges all of their history records."""
    token = register_user("cascade@example.com")
    save_res = client.post(
        "/api/history/save",
        json=SAMPLE_HISTORY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"}
    )
    record_id = save_res.json()["record_id"]

    # Delete account
    del_acc = client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
    assert del_acc.status_code == 200

    # DB verification: history record must be gone
    db = get_db()
    assert db.get_history_record_by_id(record_id) is None


# ==============================================================================
# Test Scenario 9: Unauthenticated Protection
# ==============================================================================
def test_09_unauthenticated_protection():
    """Verify all history endpoints reject requests without a token."""
    assert client.post("/api/history/save", json=SAMPLE_HISTORY_PAYLOAD).status_code in [401, 403]
    assert client.get("/api/history").status_code in [401, 403]
    assert client.get("/api/history/analytics").status_code in [401, 403]
    assert client.get("/api/history/123").status_code in [401, 403]
    assert client.delete("/api/history/123").status_code in [401, 403]
    assert client.delete("/api/history").status_code in [401, 403]


# ==============================================================================
# Test Scenario 10: History Analytics Aggregation (Feature #6)
# ==============================================================================
def test_10_history_analytics_empty_and_aggregated():
    """Verify GET /api/history/analytics provides real empty-state and aggregated metrics."""
    token = register_user("analytics_user@example.com")

    # 1. Empty State
    res_empty = client.get("/api/history/analytics", headers={"Authorization": f"Bearer {token}"})
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["success"] is True
    assert data_empty["total_analyses"] == 0
    assert data_empty["unique_skills_count"] == 0
    assert data_empty["top_skills"] == []
    assert data_empty["domain_distribution"] == []
    assert data_empty["score_progression"] == []
    assert data_empty["latest_analysis"] is None

    # 2. Add Snapshot 1
    p1 = {
        "filename": "backend_resume.pdf",
        "skills": {
            "all_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        },
        "top_prediction": {
            "category": "INFORMATION-TECHNOLOGY",
            "confidence": 0.88,
        },
        "latest_match": {
            "job_title": "Backend Engineer",
            "semantic_score": 0.82,
            "match_percentage": 75.0,
        },
    }
    client.post("/api/history/save", json=p1, headers={"Authorization": f"Bearer {token}"})

    # 3. Add Snapshot 2
    p2 = {
        "filename": "fullstack_resume.pdf",
        "skills": {
            "all_skills": ["Python", "JavaScript", "React", "Docker"],
        },
        "top_prediction": {
            "category": "INFORMATION-TECHNOLOGY",
            "confidence": 0.91,
        },
        "latest_match": {
            "job_title": "Full Stack Developer",
            "semantic_score": 0.85,
            "match_percentage": 80.0,
        },
    }
    client.post("/api/history/save", json=p2, headers={"Authorization": f"Bearer {token}"})

    # 4. Fetch Analytics
    res_agg = client.get("/api/history/analytics", headers={"Authorization": f"Bearer {token}"})
    assert res_agg.status_code == 200
    data = res_agg.json()

    assert data["success"] is True
    assert data["total_analyses"] == 2
    assert data["unique_skills_count"] == 6  # Python, FastAPI, PostgreSQL, Docker, JavaScript, React
    assert len(data["domain_distribution"]) == 1
    assert data["domain_distribution"][0]["domain"] == "INFORMATION-TECHNOLOGY"
    assert data["domain_distribution"][0]["count"] == 2
    assert data["domain_distribution"][0]["percentage"] == 100.0

    # Skills frequencies
    skill_map = {item["skill"]: item["count"] for item in data["top_skills"]}
    assert skill_map["Python"] == 2
    assert skill_map["Docker"] == 2
    assert skill_map["FastAPI"] == 1

    # Score progression length
    assert len(data["score_progression"]) == 2
    assert data["latest_analysis"]["filename"] == "fullstack_resume.pdf"
