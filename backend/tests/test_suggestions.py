"""
Comprehensive Automated Test Suite for Feature #4: Resume Improvement Suggestions Engine.
Validates structural readiness scoring, categorized suggestions, rewrite templates,
target role alignment, and boundary checks.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.suggestions import (
    SuggestionsRequest,
    SuggestionsResponse,
    RESUME_READINESS_DISCLAIMER,
)
from backend.app.services.suggestions_service import SuggestionsService

client = TestClient(app)


def test_01_sparse_resume_critical_alerts():
    """Verify that a sparse/empty resume triggers high-priority suggestions and low readiness score."""
    sparse_req = SuggestionsRequest(
        filename="empty_resume.pdf",
        contact_info={"email": None, "phone": None},
        skills={"all_skills": []},
        education=[],
        experience={"entries": []},
        projects=[],
        statistics={"word_count": 80},
        extracted_text="John Doe\nObjective: Seeking a software job.",
    )

    response = SuggestionsService.analyze_resume_improvements(sparse_req)

    assert response.success is True
    assert response.readiness_score.overall_score < 60
    assert response.readiness_score.readiness_tier == "Requires Significant Improvement"
    assert response.readiness_score.disclaimer == RESUME_READINESS_DISCLAIMER

    # High-priority alerts expected for missing contact, metrics, skills, education, projects
    high_suggestions = [s for s in response.suggestions if s.priority == "High"]
    assert len(high_suggestions) >= 4

    categories = {s.category for s in response.suggestions}
    assert "Contact & Header" in categories
    assert "Impact & Action Verbs" in categories
    assert "Skills & Keyword Organization" in categories
    assert "Projects & Experience" in categories
    assert "ATS Readability & Formatting" in categories


def test_02_strong_resume_high_readiness():
    """Verify that a comprehensive, metric-driven resume receives a high score and positive breakdown."""
    strong_req = SuggestionsRequest(
        filename="senior_engineer_resume.pdf",
        contact_info={
            "email": "sarah.connor@example.com",
            "phone": "+1 (555) 234-5678",
        },
        skills={
            "programming_languages": ["Python", "JavaScript", "TypeScript"],
            "frameworks_and_libraries": ["FastAPI", "React", "Next.js"],
            "databases": ["PostgreSQL", "Redis", "MongoDB"],
            "cloud_and_devops": ["Docker", "AWS", "CI/CD", "Git"],
            "all_skills": ["Python", "JavaScript", "TypeScript", "FastAPI", "React", "Next.js", "PostgreSQL", "Redis", "MongoDB", "Docker", "AWS", "CI/CD", "Git"],
        },
        education=[{
            "degree": "Bachelor of Technology (B.Tech)",
            "institution": "University of Technology",
            "year": "2020-2024",
        }],
        experience={
            "entries": [{
                "title": "Software Engineer",
                "organization": "TechCorp",
                "duration": "2024 - Present",
                "description": "Architected 12 asynchronous REST APIs in FastAPI with Redis caching, cutting average response latency by 35% under 500 concurrent requests.",
            }]
        },
        projects=[{
            "title": "Cloud Analytics Dashboard",
            "description": "Engineered a real-time analytics dashboard with React, Tailwind CSS, and WebSockets serving 10,000+ monthly active users.",
            "technologies": ["React", "Tailwind CSS", "WebSockets"],
        }],
        statistics={"word_count": 520},
        extracted_text=(
            "Sarah Connor\nEmail: sarah.connor@example.com | Phone: +1 (555) 234-5678\n"
            "LinkedIn: https://linkedin.com/in/sarah-connor | GitHub: https://github.com/sarahconnor\n"
            "Education: B.Tech Computer Science\n"
            "Experience: Architected 12 asynchronous REST APIs in FastAPI cutting latency by 35%.\n"
            "Projects: Engineered dashboard serving 10,000+ users with React, Docker, PostgreSQL."
        ),
    )

    response = SuggestionsService.analyze_resume_improvements(strong_req)

    assert response.success is True
    assert response.readiness_score.overall_score >= 85
    assert response.readiness_score.readiness_tier == "Strong Structural Foundation"

    # All category scores should be present
    cat_names = [cs.category for cs in response.readiness_score.category_scores]
    assert len(cat_names) == 5
    for cs in response.readiness_score.category_scores:
        assert cs.score <= cs.max_score
        assert 0.0 <= cs.percentage <= 100.0


def test_03_target_role_missing_skills_suggestion():
    """Verify that specifying a target role identifies missing core competencies."""
    role_req = SuggestionsRequest(
        filename="developer_resume.pdf",
        contact_info={"email": "dev@example.com", "phone": "+1-555-0100"},
        skills={
            "all_skills": ["HTML", "CSS", "JavaScript"],
        },
        education=[{"degree": "Bachelor of Science", "institution": "State College"}],
        experience={"entries": []},
        projects=[{"title": "Portfolio Website", "description": "Built personal site in HTML and CSS", "technologies": ["HTML", "CSS"]}],
        statistics={"word_count": 300},
        extracted_text="Developer with HTML and CSS skills seeking Python backend roles.",
        target_role="Python Backend Developer",
    )

    response = SuggestionsService.analyze_resume_improvements(role_req)

    # Check for target role suggestion
    role_suggestions = [s for s in response.suggestions if "Python Backend Developer" in s.title or s.id == "skills-target-role-alignment"]
    assert len(role_suggestions) > 0
    role_sugg = role_suggestions[0]
    assert role_sugg.priority == "High"
    assert role_sugg.category == "Skills & Keyword Organization"
    assert "FastAPI" in role_sugg.issue or "Docker" in role_sugg.issue or "PostgreSQL" in role_sugg.issue


def test_04_rewrite_examples_present():
    """Verify that suggestions include concrete before/after rewrite examples with explanations."""
    passive_req = SuggestionsRequest(
        filename="passive_resume.pdf",
        contact_info={"email": "candidate@example.com", "phone": "123-456-7890"},
        skills={"all_skills": ["Python", "SQL"]},
        education=[{"degree": "B.S. Computer Science"}],
        experience={
            "entries": [{
                "title": "Software Developer",
                "description": "Responsible for working on backend bugs and helped with database queries.",
            }]
        },
        projects=[],
        statistics={"word_count": 280},
        extracted_text="Responsible for database maintenance and worked on bug fixes.",
    )

    response = SuggestionsService.analyze_resume_improvements(passive_req)

    # Should flag passive phrases and offer rewrite examples
    metric_or_passive = [s for s in response.suggestions if s.examples and len(s.examples) > 0]
    assert len(metric_or_passive) > 0

    first_example = metric_or_passive[0].examples[0]
    assert first_example.before is not None
    assert first_example.after is not None
    assert first_example.explanation is not None
    assert len(first_example.after) > len(first_example.before)


def test_05_suggestions_api_endpoint():
    """Verify POST /api/suggestions/analyze endpoint via FastAPI TestClient."""
    payload = {
        "filename": "sample_resume.pdf",
        "contact_info": {
            "email": "alex@example.com",
            "phone": "+1-800-555-0199",
        },
        "skills": {
            "all_skills": ["Python", "FastAPI", "SQL", "Docker"],
            "programming_languages": ["Python"],
            "frameworks_and_libraries": ["FastAPI"],
            "databases": ["SQL"],
            "cloud_and_devops": ["Docker"],
        },
        "education": [
            {
                "degree": "Bachelor of Technology",
                "institution": "National Institute of Technology",
            }
        ],
        "experience": {
            "entries": [
                {
                    "title": "Backend Intern",
                    "description": "Built 8 REST endpoints in FastAPI serving 1,000 requests per minute.",
                }
            ]
        },
        "projects": [
            {
                "title": "Distributed Task Queue",
                "description": "Engineered asynchronous worker queue with Redis and Python.",
                "technologies": ["Python", "Redis"],
            }
        ],
        "statistics": {
            "word_count": 480,
            "skill_count": 4,
            "education_count": 1,
            "experience_count": 1,
            "project_count": 1,
        },
        "extracted_text": "Alex | alex@example.com | +1-800-555-0199\nLinkedIn: linkedin.com/in/alex-dev\nGitHub: github.com/alex-dev\nBuilt 8 REST endpoints in FastAPI.",
        "target_role": "Python Backend Developer",
    }

    res = client.post("/api/suggestions/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert "readiness_score" in data
    assert "overall_score" in data["readiness_score"]
    assert 0 <= data["readiness_score"]["overall_score"] <= 100
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert "summary" in data
    assert data["summary"]["total"] == len(data["suggestions"])
    assert data["target_role"] == "Python Backend Developer"
