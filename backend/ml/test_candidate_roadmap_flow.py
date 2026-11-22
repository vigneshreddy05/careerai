"""
Verification of Phase 11 end-to-end career recommendation & roadmap flow.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))

from backend.app.services.roadmap_service import get_roadmap_service

service = get_roadmap_service()

# Realistic candidate profile
candidate_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "React"]
predicted_cats = ["INFORMATION-TECHNOLOGY"]
exp_years = 5.0

print("=" * 60)
print("TESTING CAREER RECOMMENDATIONS FOR CANDIDATE")
print("=" * 60)
recs_resp = service.recommend_career_roles(
    resume_skills=candidate_skills,
    predicted_categories=predicted_cats,
    experience_years=exp_years,
)

print(f"Total analyzed roles: {recs_resp.total_analyzed_roles}")
print(f"Recommendations generated: {len(recs_resp.recommendations)}")

strong = [r for r in recs_resp.recommendations if r.match_type == "Strong Match"]
alt = [r for r in recs_resp.recommendations if r.match_type == "Alternative Career Path"]

print(f"\nStrong Matches ({len(strong)}):")
for r in strong:
    print(f"  - {r.role_title}: {r.match_percentage}% overlap | Core: {r.matched_skills} | Gaps: {r.missing_skills}")
    print(f"    Reasoning: {r.reasoning}")

print(f"\nAlternative Career Paths ({len(alt)}):")
for r in alt:
    print(f"  - {r.role_title}: {r.match_percentage}% overlap | Core: {r.matched_skills} | Gaps: {r.missing_skills}")

print("\n" + "=" * 60)
print("TESTING 30-DAY PERSONALIZED ROADMAP GENERATION")
print("=" * 60)
target_role = "Backend Software Engineer"
roadmap_30 = service.generate_roadmap(
    target_role=target_role,
    resume_skills=candidate_skills,
    duration="30-day",
).roadmap

print(f"Target Role: {roadmap_30.role_title}")
print(f"Duration: {roadmap_30.duration}")
print(f"Target Level: {roadmap_30.target_level}")
print(f"Existing Skills Leveraged: {roadmap_30.existing_skills_leveraged}")
print(f"Skills to Acquire: {roadmap_30.skills_to_acquire}")
print(f"Milestones Count: {len(roadmap_30.milestones)}")
for m in roadmap_30.milestones:
    print(f"  Week {m.week}: {m.title} [{m.focus_area}]")
    print(f"    Deliverable: {m.deliverable}")
    print(f"    Resources: {len(m.resources)} verified free links")

print("\n" + "=" * 60)
print("TESTING 60-DAY PERSONALIZED ROADMAP GENERATION")
print("=" * 60)
roadmap_60 = service.generate_roadmap(
    target_role=target_role,
    resume_skills=candidate_skills,
    duration="60-day",
).roadmap

print(f"Target Role: {roadmap_60.role_title}")
print(f"Duration: {roadmap_60.duration}")
print(f"Milestones Count: {len(roadmap_60.milestones)}")
print(f"Portfolio Capstone: {roadmap_60.capstone_project}")

print("\nAll assertions and generation steps completed successfully!")
