"""
Automated Test Suite for Career Recommendations & Personalized Learning Roadmap (Phase 11).

Covers:
1. Available roles endpoint (GET /api/roadmap/available-roles)
2. Career recommendations generation (POST /api/roadmap/recommendations)
3. Categorization into Strong Matches vs Alternative Career Paths
4. 30-day personalized roadmap generation (exactly 4 weekly milestones)
5. 60-day personalized roadmap generation (exactly 8 weekly milestones)
6. Canonical free resource verification (is_free=True, genuine https URLs)
7. Ethical disclaimer presence
8. Duration input validation (HTTP 422 on invalid duration)
9. Prioritization of custom missing skills
10. Strict Pydantic response schema validation
"""

import pytest
from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.schemas.roadmap import (
        LearningResource,
        RoadmapMilestone,
        PersonalizedRoadmap,
        CareerRoleRecommendation,
        CareerRecommendationsRequest,
        CareerRecommendationsResponse,
        RoadmapGenerationRequest,
        RoadmapGenerationResponse,
        ETHICAL_ROADMAP_DISCLAIMER,
    )
    from backend.app.services.roadmap_service import get_roadmap_service
except ModuleNotFoundError:
    from app.main import app
    from app.schemas.roadmap import (
        LearningResource,
        RoadmapMilestone,
        PersonalizedRoadmap,
        CareerRoleRecommendation,
        CareerRecommendationsRequest,
        CareerRecommendationsResponse,
        RoadmapGenerationRequest,
        RoadmapGenerationResponse,
        ETHICAL_ROADMAP_DISCLAIMER,
    )
    from app.services.roadmap_service import get_roadmap_service

client = TestClient(app)

SAMPLE_RESUME_SKILLS = ["Python", "FastAPI", "React", "PostgreSQL", "Git"]


# ==============================================================================
# Test Scenario 1: Available Roles Endpoint
# ==============================================================================
def test_01_available_roles_endpoint():
    """Verify that GET /api/roadmap/available-roles returns list of canonical benchmark roles with entry-appropriate titles."""
    response = client.get("/api/roadmap/available-roles")
    assert response.status_code == 200
    roles = response.json()
    assert isinstance(roles, list)
    assert len(roles) >= 5
    assert "Full Stack Software Engineer" in roles
    assert "Backend Software Engineer" in roles
    assert "Frontend Software Engineer" in roles
    assert "Cloud & DevOps Engineer" in roles
    assert "Senior Backend Infrastructure Engineer" not in roles
    assert "Frontend Systems Architect" not in roles


# ==============================================================================
# Test Scenario 2: Career Recommendations Generation
# ==============================================================================
def test_02_career_recommendations_success():
    """Verify that POST /api/roadmap/recommendations returns ranked recommendations with transferable skills accounted."""
    payload = {
        "resume_skills": SAMPLE_RESUME_SKILLS,
        "predicted_categories": ["INFORMATION-TECHNOLOGY"],
        "experience_years": 4.5,
    }
    response = client.post("/api/roadmap/recommendations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 5
    assert data["disclaimer"] == ETHICAL_ROADMAP_DISCLAIMER

    # Verify transferable_skills field exists on every recommendation
    for r in data["recommendations"]:
        assert "transferable_skills" in r
        assert isinstance(r["transferable_skills"], list)


# ==============================================================================
# Test Scenario 3: Match Types Separation & Skill Accounting
# ==============================================================================
def test_03_match_types_separation():
    """Verify clear distinction between Strong Matches, Alternative Career Paths, and Exploratory Tracks."""
    payload = {
        "resume_skills": SAMPLE_RESUME_SKILLS,
        "predicted_categories": ["INFORMATION-TECHNOLOGY"],
        "experience_years": 1.0,
    }
    response = client.post("/api/roadmap/recommendations", json=payload)
    assert response.status_code == 200

    recs = response.json()["recommendations"]
    strong = [r for r in recs if r["match_type"] == "Strong Match"]
    alternative = [r for r in recs if r["match_type"] == "Alternative Career Path"]
    exploratory = [r for r in recs if r["match_type"] == "Exploratory Track"]

    assert len(strong) > 0, "Expected at least one Strong Match for Python/React developer"
    assert len(alternative) > 0, "Expected at least one Alternative Career Path (15% to 50%)"
    assert len(exploratory) > 0, "Expected at least one Exploratory Track (< 15%)"

    # Full Stack or Backend should be a Strong Match
    strong_titles = [r["role_title"] for r in strong]
    assert any("Full Stack" in t or "Backend" in t for t in strong_titles)

    # Threshold enforcement:
    for r in exploratory:
        assert r["match_percentage"] < 15.0, f"Role {r['role_title']} has {r['match_percentage']}% but is labeled Exploratory"

    for r in alternative:
        assert 15.0 <= r["match_percentage"] < 50.0, f"Role {r['role_title']} has {r['match_percentage']}% but is labeled Alternative"

    for r in strong:
        assert r["match_percentage"] >= 40.0, f"Role {r['role_title']} has {r['match_percentage']}% but is labeled Strong"

    # Skill accounting: Every candidate detected skill must be in matched_skills OR transferable_skills
    candidate_skills_lower = {s.lower() for s in SAMPLE_RESUME_SKILLS}
    for r in recs:
        accounted_skills_lower = {s.lower() for s in r["matched_skills"]}.union(
            {s.lower() for s in r["transferable_skills"]}
        )
        assert candidate_skills_lower == accounted_skills_lower, (
            f"Skills mismatch for role {r['role_title']}: "
            f"Candidate: {candidate_skills_lower}, Accounted: {accounted_skills_lower}"
        )

    # Early-career experience_years factoring (< 2.0 yrs)
    for r in recs:
        assert len(r["reasoning"]) > 20
        # When experience_years < 2.0, reasoning reflects entry-level / early-career framing
        assert any(k in r["reasoning"].lower() for k in ["entry-level", "early-career", "exploratory"])


# ==============================================================================
# Test Scenario 4: 30-Day Personalized Roadmap (4 Weeks)
# ==============================================================================
def test_04_generate_30_day_roadmap():
    """Verify that 30-day roadmap generates exactly 4 weekly milestones with deliverables."""
    payload = {
        "target_role": "Full Stack Software Engineer",
        "resume_skills": SAMPLE_RESUME_SKILLS,
        "duration": "30-day",
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 200

    roadmap = response.json()["roadmap"]
    assert roadmap["duration"] == "30-day"
    assert "Foundational" in roadmap["target_level"]
    assert len(roadmap["milestones"]) == 4

    # Validate weekly milestone sequence and content
    for idx, m in enumerate(roadmap["milestones"], 1):
        assert m["week"] == idx
        assert len(m["title"]) > 5
        assert len(m["focus_area"]) > 3
        assert len(m["learning_objectives"]) >= 2
        assert len(m["practical_exercise"]) > 10
        assert len(m["deliverable"]) > 10
        assert len(m["resources"]) >= 1

    assert len(roadmap["capstone_project"]) > 20
    assert roadmap["ethical_disclaimer"] == ETHICAL_ROADMAP_DISCLAIMER


# ==============================================================================
# Test Scenario 5: 60-Day Personalized Roadmap (8 Weeks)
# ==============================================================================
def test_05_generate_60_day_roadmap():
    """Verify that 60-day roadmap generates exactly 8 weekly milestones."""
    payload = {
        "target_role": "Cloud & DevOps Engineer",
        "resume_skills": SAMPLE_RESUME_SKILLS,
        "duration": "60-day",
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 200

    roadmap = response.json()["roadmap"]
    assert roadmap["duration"] == "60-day"
    assert "Portfolio" in roadmap["target_level"]
    assert len(roadmap["milestones"]) == 8

    weeks = [m["week"] for m in roadmap["milestones"]]
    assert weeks == [1, 2, 3, 4, 5, 6, 7, 8]


# ==============================================================================
# Test Scenario 6: Verified Free Canonical Learning Resources
# ==============================================================================
def test_06_verified_free_resources():
    """Verify that all attached resources are verified free and point to genuine canonical URLs."""
    payload = {
        "target_role": "Backend Software Engineer",
        "resume_skills": ["Python"],
        "duration": "30-day",
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 200

    roadmap = response.json()["roadmap"]
    all_resources = []
    for m in roadmap["milestones"]:
        all_resources.extend(m["resources"])

    assert len(all_resources) >= 4
    for res in all_resources:
        assert res["is_free"] is True
        assert res["url"].startswith("https://")
        assert len(res["title"]) > 3
        assert len(res["platform"]) > 2
        # Check canonical hostnames
        valid_domains = [
            "docs.python.org",
            "fastapi.tiangolo.com",
            "docs.djangoproject.com",
            "react.dev",
            "developer.mozilla.org",
            "www.typescriptlang.org",
            "www.postgresql.org",
            "docs.docker.com",
            "kubernetes.io",
            "aws.amazon.com",
            "redis.io",
            "git-scm.com",
            "developer.hashicorp.com",
            "pytorch.org",
            "scikit-learn.org",
            "www.freecodecamp.org",
        ]
        assert any(domain in res["url"] for domain in valid_domains), f"Non-canonical URL: {res['url']}"


# ==============================================================================
# Test Scenario 7: Ethical Disclaimer Consistency
# ==============================================================================
def test_07_ethical_disclaimer_everywhere():
    """Verify ethical expectation disclaimer is returned in responses."""
    r1 = client.post("/api/roadmap/recommendations", json={"resume_skills": ["Python"]})
    assert r1.status_code == 200
    assert ETHICAL_ROADMAP_DISCLAIMER in r1.json()["disclaimer"]

    r2 = client.post("/api/roadmap/generate", json={"target_role": "Full Stack Software Engineer"})
    assert r2.status_code == 200
    assert ETHICAL_ROADMAP_DISCLAIMER in r2.json()["roadmap"]["ethical_disclaimer"]


# ==============================================================================
# Test Scenario 8: Duration Input Validation
# ==============================================================================
def test_08_duration_validation():
    """Verify that invalid duration string is rejected with HTTP 422."""
    payload = {
        "target_role": "Full Stack Software Engineer",
        "duration": "90-day",  # Only 30-day and 60-day supported
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 422


# ==============================================================================
# Test Scenario 9: Custom Missing Skills Prioritization
# ==============================================================================
def test_09_custom_missing_skills_prioritization():
    """Verify that custom missing skills (from job description matching) are prioritized."""
    payload = {
        "target_role": "Full Stack Software Engineer",
        "resume_skills": ["Python", "React"],
        "duration": "30-day",
        "custom_missing_skills": ["Docker", "Redis"],
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 200

    roadmap = response.json()["roadmap"]
    assert "Docker" in roadmap["skills_to_acquire"]
    assert "Redis" in roadmap["skills_to_acquire"]


# ==============================================================================
# Test Scenario 10: Strict Response Schema Validation
# ==============================================================================
def test_10_response_schema_validation():
    """Verify responses strictly parse into Pydantic models."""
    r1 = client.post("/api/roadmap/recommendations", json={"resume_skills": SAMPLE_RESUME_SKILLS})
    parsed_recs = CareerRecommendationsResponse(**r1.json())
    assert parsed_recs.success is True
    assert len(parsed_recs.recommendations) >= 5

    r2 = client.post("/api/roadmap/generate", json={"target_role": "Full Stack Software Engineer"})
    parsed_roadmap = RoadmapGenerationResponse(**r2.json())
    assert parsed_roadmap.success is True
    assert parsed_roadmap.roadmap.role_title == "Full Stack Software Engineer"
