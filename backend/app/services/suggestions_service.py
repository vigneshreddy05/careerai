"""
Resume Improvement Suggestions Engine for CareerAI.
Analyzes parsed resume structure to produce:
1. Deterministic Structural Readiness Score (0-100) with category breakdown.
2. Prioritized actionable improvement recommendations (High, Medium, Low).
3. Concrete before-and-after rewrite examples applying the XYZ impact formula.
4. ATS readability and keyword alignment checks.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from backend.app.schemas.suggestions import (
        ActionRewriteExample,
        CategoryScore,
        ResumeReadinessBreakdown,
        SuggestionItem,
        SuggestionsRequest,
        SuggestionsResponse,
        RESUME_READINESS_DISCLAIMER,
    )
    from backend.app.services.roadmap_service import ROLE_CATALOG
except ModuleNotFoundError:
    from app.schemas.suggestions import (
        ActionRewriteExample,
        CategoryScore,
        ResumeReadinessBreakdown,
        SuggestionItem,
        SuggestionsRequest,
        SuggestionsResponse,
        RESUME_READINESS_DISCLAIMER,
    )
    from app.services.roadmap_service import ROLE_CATALOG


# High-impact active action verbs
ACTION_VERBS = [
    "architected", "built", "engineered", "developed", "designed", "implemented",
    "optimized", "automated", "deployed", "spearheaded", "orchestrated",
    "streamlined", "accelerated", "refactored", "integrated", "trained",
    "delivered", "formulated", "configured", "mentored", "scaled", "reduced",
    "increased", "transformed", "established"
]

# Weak or passive phrases to avoid
PASSIVE_PHRASES = [
    r"\bresponsible for\b",
    r"\bhelped with\b",
    r"\bworked on\b",
    r"\bassisted (?:in|with)\b",
    r"\btasked with\b",
    r"\bhandled\b",
    r"\bparticipated in\b",
    r"\bduties included\b",
]

# Quantifiable metric patterns
METRIC_PATTERNS = [
    r"\b\d+(?:\.\d+)?%",                         # percentages (e.g. 35%, 99.9%)
    r"\b\d+(?:\.\d+)?x\b",                        # multipliers (e.g. 3x, 10x)
    r"\b\d+\s*(?:ms|seconds?|minutes?|hours?)\b",  # latency/time
    r"(?:\$|€|£|₹)\s*\d+",                        # currency/budget
    r"\b\d+(?:k|m|b)\+?\b",                       # abbreviated scale (e.g. 10k, 2M)
    r"\b\d+\+?\s*(?:users|requests|records|queries|datasets|concurrent|qps|endpoints|models|tests|clients|tables)\b", # entities
    r"\b[2-9]\d*\b",                              # integers >= 20
]

# Concrete before-and-after rewrite templates
CONCRETE_REWRITE_EXAMPLES = [
    ActionRewriteExample(
        context="Backend Engineering & API Development",
        before="Worked on backend APIs using Python and helped with database queries.",
        after="Architected 14 asynchronous RESTful endpoints in FastAPI with PostgreSQL and Redis caching, cutting average P95 query response time by 38% under 500 concurrent requests.",
        explanation="Uses the active verb 'Architected', explicitly identifies the tech stack (FastAPI, PostgreSQL, Redis), and quantifies performance impact (38% latency cut, 500 concurrent requests)."
    ),
    ActionRewriteExample(
        context="Frontend & Web Applications",
        before="Responsible for building frontend components in React and fixing UI bugs.",
        after="Engineered 18 modular, accessible React components with Tailwind CSS and Vite, improving Google Lighthouse accessibility score from 74 to 98 and cutting bundle size by 24%.",
        explanation="Replaces passive 'Responsible for' with 'Engineered', and quantifies results using standard benchmark metrics (Lighthouse 74->98, 24% bundle reduction)."
    ),
    ActionRewriteExample(
        context="Machine Learning & Data Science",
        before="Built a machine learning model to predict prices from data.",
        after="Trained and hyperparameter-tuned a LightGBM regression pipeline on 120,000 tabular records in Python, achieving an RMSE of 0.082 and outperforming the baseline heuristic by 19%.",
        explanation="Specifies the algorithm (LightGBM), data volume (120,000 records), and verifiable evaluation metrics (RMSE 0.082, 19% improvement)."
    ),
    ActionRewriteExample(
        context="Cloud & DevOps Infrastructure",
        before="Helped deploy applications using Docker and AWS.",
        after="Containerized 5 microservices using multi-stage Docker builds and automated continuous deployment with GitHub Actions to AWS ECS, reducing deployment lead time from 45 to 8 minutes.",
        explanation="Replaces 'Helped deploy' with 'Containerized' and 'automated', quantifying time savings (45 to 8 minutes) across 5 services."
    ),
]


class SuggestionsService:
    """Service to evaluate resume completeness and generate prioritized improvement recommendations."""

    @classmethod
    def analyze_resume_improvements(cls, request: SuggestionsRequest) -> SuggestionsResponse:
        """
        Evaluate candidate resume structure, contact information, bullet impact,
        skills alignment, and ATS readability to produce structured recommendations.
        """
        contact = request.contact_info or {}
        skills = request.skills or {}
        education = request.education or []
        experience = request.experience or {}
        projects = request.projects or []
        statistics = request.statistics or {}
        raw_text = request.extracted_text or ""
        target_role = request.target_role

        # Collect all extracted skills as normalized lowercase set
        all_skills = []
        if isinstance(skills, dict):
            all_skills = skills.get("all_skills", [])
            if not all_skills:
                for k, v in skills.items():
                    if isinstance(v, list):
                        all_skills.extend(v)
        all_skills_normalized = {s.strip().lower() for s in all_skills if isinstance(s, str) and s.strip()}

        # Collect all project & experience text snippets
        exp_entries = experience.get("entries", []) if isinstance(experience, dict) else []
        proj_entries = projects if isinstance(projects, list) else []

        bullet_texts: List[str] = []
        for e in exp_entries:
            if isinstance(e, dict) and e.get("description"):
                bullet_texts.append(e["description"])
        for p in proj_entries:
            if isinstance(p, dict):
                if p.get("description"):
                    bullet_texts.append(p["description"])
                if p.get("title"):
                    bullet_texts.append(p["title"])

        combined_exp_text = " ".join(bullet_texts)
        full_text_lower = (raw_text + " " + combined_exp_text).lower()

        suggestions: List[SuggestionItem] = []
        category_scores: List[CategoryScore] = []

        # =====================================================================
        # 1. Contact & Header Completeness (Max: 20 pts)
        # =====================================================================
        contact_pts = 0
        contact_issues = []

        # Email check (+8 pts)
        has_email = bool(contact.get("email")) or bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', raw_text))
        if has_email:
            contact_pts += 8
        else:
            contact_issues.append("Missing email address")
            suggestions.append(SuggestionItem(
                id="contact-email",
                category="Contact & Header",
                priority="High",
                title="Add a Professional Email Address",
                issue="No valid email address was detected in your resume header.",
                recommendation="Include a clear, professional email address (e.g., firstname.lastname@gmail.com) near the top of your resume.",
                action_type="add",
            ))

        # Phone check (+6 pts)
        has_phone = bool(contact.get("phone")) or bool(re.search(r'(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}', raw_text))
        if has_phone:
            contact_pts += 6
        else:
            contact_issues.append("Missing phone number")
            suggestions.append(SuggestionItem(
                id="contact-phone",
                category="Contact & Header",
                priority="High",
                title="Add a Direct Contact Number",
                issue="No phone number was identified in the resume contact section.",
                recommendation="Provide a reachable mobile phone number with your country/area code (e.g., +1 (555) 019-2834 or +91 98765 43210).",
                action_type="add",
            ))

        # Professional Links check (+6 pts: +3 for LinkedIn, +3 for GitHub/Portfolio)
        has_linkedin = bool(re.search(r'linkedin\.com/(?:in|company)/[a-zA-Z0-9_-]+', raw_text, re.IGNORECASE))
        has_github_portfolio = bool(re.search(r'(?:github\.com|gitlab\.com|kaggle\.com|behance\.net)/[a-zA-Z0-9_-]+|(?:https?://[a-zA-Z0-9_.-]+\.(?:dev|io|me|com|app))', raw_text, re.IGNORECASE))

        if has_linkedin:
            contact_pts += 3
        if has_github_portfolio:
            contact_pts += 3

        if not has_linkedin and not has_github_portfolio:
            suggestions.append(SuggestionItem(
                id="contact-links",
                category="Contact & Header",
                priority="Medium",
                title="Add LinkedIn & Technical Portfolio / GitHub Links",
                issue="Neither a LinkedIn profile URL nor a GitHub / portfolio website link was detected.",
                recommendation="Technical recruiters expect direct links to your LinkedIn profile and public code repositories (GitHub/GitLab) or live web portfolio.",
                action_type="add",
            ))
        elif not has_github_portfolio and len(all_skills_normalized) > 0:
            suggestions.append(SuggestionItem(
                id="contact-github",
                category="Contact & Header",
                priority="Medium",
                title="Include a GitHub or Project Repository Link",
                issue="Your resume lists technical skills, but no active GitHub, GitLab, or portfolio link was found.",
                recommendation="Add a clickable link to your GitHub profile or personal portfolio site so hiring managers can inspect real source code.",
                action_type="add",
            ))

        contact_pct = round((contact_pts / 20) * 100, 1)
        contact_status = "Complete" if contact_pts >= 17 else ("Needs Improvement" if contact_pts >= 10 else "Critical Gap")
        category_scores.append(CategoryScore(
            category="Contact & Header",
            score=contact_pts,
            max_score=20,
            percentage=contact_pct,
            status=contact_status,
            summary="All core contact details detected." if not contact_issues else f"Issues: {', '.join(contact_issues)}."
        ))

        # =====================================================================
        # 2. Impact & Action-Verb Bullet Quality (Max: 25 pts)
        # =====================================================================
        impact_pts = 0

        # Check for quantifiable metrics (+13 pts)
        has_metrics = False
        metrics_found_count = 0
        for pattern in METRIC_PATTERNS:
            matches = re.findall(pattern, combined_exp_text or raw_text, re.IGNORECASE)
            metrics_found_count += len(matches)

        if metrics_found_count >= 3:
            impact_pts += 13
            has_metrics = True
        elif metrics_found_count >= 1:
            impact_pts += 8
            has_metrics = True
        else:
            impact_pts += 2

        if not has_metrics or metrics_found_count < 2:
            suggestions.append(SuggestionItem(
                id="bullet-metrics",
                category="Impact & Action Verbs",
                priority="High",
                title="Quantify Project and Work Achievements (XYZ Formula)",
                issue="Bullet points appear descriptive rather than metric-driven; few or no quantifiable numbers, percentages, or scale metrics were found.",
                recommendation="Adopt the Google 'XYZ Formula': 'Accomplished [X], as measured by [Y], by doing [Z]'. Add percentages (e.g. 'reduced latency by 35%'), scale figures ('served 10,000+ users'), or throughput benchmarks.",
                action_type="rewrite",
                examples=[CONCRETE_REWRITE_EXAMPLES[0], CONCRETE_REWRITE_EXAMPLES[1]],
            ))

        # Check for active action verbs vs. passive phrases (+12 pts)
        action_verbs_found = [v for v in ACTION_VERBS if re.search(rf'\b{v}\b', full_text_lower)]
        passive_matches = []
        for p_pat in PASSIVE_PHRASES:
            found = re.findall(p_pat, full_text_lower)
            if found:
                passive_matches.extend(found)

        if len(action_verbs_found) >= 5:
            impact_pts += 12
        elif len(action_verbs_found) >= 2:
            impact_pts += 8
        else:
            impact_pts += 4

        if passive_matches:
            suggestions.append(SuggestionItem(
                id="bullet-passive-phrasing",
                category="Impact & Action Verbs",
                priority="Medium",
                title="Eliminate Passive Phrases ('Responsible for', 'Worked on')",
                issue=f"Detected passive phrasing ({', '.join(set(passive_matches[:3]))}) which diminishes the candidate's personal contribution.",
                recommendation="Replace passive expressions with decisive action verbs like 'Architected', 'Spearheaded', 'Engineered', 'Optimized', or 'Automated'.",
                action_type="rewrite",
                examples=[CONCRETE_REWRITE_EXAMPLES[1], CONCRETE_REWRITE_EXAMPLES[3]],
            ))
        elif len(action_verbs_found) < 3 and (exp_entries or proj_entries):
            suggestions.append(SuggestionItem(
                id="bullet-action-verbs",
                category="Impact & Action Verbs",
                priority="Medium",
                title="Lead Every Bullet with a Strong Action Verb",
                issue="Several bullet descriptions do not start with decisive engineering verbs.",
                recommendation="Begin every accomplishment bullet with past-tense power verbs such as 'Engineered', 'Designed', 'Refactored', or 'Accelerated'.",
                action_type="rewrite",
                examples=[CONCRETE_REWRITE_EXAMPLES[2]],
            ))

        impact_pct = round((impact_pts / 25) * 100, 1)
        impact_status = "Complete" if impact_pts >= 20 else ("Needs Improvement" if impact_pts >= 12 else "Critical Gap")
        category_scores.append(CategoryScore(
            category="Impact & Action Verbs",
            score=impact_pts,
            max_score=25,
            percentage=impact_pct,
            status=impact_status,
            summary=f"Detected {metrics_found_count} quantifiable metrics and {len(action_verbs_found)} action verbs."
        ))

        # =====================================================================
        # 3. Technical Skills & Keyword Organization (Max: 25 pts)
        # =====================================================================
        skills_pts = 0
        total_skills_count = len(all_skills_normalized)

        # Quantity of skills (+15 pts)
        if total_skills_count >= 10:
            skills_pts += 15
        elif total_skills_count >= 6:
            skills_pts += 11
        elif total_skills_count >= 3:
            skills_pts += 6
        else:
            skills_pts += 2

        if total_skills_count < 5:
            suggestions.append(SuggestionItem(
                id="skills-sparse",
                category="Skills & Keyword Organization",
                priority="High",
                title="Expand Technical Skills Inventory",
                issue=f"Only {total_skills_count} technical skill(s) were identified in the resume.",
                recommendation="Add a clear 'Technical Skills' section listing specific programming languages, frameworks, databases, and development tools you have worked with.",
                action_type="add",
            ))

        # Categorization / Diversity (+10 pts)
        cats_with_skills = 0
        if isinstance(skills, dict):
            for cat_key in ["programming_languages", "frameworks_and_libraries", "databases", "cloud_and_devops"]:
                if skills.get(cat_key) and len(skills[cat_key]) > 0:
                    cats_with_skills += 1

        if cats_with_skills >= 3:
            skills_pts += 10
        elif cats_with_skills >= 2:
            skills_pts += 7
        elif cats_with_skills >= 1:
            skills_pts += 4
        else:
            skills_pts += 2

        if cats_with_skills < 2 and total_skills_count >= 4:
            suggestions.append(SuggestionItem(
                id="skills-categorization",
                category="Skills & Keyword Organization",
                priority="Medium",
                title="Group Skills into Logical Categories",
                issue="Skills appear as an unsegmented list rather than organized functional clusters.",
                recommendation="Organize your skills into distinct subheadings: Languages (e.g. Python, TypeScript), Frameworks (e.g. React, FastAPI), Databases (e.g. PostgreSQL, Redis), and Tools/Cloud (e.g. Docker, Git, AWS).",
                action_type="reorganize",
            ))

        # Target Role Keyword Alignment check
        if target_role:
            matched_catalog_role = None
            target_role_lower = target_role.strip().lower()
            target_tokens = set(re.findall(r'\b[a-z]{3,}\b', target_role_lower))

            # 1. Exact match
            for r in ROLE_CATALOG:
                if r["role_title"].lower() == target_role_lower:
                    matched_catalog_role = r
                    break

            # 2. Substring match
            if not matched_catalog_role:
                for r in ROLE_CATALOG:
                    rt_lower = r["role_title"].lower()
                    if target_role_lower in rt_lower or rt_lower in target_role_lower:
                        matched_catalog_role = r
                        break

            # 3. Token overlap match
            if not matched_catalog_role and target_tokens:
                best_overlap = 0
                for r in ROLE_CATALOG:
                    role_tokens = set(re.findall(r'\b[a-z]{3,}\b', r["role_title"].lower()))
                    overlap = len(target_tokens & role_tokens)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_catalog_role = r

            if matched_catalog_role:
                core_skills = matched_catalog_role["core_skills"]
                missing_role_skills = [s for s in core_skills if s.strip().lower() not in all_skills_normalized]
                if missing_role_skills:
                    suggestions.append(SuggestionItem(
                        id="skills-target-role-alignment",
                        category="Skills & Keyword Organization",
                        priority="High",
                        title=f"Incorporate Missing Core Skills for '{matched_catalog_role['role_title']}'",
                        issue=f"Your resume does not explicitly mention these expected competencies: {', '.join(missing_role_skills[:5])}.",
                        recommendation=f"If you have hands-on experience or coursework with {', '.join(missing_role_skills[:3])}, add them to your skills inventory and reference them in relevant project bullet points.",
                        action_type="add",
                    ))
            elif request.custom_missing_skills and len(request.custom_missing_skills) > 0:
                missing_clean = [s for s in request.custom_missing_skills if s.strip().lower() not in all_skills_normalized]
                if missing_clean:
                    suggestions.append(SuggestionItem(
                        id="skills-target-role-alignment",
                        category="Skills & Keyword Organization",
                        priority="High",
                        title=f"Address Missing Skills for Target Role '{target_role}'",
                        issue=f"Key skills required for this role are absent from your resume: {', '.join(missing_clean[:5])}.",
                        recommendation="Incorporate matching skills into your skills list and describe how you have applied them or plan to learn them in your roadmap.",
                        action_type="add",
                    ))
        elif request.custom_missing_skills and len(request.custom_missing_skills) > 0:
            missing_clean = [s for s in request.custom_missing_skills if s.strip().lower() not in all_skills_normalized]
            if missing_clean:
                suggestions.append(SuggestionItem(
                    id="skills-custom-gap",
                    category="Skills & Keyword Organization",
                    priority="High",
                    title="Address Skill Gaps from Target Job Description",
                    issue=f"The job description highlights key skills absent from your resume: {', '.join(missing_clean[:5])}.",
                    recommendation="Incorporate matching skills into your skills list and describe how you have applied them or plan to learn them in your roadmap.",
                    action_type="add",
                ))

        skills_pct = round((skills_pts / 25) * 100, 1)
        skills_status = "Complete" if skills_pts >= 20 else ("Needs Improvement" if skills_pts >= 12 else "Critical Gap")
        category_scores.append(CategoryScore(
            category="Skills & Keyword Organization",
            score=skills_pts,
            max_score=25,
            percentage=skills_pct,
            status=skills_status,
            summary=f"Identified {total_skills_count} total skills across {cats_with_skills} technology categories."
        ))

        # =====================================================================
        # 4. Projects & Experience Presentation (Max: 18 pts)
        # =====================================================================
        proj_exp_pts = 0
        has_experience = len(exp_entries) > 0
        has_projects = len(proj_entries) > 0

        if has_experience and has_projects:
            proj_exp_pts += 18
        elif has_experience:
            proj_exp_pts += 13
            # Suggest adding projects to showcase modern stack
            suggestions.append(SuggestionItem(
                id="projects-add-capstone",
                category="Projects & Experience",
                priority="Medium",
                title="Showcase Standalone or Capstone Projects",
                issue="Work experience is present, but no dedicated project portfolio section was found.",
                recommendation="Add 1-2 featured projects highlighting end-to-end architecture, tools used, and links to public repositories or live deployments.",
                action_type="add",
            ))
        elif has_projects:
            proj_exp_pts += 14
        else:
            proj_exp_pts += 3
            suggestions.append(SuggestionItem(
                id="projects-experience-missing",
                category="Projects & Experience",
                priority="High",
                title="Add Practical Projects or Work Experience",
                issue="Neither professional employment experience nor structured project entries were detected.",
                recommendation="Create a 'Projects' section featuring 2-3 substantial technical projects. For each project, state the problem solved, tech stack used, and your measurable results.",
                action_type="add",
            ))

        # Check if project entries have technology tags
        projects_lacking_tech = [
            p.get("title", "Project") for p in proj_entries
            if isinstance(p, dict) and (not p.get("technologies") or len(p["technologies"]) == 0)
        ]
        if projects_lacking_tech and has_projects:
            suggestions.append(SuggestionItem(
                id="projects-tag-tech-stack",
                category="Projects & Experience",
                priority="Medium",
                title="Explicitly Tag Technologies Used in Projects",
                issue=f"Projects ({', '.join(projects_lacking_tech[:2])}) do not clearly list their underlying tech stack.",
                recommendation="Include a clear 'Technologies: [Tool 1, Tool 2, Framework 3]' sub-line under each project title so recruiters and ATS scrapers can quickly index them.",
                action_type="rewrite",
            ))

        proj_pct = round((proj_exp_pts / 18) * 100, 1)
        proj_status = "Complete" if proj_exp_pts >= 15 else ("Needs Improvement" if proj_exp_pts >= 9 else "Critical Gap")
        category_scores.append(CategoryScore(
            category="Projects & Experience",
            score=proj_exp_pts,
            max_score=18,
            percentage=proj_pct,
            status=proj_status,
            summary=f"Found {len(exp_entries)} experience entry(ies) and {len(proj_entries)} project entry(ies)."
        ))

        # =====================================================================
        # 5. ATS Readability & Formatting (Max: 12 pts)
        # =====================================================================
        ats_pts = 0
        word_count = statistics.get("word_count", 0) if isinstance(statistics, dict) else len(raw_text.split())

        # Word count evaluation (+6 pts)
        if 350 <= word_count <= 950:
            ats_pts += 6
        elif 200 <= word_count < 350:
            ats_pts += 4
            suggestions.append(SuggestionItem(
                id="ats-word-count-short",
                category="ATS Readability & Formatting",
                priority="Medium",
                title="Expand Resume Detail and Scope (Under 350 Words)",
                issue=f"Total document length is {word_count} words, which may appear thin or incomplete to ATS screening algorithms.",
                recommendation="Flesh out project descriptions, technical responsibilities, and key accomplishments to reach a typical single-page density of 400-700 words.",
                action_type="rewrite",
            ))
        elif word_count > 1200:
            ats_pts += 3
            suggestions.append(SuggestionItem(
                id="ats-word-count-long",
                category="ATS Readability & Formatting",
                priority="Low",
                title="Streamline Content to 1-2 Focused Pages (Over 1,200 Words)",
                issue=f"Total document length is {word_count} words. Extended resumes risk recruiter fatigue during initial 6-second scans.",
                recommendation="Trim verbose bullet points, eliminate redundant duties, and focus strictly on high-impact accomplishments within the last 3-5 years.",
                action_type="rewrite",
            ))
        else:
            ats_pts += 2
            if word_count < 200:
                suggestions.append(SuggestionItem(
                    id="ats-word-count-critical",
                    category="ATS Readability & Formatting",
                    priority="High",
                    title="Substantially Expand Resume Content",
                    issue=f"Extracted resume contains only {word_count} words. Crucial sections may be omitted or unreadable.",
                    recommendation="Ensure your resume is formatted with selectable text (not scanned images) and contains comprehensive education, skills, and project sections.",
                    action_type="add",
                ))

        # Section balance check (+6 pts)
        has_education = len(education) > 0
        sections_present = sum([
            1 if has_email or has_phone else 0,
            1 if total_skills_count > 0 else 0,
            1 if has_education else 0,
            1 if has_experience or has_projects else 0,
        ])

        if sections_present == 4:
            ats_pts += 6
        elif sections_present >= 3:
            ats_pts += 4
        else:
            ats_pts += 2

        if not has_education:
            suggestions.append(SuggestionItem(
                id="education-missing",
                category="ATS Readability & Formatting",
                priority="High",
                title="Add an Education Section",
                issue="No recognized university degree, diploma, or educational qualification was detected.",
                recommendation="Add an 'Education' section stating your degree title (e.g. B.Tech Computer Science), institution name, graduation year, and GPA/percentage.",
                action_type="add",
            ))

        ats_pct = round((ats_pts / 12) * 100, 1)
        ats_status = "Complete" if ats_pts >= 10 else ("Needs Improvement" if ats_pts >= 6 else "Critical Gap")
        category_scores.append(CategoryScore(
            category="ATS Readability & Formatting",
            score=ats_pts,
            max_score=12,
            percentage=ats_pct,
            status=ats_status,
            summary=f"Document length: {word_count} words across {sections_present}/4 standard ATS sections."
        ))

        # =====================================================================
        # Overall Readiness Score Calculation
        # =====================================================================
        total_score = contact_pts + impact_pts + skills_pts + proj_exp_pts + ats_pts
        total_score = max(0, min(100, total_score))

        if total_score >= 85:
            readiness_tier = "Strong Structural Foundation"
        elif total_score >= 60:
            readiness_tier = "Moderate Completeness"
        else:
            readiness_tier = "Requires Significant Improvement"

        # Prioritize suggestions: High -> Medium -> Low
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

        summary = {
            "total": len(suggestions),
            "high": sum(1 for s in suggestions if s.priority == "High"),
            "medium": sum(1 for s in suggestions if s.priority == "Medium"),
            "low": sum(1 for s in suggestions if s.priority == "Low"),
        }

        readiness_breakdown = ResumeReadinessBreakdown(
            overall_score=total_score,
            readiness_tier=readiness_tier,
            disclaimer=RESUME_READINESS_DISCLAIMER,
            category_scores=category_scores,
        )

        return SuggestionsResponse(
            success=True,
            readiness_score=readiness_breakdown,
            suggestions=suggestions,
            summary=summary,
            target_role=target_role,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )
