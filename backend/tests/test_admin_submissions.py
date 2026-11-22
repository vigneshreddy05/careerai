"""
Automated Test Suite for Protected Admin Resume Submissions & Candidate Directory.
Covers:
1. Rejection of unauthorized access (missing/invalid X-Admin-Key -> HTTP 403).
2. Automatic persistence of guest resume uploads in resume_submissions.
3. Automatic persistence of authenticated candidate uploads linked to user_id and user_email.
4. Administrative retrieval of all uploaded resumes including full extracted text.
5. Registered users directory retrieval (verifying passwords and hashes are omitted).
6. Deletion of individual resume submissions.
"""

import io
import pymupdf
import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.core.config import settings
    from backend.app.core.database import get_db
except ModuleNotFoundError:
    from app.main import app
    from app.core.config import settings
    from app.core.database import get_db

client = TestClient(app)

SAMPLE_RESUME_TEXT = """
Jordan Lee
Email: jordan.lee@example.com
Phone: +1-555-456-7890

Summary:
Experienced Software Engineer specializing in Python, FastAPI, and PostgreSQL.

Skills:
Python, FastAPI, Docker, PostgreSQL, React, Git

Experience:
Senior Software Engineer at TechCorp (2022 - Present)
- Architected RESTful microservices with FastAPI and PostgreSQL.
- Reduced database query latency by 35%.

Education:
B.S. in Computer Science, University of Technology, 2021
"""


def create_in_memory_pdf(text: str) -> bytes:
    """Generate in-memory PDF using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def clean_database():
    """Ensure clean isolated database state for each test run."""
    db = get_db()
    db.reset_database()
    yield
    db.reset_database()


def test_01_unauthorized_admin_requests_rejected():
    """Verify all /api/admin endpoints strictly require valid X-Admin-Key."""
    # Missing header
    res1 = client.get("/api/admin/submissions")
    assert res1.status_code == 403
    assert "admin access key" in res1.json()["detail"].lower()

    # Wrong key
    res2 = client.get("/api/admin/submissions", headers={"X-Admin-Key": "wrong-secret-key"})
    assert res2.status_code == 403

    # Detail endpoint missing key
    res3 = client.get("/api/admin/submissions/dummy-id")
    assert res3.status_code == 403

    # Delete endpoint missing key
    res4 = client.delete("/api/admin/submissions/dummy-id")
    assert res4.status_code == 403


def test_02_guest_resume_upload_stored_in_submissions():
    """Verify that a guest uploading a resume has their submission recorded with user_id=None."""
    pdf_bytes = create_in_memory_pdf(SAMPLE_RESUME_TEXT)
    files = {"file": ("guest_resume.pdf", pdf_bytes, "application/pdf")}

    upload_res = client.post("/api/resume/analyze", files=files)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    assert "Python" in upload_data["skills"]["all_skills"]

    # Verify admin viewer retrieves the record
    admin_headers = {"X-Admin-Key": settings.ADMIN_ACCESS_KEY}
    admin_res = client.get("/api/admin/submissions", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()

    assert data["success"] is True
    assert data["total_submissions"] == 1
    sub = data["submissions"][0]
    assert sub["filename"] == "guest_resume.pdf"
    assert sub["user_id"] is None
    assert sub["user_email"] is None
    assert "Python" in sub["skills"]
    assert "FastAPI" in sub["skills"]
    assert "Jordan Lee" in sub["extracted_text"]


def test_03_authenticated_resume_upload_links_user():
    """Verify that an authenticated user upload records the user's ID and email."""
    # 1. Register candidate user
    reg_res = client.post("/api/auth/register", json={
        "email": "candidate@example.com",
        "password": "SecurePassword2026!",
        "full_name": "Jordan Lee",
        "target_role": "Backend Engineer",
    })
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    token = auth_data["token"]
    user_id = auth_data["user"]["id"]

    # 2. Upload resume with Bearer token
    pdf_bytes = create_in_memory_pdf(SAMPLE_RESUME_TEXT)
    files = {"file": ("jordan_lee_resume.pdf", pdf_bytes, "application/pdf")}
    headers = {"Authorization": f"Bearer {token}"}

    upload_res = client.post("/api/resume/analyze", files=files, headers=headers)
    assert upload_res.status_code == 200

    # 3. Check admin viewer captures linked identity
    admin_headers = {"X-Admin-Key": settings.ADMIN_ACCESS_KEY}
    admin_res = client.get("/api/admin/submissions", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()

    assert data["total_submissions"] == 1
    sub = data["submissions"][0]
    assert sub["filename"] == "jordan_lee_resume.pdf"
    assert sub["user_id"] == user_id
    assert sub["user_email"] == "candidate@example.com"


def test_04_get_submission_detail_and_users_directory():
    """Verify full detail inspection and user listing with passwords omitted."""
    # Register user
    reg_res = client.post("/api/auth/register", json={
        "email": "sarah.connor@example.com",
        "password": "Password2026!",
        "full_name": "Sarah Connor",
        "target_role": "DevOps Engineer",
    })
    assert reg_res.status_code == 201

    # Upload resume
    pdf_bytes = create_in_memory_pdf(SAMPLE_RESUME_TEXT)
    files = {"file": ("sarah_resume.pdf", pdf_bytes, "application/pdf")}
    client.post("/api/resume/analyze", files=files)

    admin_headers = {"X-Admin-Key": settings.ADMIN_ACCESS_KEY}
    admin_res = client.get("/api/admin/submissions", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()

    # Verify user list
    assert data["total_users"] == 1
    user_item = data["users"][0]
    assert user_item["email"] == "sarah.connor@example.com"
    assert user_item["full_name"] == "Sarah Connor"
    assert "hashed_password" not in user_item  # Must not leak password hashes

    # Verify detail endpoint
    sub_id = data["submissions"][0]["id"]
    detail_res = client.get(f"/api/admin/submissions/{sub_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["success"] is True
    assert len(detail_data["submission"]["extracted_text"]) > 50

    # Non-existent ID returns 404
    missing_res = client.get("/api/admin/submissions/non-existent-uuid", headers=admin_headers)
    assert missing_res.status_code == 404


def test_05_delete_submission():
    """Verify deleting a submission removes it from the admin viewer."""
    pdf_bytes = create_in_memory_pdf(SAMPLE_RESUME_TEXT)
    files = {"file": ("to_delete.pdf", pdf_bytes, "application/pdf")}
    client.post("/api/resume/analyze", files=files)

    admin_headers = {"X-Admin-Key": settings.ADMIN_ACCESS_KEY}
    admin_res = client.get("/api/admin/submissions", headers=admin_headers)
    sub_id = admin_res.json()["submissions"][0]["id"]

    # Delete submission
    del_res = client.delete(f"/api/admin/submissions/{sub_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check that it's no longer present
    after_res = client.get("/api/admin/submissions", headers=admin_headers)
    assert after_res.json()["total_submissions"] == 0

    # Second delete returns 404
    del_res2 = client.delete(f"/api/admin/submissions/{sub_id}", headers=admin_headers)
    assert del_res2.status_code == 404
