import io
import docx
import pymupdf
import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
except ModuleNotFoundError:
    from app.main import app

client = TestClient(app)


def create_in_memory_pdf(text: str) -> bytes:
    """Generate in-memory PDF using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_in_memory_docx(text: str) -> bytes:
    """Generate in-memory DOCX using python-docx."""
    doc = docx.Document()
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


SAMPLE_RESUME_TEXT = """
Alex Morgan
Email: alex.morgan@example.com
Phone: +1-555-234-5678
Location: San Francisco, CA

Professional Summary:
Full Stack Developer with 4 years of experience building scalable web applications.

Technical Skills:
Programming Languages: Python, TypeScript, JavaScript, SQL
Frameworks & Libraries: React, Node.js, FastAPI, Django
Databases: PostgreSQL, Redis, MongoDB
Cloud & DevOps: Docker, Kubernetes, AWS, Git, CI/CD

Education:
Bachelor of Technology in Computer Science
Stanford University, 2018 - 2022

Work Experience:
Software Engineer at Acme Corp (Jan 2022 - Present)
Developed distributed FastAPI microservices and React dashboards with PostgreSQL and Docker.

Junior Software Developer at Beta Labs (Jun 2020 - Dec 2021)
Implemented frontend modules with TypeScript, Redux, and Tailwind CSS.
"""


def test_valid_pdf_extraction():
    """Verify successful parsing of a valid PDF resume."""
    pdf_bytes = create_in_memory_pdf(SAMPLE_RESUME_TEXT)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("alex_morgan_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["file_type"] == "PDF"
    assert data["filename"] == "alex_morgan_resume.pdf"

    # Contact info
    assert data["contact_info"]["email"] == "alex.morgan@example.com"
    assert "555-234-5678" in data["contact_info"]["phone"]

    # Technical skills
    skills = data["skills"]["all_skills"]
    assert "Python" in skills
    assert "React" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills

    # Education
    assert len(data["education"]) >= 1
    assert any("Bachelor of Technology" in edu["degree"] for edu in data["education"])

    # Experience
    assert len(data["experience"]["entries"]) >= 1
    assert data["experience"]["total_years_estimated"] == 4.0

    # Statistics
    assert data["statistics"]["word_count"] > 30
    assert data["statistics"]["skill_count"] >= 5


def test_valid_docx_extraction():
    """Verify successful parsing of a valid DOCX resume."""
    docx_bytes = create_in_memory_docx(SAMPLE_RESUME_TEXT)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("alex_morgan_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["file_type"] == "DOCX"
    assert "Python" in data["skills"]["all_skills"]
    assert data["contact_info"]["email"] == "alex.morgan@example.com"


def test_invalid_file_extension():
    """Verify rejection of unsupported file extension (.txt)."""
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("resume.txt", b"Plain text resume content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_invalid_signature():
    """Verify rejection of file with .pdf extension but invalid magic bytes."""
    fake_pdf = b"This is plain text with no PDF magic signature."
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("fake_resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert "Invalid PDF file" in response.json()["detail"]


def test_empty_file():
    """Verify rejection of an empty file (0 bytes)."""
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("empty_resume.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_file_exceeding_upload_limit():
    """Verify rejection of file exceeding 5 MB limit."""
    oversized_content = b"%PDF-1.4\n" + (b"0" * (5 * 1024 * 1024 + 1000))
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("large_resume.pdf", oversized_content, "application/pdf")},
    )
    assert response.status_code == 400
    assert "exceeds maximum allowed size" in response.json()["detail"].lower()


def test_resume_missing_contact_info():
    """Verify graceful handling when no email or phone is present."""
    text_without_contact = """
    Software Engineer with expertise in Python, PyTorch, and Docker.
    Education:
    Master of Science in Data Science, Stanford University
    Experience:
    Data Scientist at AI Corp (2021 - Present)
    """
    pdf_bytes = create_in_memory_pdf(text_without_contact)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("no_contact.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["contact_info"]["email"] is None
    assert data["contact_info"]["phone"] is None
    assert "Python" in data["skills"]["all_skills"]
    assert "PyTorch" in data["skills"]["all_skills"]


def test_corrupted_document():
    """Verify rejection of corrupted document starting with valid signature but broken content."""
    corrupted_pdf = b"%PDF-1.4\n%%corrupted_garbage_stream_not_a_valid_pdf_structure%%"
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("corrupted.pdf", corrupted_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "parse" in response.json()["detail"].lower()


# =====================================================================
# NEW ACCURACY ENHANCEMENT TESTS
# =====================================================================

def test_c_programming_detection():
    """Verify accurate detection of 'C' programming language without false positives."""
    resume_with_c = """
    Technical Skills:
    Programming Languages: C, C++, Python, Java
    Developer Tools: Git, Linux

    Experience:
    Software Developer at Embedded Systems Inc.
    Worked on C programming and low-level kernel drivers.
    """
    pdf_bytes = create_in_memory_pdf(resume_with_c)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("c_skills.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "C" in data["skills"]["programming_languages"]
    assert "C++" in data["skills"]["programming_languages"]
    assert "Python" in data["skills"]["programming_languages"]

    # Verify no false positive from unrelated text
    text_without_c_lang = """
    Location: Section C, Block 4
    Academic Grade: Category C
    Doctor: Dr. John C. Smith
    Skills: Python, React
    """
    pdf_bytes2 = create_in_memory_pdf(text_without_c_lang)
    response2 = client.post(
        "/api/resume/analyze",
        files={"file": ("no_c_lang.pdf", pdf_bytes2, "application/pdf")},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert "C" not in data2["skills"]["programming_languages"]


def test_visual_studio_code_detection():
    """Verify detection and canonicalization of Visual Studio Code / VS Code."""
    resume_with_vscode = """
    Skills:
    Languages: JavaScript, TypeScript
    Tools: Visual Studio Code, Postman, Git, Jira
    """
    pdf_bytes = create_in_memory_pdf(resume_with_vscode)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("vscode_test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Visual Studio Code" in data["skills"]["cloud_and_devops"]
    assert "Postman" in data["skills"]["cloud_and_devops"]


def test_10th_and_12th_education_levels():
    """Verify detection of B.Tech, 12th/Intermediate, and 10th/SSC qualifications."""
    education_resume = """
    Education Details:
    1. Bachelor of Technology in Computer Science
       National Institute of Technology, 2020 - 2024 | CGPA: 8.8

    2. Class XII / Intermediate (MPC)
       Sri Chaitanya Junior College, 2018 - 2020 | Score: 95.4%

    3. Class X / Secondary School Certificate (SSC)
       St. Xavier's High School, 2018 | Percentage: 92%
    """
    pdf_bytes = create_in_memory_pdf(education_resume)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("education_levels.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    degrees = [edu["degree"] for edu in data["education"]]

    assert any("Bachelor of Technology" in d for d in degrees)
    assert any("Class XII" in d or "Intermediate" in d for d in degrees)
    assert any("Class X" in d or "Secondary" in d for d in degrees)
    assert len(data["education"]) == 3


def test_institution_clean_of_cgpa_and_percentage():
    """Verify institution name is cleanly extracted without attached CGPA or percentage."""
    resume_text = """
    Education:
    Bachelor of Technology in Information Technology
    College of Engineering, Guindy | CGPA: 8.9 / 10 | 2024
    """
    pdf_bytes = create_in_memory_pdf(resume_text)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("clean_inst.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["education"]) == 1
    edu = data["education"][0]

    # Verify institution name does NOT contain the CGPA
    assert "CGPA" not in edu["institution"]
    assert "8.9" not in edu["institution"]
    assert "College of Engineering" in edu["institution"]

    # Verify score is extracted separately
    assert edu["score"] is not None
    assert "8.9" in edu["score"]


def test_project_separated_from_employment_experience():
    """Verify that academic/personal projects are not counted as paid work experience."""
    resume_with_projects = """
    Alex Morgan
    Email: alex@example.com

    Work Experience:
    Software Engineer at CloudTech Systems (Jan 2022 - Present)
    Building production microservices using Go and Docker.

    Academic Projects:
    AI Resume Analyzer
    Built an automated parser using Python and PyMuPDF to analyze student documents.

    Personal Projects:
    E-Commerce Dashboard
    Full stack shopping portal built with React, FastAPI, and PostgreSQL.
    """
    pdf_bytes = create_in_memory_pdf(resume_with_projects)
    response = client.post(
        "/api/resume/analyze",
        files={"file": ("projects_test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()

    # Work experience must only contain the genuine job, not projects
    assert len(data["experience"]["entries"]) == 1
    assert data["experience"]["entries"][0]["title"] == "Software Engineer"
    for entry in data["experience"]["entries"]:
        assert "Academic Project" not in entry["description"]
        assert "Personal Project" not in entry["description"]

    # Projects must be stored in the dedicated projects section
    assert len(data["projects"]) >= 2
    proj_titles = [p["title"] for p in data["projects"]]
    assert any("Resume Analyzer" in t for t in proj_titles)
    assert any("E-Commerce Dashboard" in t for t in proj_titles)
    assert data["statistics"]["project_count"] >= 2
