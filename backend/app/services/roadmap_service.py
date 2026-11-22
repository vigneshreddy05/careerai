"""
Career Recommendations and Personalized Learning Roadmap Engine for CareerAI.

Generates:
1. Explainable career role recommendations based on candidate resume skills and DistilBERT categories.
2. Structured 30-day and 60-day personalized learning roadmaps with weekly deliverables.
3. Curated, verified, 100% free canonical educational resources.
"""

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

try:
    from backend.app.schemas.roadmap import (
        LearningResource,
        RoadmapMilestone,
        PersonalizedRoadmap,
        CareerRoleRecommendation,
        CareerRecommendationsResponse,
        RoadmapGenerationResponse,
        ETHICAL_ROADMAP_DISCLAIMER,
    )
except ModuleNotFoundError:
    from app.schemas.roadmap import (
        LearningResource,
        RoadmapMilestone,
        PersonalizedRoadmap,
        CareerRoleRecommendation,
        CareerRecommendationsResponse,
        RoadmapGenerationResponse,
        ETHICAL_ROADMAP_DISCLAIMER,
    )


# Curated repository of verified, canonical, 100% free learning resources
VERIFIED_FREE_RESOURCES: Dict[str, List[LearningResource]] = {
    "Python": [
        LearningResource(
            title="The Python Official Tutorial",
            platform="Python Software Foundation",
            resource_type="Official Documentation",
            url="https://docs.python.org/3/tutorial/",
            is_free=True,
        ),
        LearningResource(
            title="Scientific Computing with Python",
            platform="freeCodeCamp",
            resource_type="Interactive Tutorial",
            url="https://www.freecodecamp.org/learn/scientific-computing-with-python/",
            is_free=True,
        ),
    ],
    "FastAPI": [
        LearningResource(
            title="FastAPI Tutorial - User Guide",
            platform="FastAPI Official Documentation",
            resource_type="Official Documentation",
            url="https://fastapi.tiangolo.com/tutorial/",
            is_free=True,
        ),
    ],
    "Django": [
        LearningResource(
            title="Writing your first Django app",
            platform="Django Software Foundation",
            resource_type="Official Documentation",
            url="https://docs.djangoproject.com/en/stable/intro/tutorial01/",
            is_free=True,
        ),
    ],
    "React": [
        LearningResource(
            title="Quick Start: Describing the UI",
            platform="React Official Documentation",
            resource_type="Official Documentation",
            url="https://react.dev/learn",
            is_free=True,
        ),
    ],
    "JavaScript": [
        LearningResource(
            title="JavaScript Guide & Core Concepts",
            platform="MDN Web Docs",
            resource_type="MDN Web Docs",
            url="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
            is_free=True,
        ),
    ],
    "TypeScript": [
        LearningResource(
            title="The TypeScript Handbook",
            platform="Microsoft TypeScript Documentation",
            resource_type="Official Documentation",
            url="https://www.typescriptlang.org/docs/handbook/intro.html",
            is_free=True,
        ),
    ],
    "PostgreSQL": [
        LearningResource(
            title="PostgreSQL Official Tutorial",
            platform="PostgreSQL Global Development Group",
            resource_type="Official Documentation",
            url="https://www.postgresql.org/docs/current/tutorial.html",
            is_free=True,
        ),
    ],
    "Docker": [
        LearningResource(
            title="Docker Getting Started Guide",
            platform="Docker Official Documentation",
            resource_type="Official Documentation",
            url="https://docs.docker.com/get-started/",
            is_free=True,
        ),
    ],
    "Kubernetes": [
        LearningResource(
            title="Kubernetes Interactive Basics Tutorial",
            platform="Kubernetes Official Documentation",
            resource_type="Interactive Tutorial",
            url="https://kubernetes.io/docs/tutorials/kubernetes-basics/",
            is_free=True,
        ),
    ],
    "AWS": [
        LearningResource(
            title="AWS Free Tier Hands-on Tutorials",
            platform="Amazon Web Services",
            resource_type="Official Documentation",
            url="https://aws.amazon.com/getting-started/",
            is_free=True,
        ),
    ],
    "Redis": [
        LearningResource(
            title="Redis Getting Started & Data Structures",
            platform="Redis Documentation",
            resource_type="Official Documentation",
            url="https://redis.io/docs/latest/get-started/",
            is_free=True,
        ),
    ],
    "Git": [
        LearningResource(
            title="Pro Git Book & Official Documentation",
            platform="Git SCM",
            resource_type="Open-Access Guide",
            url="https://git-scm.com/doc",
            is_free=True,
        ),
    ],
    "Terraform": [
        LearningResource(
            title="HashiCorp Terraform Tutorials",
            platform="HashiCorp Developer",
            resource_type="Official Documentation",
            url="https://developer.hashicorp.com/terraform/tutorials",
            is_free=True,
        ),
    ],
    "PyTorch": [
        LearningResource(
            title="Deep Learning with PyTorch: A 60 Minute Blitz",
            platform="PyTorch Official Documentation",
            resource_type="Official Documentation",
            url="https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html",
            is_free=True,
        ),
    ],
    "Scikit-learn": [
        LearningResource(
            title="Scikit-learn Machine Learning Tutorial",
            platform="Scikit-learn Documentation",
            resource_type="Official Documentation",
            url="https://scikit-learn.org/stable/tutorial/basic/tutorial.html",
            is_free=True,
        ),
    ],
    "Linux": [
        LearningResource(
            title="Command Line Crash Course for Developers",
            platform="MDN Web Docs",
            resource_type="MDN Web Docs",
            url="https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Understanding_client-side_tools/Command_line",
            is_free=True,
        ),
    ],
    "General Web": [
        LearningResource(
            title="freeCodeCamp Full Stack Open Curriculum",
            platform="freeCodeCamp",
            resource_type="Interactive Tutorial",
            url="https://www.freecodecamp.org/learn/",
            is_free=True,
        ),
    ],
}


# Standard Benchmark Career Roles Catalog
ROLE_CATALOG = [
    {
        "role_title": "Full Stack Software Engineer",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["Python", "JavaScript", "React", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "capstone_30": "Build and deploy a responsive task-management web application with a FastAPI backend, PostgreSQL database, and React frontend.",
        "capstone_60": "Architect an enterprise multi-tier e-commerce catalog with React/TypeScript frontend, FastAPI microservices, PostgreSQL sharding, Redis caching, and Docker Compose orchestration.",
    },
    {
        "role_title": "Cloud & DevOps Engineer",
        "category": "ENGINEERING",
        "core_skills": ["Linux", "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Python"],
        "capstone_30": "Create an automated GitHub Actions CI/CD pipeline deploying a containerized Python service to AWS with health checks.",
        "capstone_60": "Design and provision an end-to-end Kubernetes cluster on AWS using Terraform infrastructure-as-code, Helm charts, and Prometheus/Grafana observability.",
    },
    {
        "role_title": "Backend Software Engineer",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "AWS"],
        "capstone_30": "Develop a high-throughput rate-limited REST API in FastAPI utilizing Redis for caching and PostgreSQL for persistent transactions.",
        "capstone_60": "Build a distributed asynchronous event-processing pipeline with background workers, database connection pooling, Redis pub/sub, and automated stress testing.",
    },
    {
        "role_title": "Frontend Software Engineer",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Tailwind CSS", "Next.js"],
        "capstone_30": "Build a modular, accessible component library in React and TypeScript styled with Tailwind CSS and documented with interactive stories.",
        "capstone_60": "Develop a server-side rendered analytics portal using Next.js, TypeScript, global state management, responsive charting, and Core Web Vitals optimization.",
    },
    {
        "role_title": "Data Scientist & ML Practitioner",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["Python", "SQL", "Pandas", "NumPy", "Scikit-learn", "PyTorch", "Machine Learning"],
        "capstone_30": "Perform end-to-end exploratory data analysis on a public dataset and build a supervised classification pipeline with Scikit-learn.",
        "capstone_60": "Train and evaluate a custom sequence model in PyTorch, package it inside a FastAPI inference service, and containerize the ML pipeline for deployment.",
    },
    {
        "role_title": "Database Administrator & Data Engineer",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Python", "Linux"],
        "capstone_30": "Design a normalized relational schema in PostgreSQL with indexing strategies, write stored procedures, and automate backup scripts in Bash.",
        "capstone_60": "Construct an automated ETL data warehouse pipeline extracting transactional records into PostgreSQL and streaming analytical aggregates into Redis.",
    },
    {
        "role_title": "Software QA & Automation Engineer",
        "category": "INFORMATION-TECHNOLOGY",
        "core_skills": ["Python", "JavaScript", "Git", "CI/CD", "Docker", "Linux"],
        "capstone_30": "Develop an automated integration testing framework for REST APIs using PyTest with mocked fixtures and coverage reports.",
        "capstone_60": "Construct a full test automation matrix integrating end-to-end UI regression tests and API performance benchmarks executed automatically via CI/CD.",
    },
]


class RoadmapService:
    """
    Engine for generating explainable career recommendations and personalized roadmaps.
    """

    @staticmethod
    def get_available_roles() -> List[str]:
        """Return the list of benchmark career role titles."""
        return [r["role_title"] for r in ROLE_CATALOG]

    @staticmethod
    def recommend_career_roles(
        resume_skills: List[str],
        predicted_categories: Optional[List[str]] = None,
        experience_years: Optional[float] = None
    ) -> CareerRecommendationsResponse:
        """
        Generate explainable career role recommendations based on candidate's verified skills
        and DistilBERT predicted domains.
        """
        candidate_skills_set = {s.strip().lower() for s in resume_skills if s.strip()}
        primary_category = predicted_categories[0].upper() if predicted_categories else None

        recommendations: List[CareerRoleRecommendation] = []

        for role_info in ROLE_CATALOG:
            role_skills = role_info["core_skills"]
            role_core_skills_lower = {s.lower() for s in role_skills}
            matched: List[str] = []
            missing: List[str] = []

            for s in role_skills:
                if s.lower() in candidate_skills_set:
                    matched.append(s)
                else:
                    missing.append(s)

            # Account for all candidate detected skills not part of this role's core list
            transferable: List[str] = []
            seen_transferable: Set[str] = set()
            for s in resume_skills:
                s_clean = s.strip()
                if s_clean and s_clean.lower() not in role_core_skills_lower and s_clean.lower() not in seen_transferable:
                    transferable.append(s_clean)
                    seen_transferable.add(s_clean.lower())

            total_core = len(role_skills)
            overlap_pct = round((len(matched) / total_core * 100), 1) if total_core > 0 else 0.0

            # Determine match type: Strong Match, Alternative Career Path (>=15%), or Exploratory Track (<15%)
            category_match = primary_category and role_info["category"] == primary_category
            if overlap_pct >= 50.0 or (overlap_pct >= 40.0 and category_match):
                match_type = "Strong Match"
                ramp_duration = "30-day" if len(missing) <= 3 else "60-day"
            elif overlap_pct >= 15.0:
                match_type = "Alternative Career Path"
                ramp_duration = "60-day"
            else:
                match_type = "Exploratory Track"
                ramp_duration = "60-day"

            # Formulate transparent, honest reasoning incorporating experience_years
            is_early_career = experience_years is None or experience_years < 2.0
            matched_preview = ", ".join(matched[:3]) if matched else "foundational concepts"
            missing_preview = ", ".join(missing[:3]) if missing else "role specialization"

            if match_type == "Strong Match":
                if is_early_career:
                    reasoning = (
                        f"Strong entry-level alignment ({overlap_pct}% core overlap). Capitalizes on your verified skills in "
                        f"{matched_preview}. Focus on acquiring {missing_preview} to complete requirements for junior/associate roles."
                    )
                else:
                    reasoning = (
                        f"Strong direct alignment ({overlap_pct}% core overlap). Capitalizes on your verified skills in "
                        f"{matched_preview} ({experience_years:.1f} yrs experience). Focus on acquiring {missing_preview} to complete requirements."
                    )
            elif match_type == "Alternative Career Path":
                if is_early_career:
                    reasoning = (
                        f"Early-career lateral expansion path ({overlap_pct}% core overlap). Leverages foundational skills in "
                        f"{matched_preview} to pivot toward {role_info['category'].lower()} with focused portfolio-building in {missing_preview}."
                    )
                else:
                    reasoning = (
                        f"Lateral career expansion path ({overlap_pct}% core overlap). Leverages transferable competencies in "
                        f"{matched_preview} while expanding into {role_info['category'].lower()} through structured ramp-up in {missing_preview}."
                    )
            else:
                # Exploratory Track (< 15.0% overlap)
                if is_early_career:
                    reasoning = (
                        f"Exploratory entry-level pathway ({overlap_pct}% core overlap). Requires comprehensive foundational upskilling in "
                        f"{missing_preview} before targeting active job applications."
                    )
                else:
                    reasoning = (
                        f"Exploratory career shift ({overlap_pct}% core overlap). Requires substantial foundational upskilling in "
                        f"{missing_preview} across {role_info['category'].lower()} fundamentals."
                    )

            recommendations.append(
                CareerRoleRecommendation(
                    role_title=role_info["role_title"],
                    category=role_info["category"],
                    match_type=match_type,
                    match_percentage=overlap_pct,
                    matched_skills=matched,
                    missing_skills=missing,
                    transferable_skills=transferable,
                    reasoning=reasoning,
                    recommended_duration=ramp_duration,
                )
            )

        # Sort recommendations: Strong Match (tier 2), Alternative Career Path (tier 1), Exploratory Track (tier 0), then match_percentage descending
        match_tier = {
            "Strong Match": 2,
            "Alternative Career Path": 1,
            "Exploratory Track": 0,
        }
        recommendations.sort(
            key=lambda r: (match_tier.get(r.match_type, 0), r.match_percentage),
            reverse=True,
        )

        return CareerRecommendationsResponse(
            success=True,
            recommendations=recommendations,
            total_analyzed_roles=len(ROLE_CATALOG),
            disclaimer=ETHICAL_ROADMAP_DISCLAIMER,
        )

    @classmethod
    def generate_roadmap(
        cls,
        target_role: str,
        resume_skills: List[str],
        duration: str = "30-day",
        custom_missing_skills: Optional[List[str]] = None
    ) -> RoadmapGenerationResponse:
        """
        Synthesize a personalized 30-day or 60-day milestone roadmap based on candidate skills.
        """
        # Normalize duration
        is_60_day = "60" in duration
        duration_label = "60-day" if is_60_day else "30-day"
        target_level = (
            "Comprehensive Hands-on Portfolio Implementation"
            if is_60_day
            else "Foundational Tool Proficiency"
        )

        # Locate role metadata or create fallback
        role_entry = next((r for r in ROLE_CATALOG if r["role_title"].lower() == target_role.lower()), None)
        if not role_entry:
            role_entry = {
                "role_title": target_role,
                "category": "INFORMATION-TECHNOLOGY",
                "core_skills": ["Python", "Docker", "Git", "PostgreSQL"],
                "capstone_30": f"Build a practical demonstration project showcasing core {target_role} competencies.",
                "capstone_60": f"Develop an end-to-end multi-tier portfolio application aligned with {target_role} standards.",
            }

        candidate_set = {s.strip().lower() for s in resume_skills if s.strip()}
        existing_leveraged = [s for s in role_entry["core_skills"] if s.lower() in candidate_set]

        # Prioritize missing skills
        if custom_missing_skills:
            target_skills_to_learn = [s for s in custom_missing_skills if s.strip()]
        else:
            target_skills_to_learn = [s for s in role_entry["core_skills"] if s.lower() not in candidate_set]

        # If user has no missing skills, suggest advanced tooling
        if not target_skills_to_learn:
            target_skills_to_learn = ["Docker", "CI/CD", "Redis", "Performance Optimization"]

        milestones: List[RoadmapMilestone] = []

        if not is_60_day:
            # 30-Day Plan: 4 Weekly Milestones
            milestones = cls._build_30_day_milestones(
                target_role=role_entry["role_title"],
                skills_to_learn=target_skills_to_learn,
                existing_skills=existing_leveraged,
            )
            capstone_desc = role_entry["capstone_30"]
        else:
            # 60-Day Plan: 8 Weekly Milestones
            milestones = cls._build_60_day_milestones(
                target_role=role_entry["role_title"],
                skills_to_learn=target_skills_to_learn,
                existing_skills=existing_leveraged,
            )
            capstone_desc = role_entry["capstone_60"]

        roadmap = PersonalizedRoadmap(
            role_title=role_entry["role_title"],
            duration=duration_label,
            target_level=target_level,
            existing_skills_leveraged=existing_leveraged,
            skills_to_acquire=target_skills_to_learn,
            milestones=milestones,
            capstone_project=capstone_desc,
            ethical_disclaimer=ETHICAL_ROADMAP_DISCLAIMER,
        )

        return RoadmapGenerationResponse(success=True, roadmap=roadmap)

    @classmethod
    def _get_resources_for_skills(cls, skills: List[str]) -> List[LearningResource]:
        """Collect verified learning resources for a list of target skills."""
        collected: List[LearningResource] = []
        seen_urls: Set[str] = set()

        for skill in skills:
            matches = VERIFIED_FREE_RESOURCES.get(skill, [])
            for res in matches:
                if res.url not in seen_urls:
                    seen_urls.add(res.url)
                    collected.append(res)

        if not collected:
            # Fallback to general web & Git documentation
            for res in VERIFIED_FREE_RESOURCES.get("General Web", []) + VERIFIED_FREE_RESOURCES.get("Git", []):
                if res.url not in seen_urls:
                    seen_urls.add(res.url)
                    collected.append(res)

        return collected

    @classmethod
    def _build_30_day_milestones(
        cls,
        target_role: str,
        skills_to_learn: List[str],
        existing_skills: List[str]
    ) -> List[RoadmapMilestone]:
        """Construct 4 targeted weekly milestones for a 30-day intensive ramp-up."""
        # Distribute skills across weeks
        s1 = skills_to_learn[:2] if skills_to_learn else ["Core Tool Fundamentals"]
        s2 = skills_to_learn[2:4] if len(skills_to_learn) > 2 else s1
        s3 = skills_to_learn[4:6] if len(skills_to_learn) > 4 else ["Testing & CI/CD"]
        s4 = skills_to_learn[6:] if len(skills_to_learn) > 6 else ["Portfolio Project Deployment"]

        leveraged_text = f" (building upon your {', '.join(existing_skills[:2])} experience)" if existing_skills else ""

        return [
            RoadmapMilestone(
                week=1,
                title="Environment Setup & Tool Syntax Fundamentals",
                focus_area=f"{', '.join(s1)} Core Fundamentals",
                learning_objectives=[
                    f"Install and configure official developer tooling for {', '.join(s1)}.",
                    "Review canonical official documentation and standard coding conventions.",
                    "Build isolated sandbox scripts to practice basic operations.",
                ],
                target_skills=s1,
                practical_exercise=f"Write 3 standalone utility scripts implementing core operations with {s1[0]}.",
                deliverable="Clean, linted code repository committed to Git with a documented README.",
                resources=cls._get_resources_for_skills(s1),
            ),
            RoadmapMilestone(
                week=2,
                title="API Integration & Data Handling",
                focus_area=f"{', '.join(s2)} Practical Implementation",
                learning_objectives=[
                    f"Implement structured data transactions and API interfaces{leveraged_text}.",
                    "Handle error states, input validation, and connection lifecycles.",
                    "Connect application logic with persistent data storage.",
                ],
                target_skills=s2,
                practical_exercise="Construct a working CRUD API endpoint with input schema validation.",
                deliverable="Fully functional API endpoint passing automated status code checks.",
                resources=cls._get_resources_for_skills(s2),
            ),
            RoadmapMilestone(
                week=3,
                title="Containerization, Tooling & Automation",
                focus_area="Modern Workflow & Testing",
                learning_objectives=[
                    "Containerize application runtime environment to ensure consistent execution.",
                    "Write automated unit tests verifying core logic and boundary conditions.",
                    "Set up automated format and lint checks.",
                ],
                target_skills=s3,
                practical_exercise="Create a multi-stage Dockerfile and a test suite with 5+ automated test cases.",
                deliverable="Container image that builds cleanly and executes tests without errors.",
                resources=cls._get_resources_for_skills(s3 + ["Docker", "Git"]),
            ),
            RoadmapMilestone(
                week=4,
                title="Capstone Implementation & Portfolio Documentation",
                focus_area=f"{target_role} Synthesis",
                learning_objectives=[
                    f"Integrate all acquired competencies into a cohesive mini-project tailored for {target_role}.",
                    "Draft clear architectural documentation and quickstart instructions.",
                    "Conduct self-directed code review against standard best practices.",
                ],
                target_skills=s4,
                practical_exercise="Assemble and deploy your end-to-end capstone repository with automated tests.",
                deliverable="Public portfolio repository with interactive demo instructions and architecture diagram.",
                resources=cls._get_resources_for_skills(["Git", "General Web"]),
            ),
        ]

    @classmethod
    def _build_60_day_milestones(
        cls,
        target_role: str,
        skills_to_learn: List[str],
        existing_skills: List[str]
    ) -> List[RoadmapMilestone]:
        """Construct 8 comprehensive weekly milestones for a 60-day portfolio implementation."""
        s1 = skills_to_learn[:1] if skills_to_learn else ["Language Foundations"]
        s2 = skills_to_learn[1:2] if len(skills_to_learn) > 1 else s1
        s3 = skills_to_learn[2:3] if len(skills_to_learn) > 2 else ["API Architecture"]
        s4 = skills_to_learn[3:4] if len(skills_to_learn) > 3 else ["Databases & Caching"]
        s5 = skills_to_learn[4:5] if len(skills_to_learn) > 4 else ["Docker & Cloud Setup"]
        s6 = ["CI/CD Automation", "Testing Suites"]
        s7 = ["Multi-Tier Capstone Integration"]
        s8 = ["Production Hardening & Portfolio Deployment"]

        return [
            RoadmapMilestone(
                week=1,
                title="Deep Tool Syntax & Language Fundamentals",
                focus_area=f"{', '.join(s1)} Deep Dive",
                learning_objectives=[
                    f"Master the core idioms, memory model, and typing conventions of {s1[0]}.",
                    "Explore official documentation and standard library capabilities.",
                    "Implement algorithmic exercises to reinforce fundamental syntax.",
                ],
                target_skills=s1,
                practical_exercise="Complete 5 algorithmic and data transformation challenges using official idioms.",
                deliverable="GitHub repository with documented problem solutions and test suites.",
                resources=cls._get_resources_for_skills(s1),
            ),
            RoadmapMilestone(
                week=2,
                title="Advanced Language Constructs & Module Architecture",
                focus_area=f"{', '.join(s2)} Architecture",
                learning_objectives=[
                    "Implement object-oriented or functional patterns, concurrency, or async workflows.",
                    "Structure modular packages with clear dependency boundaries.",
                    "Enforce strict linting, type hinting, and code formatting.",
                ],
                target_skills=s2,
                practical_exercise="Design and package a reusable utility module with unit tests.",
                deliverable="Standalone Python or JavaScript package installable in isolated environments.",
                resources=cls._get_resources_for_skills(s2),
            ),
            RoadmapMilestone(
                week=3,
                title="Service Architecture & RESTful API Design",
                focus_area=f"{', '.join(s3)} Service Layer",
                learning_objectives=[
                    "Design high-throughput REST API schemas with request validation.",
                    "Implement authentication, request routing, and exception handlers.",
                    "Document endpoints using OpenAPI / Swagger specifications.",
                ],
                target_skills=s3,
                practical_exercise="Build a multi-resource API with CRUD routes and schema validation.",
                deliverable="Interactive OpenAPI documentation running locally on your development server.",
                resources=cls._get_resources_for_skills(s3),
            ),
            RoadmapMilestone(
                week=4,
                title="Data Persistence, Sharding & Caching Strategies",
                focus_area=f"{', '.join(s4)} Storage Optimization",
                learning_objectives=[
                    "Connect application layer to relational and in-memory datastores.",
                    "Design relational schemas, indices, and connection pool configurations.",
                    "Implement in-memory caching to reduce response latency.",
                ],
                target_skills=s4,
                practical_exercise="Implement Redis caching for slow database queries with TTL invalidation.",
                deliverable="Performance benchmark report showing query latency before and after caching.",
                resources=cls._get_resources_for_skills(s4 + ["PostgreSQL", "Redis"]),
            ),
            RoadmapMilestone(
                week=5,
                title="Containerization & Cloud Infrastructure",
                focus_area=f"{', '.join(s5)} Infrastructure",
                learning_objectives=[
                    "Author secure, multi-stage Docker container images.",
                    "Configure local multi-container environments using Docker Compose.",
                    "Deploy services onto cloud platforms using foundational cloud services.",
                ],
                target_skills=s5,
                practical_exercise="Create a multi-service docker-compose setup connecting frontend, backend, and database.",
                deliverable="Compose file spinning up the entire stack with a single command.",
                resources=cls._get_resources_for_skills(s5 + ["Docker", "AWS"]),
            ),
            RoadmapMilestone(
                week=6,
                title="Automated CI/CD Pipelines & Quality Assurance",
                focus_area="CI/CD & Reliability",
                learning_objectives=[
                    "Configure automated GitHub Actions workflows for pull requests.",
                    "Run automated linters, security scanners, and pytest suites on every commit.",
                    "Measure code coverage and establish quality gates.",
                ],
                target_skills=s6,
                practical_exercise="Build a complete GitHub Actions YAML workflow that builds and tests on push.",
                deliverable="Green CI workflow badge in your repository with automated test execution.",
                resources=cls._get_resources_for_skills(["Git", "Linux"]),
            ),
            RoadmapMilestone(
                week=7,
                title="Multi-Tier Capstone Portfolio Project Implementation",
                focus_area=f"{target_role} Capstone Phase 1",
                learning_objectives=[
                    f"Integrate all 6 weeks of learning into an end-to-end application tailored for {target_role}.",
                    "Implement complete user workflows from user interface to database.",
                    "Conduct extensive load testing and handle edge cases.",
                ],
                target_skills=s7,
                practical_exercise="Build the core MVP of your capstone portfolio project with working data flow.",
                deliverable="Working MVP running locally with automated seed data generation scripts.",
                resources=cls._get_resources_for_skills(["General Web"]),
            ),
            RoadmapMilestone(
                week=8,
                title="Production Hardening, Code Review & Portfolio Deployment",
                focus_area=f"{target_role} Capstone Phase 2",
                learning_objectives=[
                    "Harden security: remove hardcoded secrets, configure CORS, and sanitize inputs.",
                    "Author professional README with architectural diagrams and setup guides.",
                    "Publish a public repository and live demo walkthrough for technical reviewers.",
                ],
                target_skills=s8,
                practical_exercise="Conduct an audit against standard OWASP guidelines and finalize portfolio documentation.",
                deliverable="Polished public portfolio repository with live demo links and architectural writeup.",
                resources=cls._get_resources_for_skills(["General Web", "Git"]),
            ),
        ]


# Singleton instance
_roadmap_service_instance: Optional[RoadmapService] = None


def get_roadmap_service() -> RoadmapService:
    """Return the singleton instance of RoadmapService."""
    global _roadmap_service_instance
    if _roadmap_service_instance is None:
        _roadmap_service_instance = RoadmapService()
    return _roadmap_service_instance
