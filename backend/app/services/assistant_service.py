"""
AI Career Assistant Service for CareerAI.
Integrates:
1. Local Ollama LLM runtime (Qwen 2.5 3B) via httpx async client.
2. Intelligent, context-aware Guided Career Advisor (instant CPU fallback).
3. Strict ethical guardrails preventing score alteration or hiring promises.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

try:
    from backend.app.core.config import settings
    from backend.app.schemas.assistant import (
        AssistantChatRequest,
        AssistantChatResponse,
        AssistantContextPayload,
        AssistantStatusResponse,
        ChatMessage,
        ASSISTANT_ETHICAL_DISCLAIMER,
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.schemas.assistant import (
        AssistantChatRequest,
        AssistantChatResponse,
        AssistantContextPayload,
        AssistantStatusResponse,
        ChatMessage,
        ASSISTANT_ETHICAL_DISCLAIMER,
    )

logger = logging.getLogger(__name__)

# Timeout configuration for local Ollama calls
OLLAMA_STATUS_TIMEOUT = 1.5  # seconds for health check
OLLAMA_CHAT_TIMEOUT = 20.0   # seconds for chat generation


class AssistantService:
    """Service orchestrating conversational mentorship with local Ollama and CPU-guided fallback."""

    @staticmethod
    async def check_ollama_status() -> AssistantStatusResponse:
        """
        Probe local Ollama daemon on 127.0.0.1:11434 with a fast 1.5s timeout.
        Returns connection state and available model tags.
        """
        tags_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=OLLAMA_STATUS_TIMEOUT) as client:
                res = await client.get(tags_url)
                if res.status_code == 200:
                    data = res.json()
                    models_list = data.get("models", [])
                    available_model_names = [m.get("name", "") for m in models_list if m.get("name")]
                    return AssistantStatusResponse(
                        ollama_available=True,
                        ollama_base_url=settings.OLLAMA_BASE_URL,
                        configured_model=settings.OLLAMA_MODEL,
                        available_models=available_model_names,
                        status="connected",
                    )
        except Exception as exc:
            logger.debug(f"Local Ollama probe offline ({settings.OLLAMA_BASE_URL}): {exc}")

        return AssistantStatusResponse(
            ollama_available=False,
            ollama_base_url=settings.OLLAMA_BASE_URL,
            configured_model=settings.OLLAMA_MODEL,
            available_models=[],
            status="offline",
        )

    @classmethod
    async def process_chat_message(cls, request: AssistantChatRequest) -> AssistantChatResponse:
        """
        Process user message using local Ollama if available and requested,
        or gracefully fall back to the deterministic Guided Career Advisor engine.
        """
        user_message = request.message.strip()
        context = request.context or AssistantContextPayload()

        # 1. Attempt local Ollama inference if requested
        if request.use_local_llm:
            status = await cls.check_ollama_status()
            if status.ollama_available:
                try:
                    ollama_reply = await cls._invoke_ollama(
                        message=user_message,
                        history=request.conversation_history,
                        context=context,
                    )
                    if ollama_reply:
                        followups = cls._generate_followups(user_message, context)
                        return AssistantChatResponse(
                            success=True,
                            reply=ollama_reply,
                            engine_used=f"ollama:{settings.OLLAMA_MODEL}",
                            ollama_available=True,
                            suggested_followups=followups,
                            disclaimer=ASSISTANT_ETHICAL_DISCLAIMER,
                        )
                except Exception as exc:
                    logger.warning(f"Ollama generation failed or timed out: {exc}. Falling back to Guided Advisor.")

        # 2. Guided Career Advisor Fallback (Instant CPU Execution)
        guided_reply, followups = cls.generate_guided_response(
            message=user_message,
            context=context,
            history=request.conversation_history,
        )

        return AssistantChatResponse(
            success=True,
            reply=guided_reply,
            engine_used="careerai-guided-advisor",
            ollama_available=False,
            suggested_followups=followups,
            disclaimer=ASSISTANT_ETHICAL_DISCLAIMER,
        )

    @classmethod
    async def _invoke_ollama(
        cls,
        message: str,
        history: List[ChatMessage],
        context: AssistantContextPayload,
    ) -> Optional[str]:
        """Send grounded prompt and history to local Ollama /api/chat endpoint."""
        system_prompt = cls._build_grounded_system_prompt(context)
        chat_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"

        # Trim conversation history to last 6 messages
        recent_history = history[-6:] if history else []
        messages = [{"role": "system", "content": system_prompt}]
        for turn in recent_history:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 512,
            },
        }

        async with httpx.AsyncClient(timeout=OLLAMA_CHAT_TIMEOUT) as client:
            res = await client.post(chat_url, json=payload)
            if res.status_code == 200:
                data = res.json()
                content = data.get("message", {}).get("content", "").strip()
                if content:
                    return content
        return None

    @staticmethod
    def _build_grounded_system_prompt(context: AssistantContextPayload) -> str:
        """Construct concise, grounded system prompt without PII."""
        skills_str = ", ".join(context.detected_skills[:12]) if context.detected_skills else "None specified"
        missing_str = ", ".join(context.missing_skills[:8]) if context.missing_skills else "None identified"
        domain_str = (
            f"{context.top_predicted_domain} ({round(context.top_prediction_confidence * 100, 1)}% confidence)"
            if context.top_predicted_domain and context.top_prediction_confidence is not None
            else (context.top_predicted_domain or "Not evaluated yet")
        )

        return (
            "You are CareerAI Assistant, an expert, pragmatic technical career mentor. "
            "Your guidance must be strictly grounded in the candidate's verified profile:\n"
            f"- Verified Candidate Skills: {skills_str}\n"
            f"- Target Career Role: {context.target_role or 'Not selected'}\n"
            f"- Identified Missing Skills / Skill Gaps: {missing_str}\n"
            f"- DistilBERT Predicted Domain: {domain_str}\n"
            f"- Active Roadmap Duration: {context.roadmap_duration or 'Not generated'}\n"
            f"- Resume Structural Readiness: {context.readiness_score or 'N/A'}/100\n\n"
            "STRICT RULES:\n"
            "1. Never invent or alter DistilBERT confidence percentages or Sentence-BERT similarity scores.\n"
            "2. Never claim hiring probabilities or promise job offers.\n"
            "3. Format answers with clear Markdown headings, concise bullet points, and practical action items.\n"
            "4. Keep replies under 300 words for readability."
        )

    @classmethod
    def generate_guided_response(
        cls,
        message: str,
        context: AssistantContextPayload,
        history: Optional[List[ChatMessage]] = None,
    ) -> Tuple[str, List[str]]:
        """
        Intelligent, context-aware deterministic career advisor engine.
        Delivers immediate, rich, grounded advice when Ollama is offline or on CPU mode.
        """
        msg_lower = message.lower()
        skills = context.detected_skills or []
        missing = context.missing_skills or []
        role = context.target_role or "Software Engineering"
        domain = context.top_predicted_domain
        skills_sample = ", ".join(skills[:5]) if skills else "Python, Git, and web technologies"
        missing_sample = ", ".join(missing[:4]) if missing else "system architecture and testing"

        # ---------------------------------------------------------------------
        # Intent 1: Skill Gaps & What to Learn First
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "missing skill", "skill gap", "what should i learn", "learn first",
            "priority", "where to start", "bridge gap", "skills to learn", "which skill"
        ]):
            if missing:
                reply = (
                    f"### Strategic Learning Plan for **{role}**\n\n"
                    f"Based on your resume audit, you have strong foundations in **{skills_sample}**. "
                    f"To bridge the gap for **{role}**, here is your recommended 3-tier learning sequence:\n\n"
                    f"1. **Primary High-Impact Competency: `{missing[0]}`**\n"
                    f"   * *Why:* Core prerequisite frequently evaluated in technical screens for this role.\n"
                    f"   * *Action:* Complete official tutorials, build a mini demo, and write unit tests.\n\n"
                )
                if len(missing) > 1:
                    reply += (
                        f"2. **Secondary Framework/Data Layer: `{missing[1]}`**\n"
                        f"   * *Why:* Demonstrates end-to-end full-stack or data pipeline integration capability.\n"
                        f"   * *Action:* Integrate it into a project that connects with your existing stack ({skills[0] if skills else 'Python'}).\n\n"
                    )
                if len(missing) > 2:
                    reply += (
                        f"3. **Production Tooling & Best Practices: `{', '.join(missing[2:4])}`**\n"
                        f"   * *Why:* Differentiates junior candidates by showing awareness of deployment, containerization, and reliability.\n\n"
                    )
                reply += (
                    "**Recommended Next Step:** Dedicate 70% of your study time to building hands-on deliverables rather than passively watching video tutorials."
                )
            else:
                reply = (
                    f"### Skill Alignment Assessment for **{role}**\n\n"
                    f"Your resume already covers key foundational skills (**{skills_sample}**)! "
                    "To elevate your profile further:\n\n"
                    "1. **Deepen System Architecture:** Focus on asynchronous patterns, caching (Redis), and connection pooling.\n"
                    "2. **Production Observability:** Add structured logging, automated health checks, and CI/CD pipelines.\n"
                    "3. **Testing Coverage:** Target 80%+ unit and integration test coverage using PyTest or Jest."
                )

            followups = [
                f"Suggest a portfolio project combining {skills[0] if skills else 'my stack'} and {missing[0] if missing else 'Docker'}",
                f"What interview questions should I expect on {missing[0] if missing else role}?",
                "How do I structure my weekly learning schedule?",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Intent 2: Portfolio & Project Ideas
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "portfolio", "project idea", "what project", "capstone", "build a project",
            "project to show", "side project", "project concepts"
        ]):
            lead_skill = skills[0] if skills else "Python"
            target_skill = missing[0] if missing else "FastAPI"

            reply = (
                f"### High-Impact Portfolio Projects for **{role}**\n\n"
                f"Recruiters look for projects demonstrating end-to-end ownership, quantifiable performance, and clean code. "
                f"Here are two production-grade concepts leveraging your background in **{lead_skill}**:\n\n"
                f"#### Project 1: Asynchronous API & Data Service (`{lead_skill}` + `{target_skill}`)\n"
                f"* **What to Build:** A high-throughput RESTful service (e.g., job tracking, telemetry ingestion, or financial ledger) with token authentication and rate limiting.\n"
                f"* **Architecture:** REST API endpoints, relational persistence with PostgreSQL, Redis cache layer, and automated PyTest suite.\n"
                f"* **Recruiter Pitch:** *'Engineered a rate-limited REST API handling 500 concurrent requests with sub-50ms P95 latency.'*\n\n"
                f"#### Project 2: Real-Time Analytics Dashboard\n"
                f"* **What to Build:** Interactive analytics dashboard with live search, filtering, and chart visualization.\n"
                f"* **Key Highlight:** Include a comprehensive `README.md` with an architecture diagram, setup instructions in Docker Compose, and unit test badges."
            )
            followups = [
                f"How should I write resume bullet points for this {lead_skill} project?",
                "How do I document this project to impress hiring managers on GitHub?",
                f"What are the common architecture mistakes in {role} projects?",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Intent 3: Resume Bullets & Google XYZ Formula
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "resume bullet", "xyz formula", "how to write bullet", "bullet point",
            "improve resume", "ats tip", "action verb", "passive phrase"
        ]):
            lead_skill = skills[0] if skills else "Python"
            reply = (
                "### Mastering the Google XYZ Resume Formula\n\n"
                "The most impactful way to frame technical accomplishments is Google's **XYZ Formula**:\n\n"
                "> **Accomplished [X], as measured by [Y], by doing [Z]**\n\n"
                "#### Comparison Example:\n"
                f"* **Passive (Weak):** *'Worked on backend APIs using {lead_skill} and fixed bugs.'*\n"
                f"* **Metric-Driven (Strong):** *'Architected 12 asynchronous REST endpoints in {lead_skill} with Redis caching, cutting average query latency by 35% under 500 concurrent requests.'*\n\n"
                "#### 3 Rules for High-Impact Technical Bullets:\n"
                "1. **Lead with Active Power Verbs:** Use *Architected, Engineered, Optimized, Automated, Containerized* (avoid *Responsible for, Helped with*).\n"
                "2. **Quantify Results:** Include numbers, percentages, query times, or user counts.\n"
                "3. **Name Technologies Explicitly:** Don't just say *'used databases'*; state *'PostgreSQL indexing and Redis caching'*."
            )
            followups = [
                "How can I quantify my work if I didn't measure performance in production?",
                "How do I categorize my skills section for ATS readability?",
                f"Give me another example bullet for {role}",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Intent 4: Interview Preparation & Technical Questions
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "interview", "mock question", "technical question", "prepare for interview",
            "interview prep", "coding question", "behavioral"
        ]):
            primary_topic = skills[0] if skills else role
            reply = (
                f"### Technical Interview Preparation Matrix for **{role}**\n\n"
                f"For candidates with experience in **{skills_sample}**, technical interviews typically divide into 3 core evaluation stages:\n\n"
                f"#### 1. Core Technical Fundamentals ({primary_topic})\n"
                f"* *Sample Question:* 'How does asynchronous I/O differ from multi-threading, and when would you choose one over the other in {primary_topic}?'\n"
                f"* *What Interviewers Want:* Clear grasp of event loops, GIL/concurrency limits, and non-blocking I/O.\n\n"
                f"#### 2. System Design & Architectural Tradeoffs\n"
                f"* *Sample Question:* 'How would you design a caching strategy for high-read, low-write API endpoints, and how do you handle cache invalidation?'\n"
                f"* *What Interviewers Want:* Knowledge of Redis/Memcached, Cache-Aside pattern, and TTL strategies.\n\n"
                f"#### 3. Behavioral & Debugging (STAR Method)\n"
                f"* *Sample Question:* 'Describe a challenging bug you encountered in a recent project. How did you isolate the root cause?'\n"
                f"* *What Interviewers Want:* Structured response following Situation -> Task -> Action -> Result."
            )
            followups = [
                f"How should I answer the asynchronous I/O question for {primary_topic}?",
                "Can you provide a sample STAR behavioral answer?",
                f"What are the top 5 questions asked for junior {role} positions?",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Intent 5: Roadmap Execution & Milestones
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "roadmap", "schedule", "how many hours", "30 day", "60 day",
            "study plan", "routine", "burnout", "pace", "milestone"
        ]):
            duration = context.roadmap_duration or "30-day"
            reply = (
                f"### Executing Your **{duration}** Learning Roadmap\n\n"
                "Consistency and tangible milestones are much more valuable than cramming hours. "
                "Here is how to structure your learning for maximum retention:\n\n"
                "#### Suggested Time Allocation:\n"
                f"* **Pacing:** Aim for 12–15 focused hours per week (approx. 2 hours on weekdays, 3-4 hours on one weekend day).\n"
                "* **The 70 / 20 / 10 Framework:**\n"
                "  * **70% Hands-on Coding:** Writing tests, building features, debugging errors.\n"
                "  * **20% Official Documentation:** Reading official guides and best-practice patterns.\n"
                "  * **10% High-Level Concepts:** Architectural overviews and design patterns.\n\n"
                "#### Milestone Checkpoint Rule:\n"
                "At the end of every week, commit working, tested code to GitHub. If a milestone produces no commit, break the task into smaller sub-tasks."
            )
            followups = [
                "Should I pick a 30-day intensive or 60-day comprehensive roadmap?",
                f"What should my Week 1 milestone look like for {role}?",
                "How do I prevent burnout while studying alongside work?",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Intent 6: Explaining Scores & Model Predictions
        # ---------------------------------------------------------------------
        if any(k in msg_lower for k in [
            "explain score", "what is distilbert", "what is sentence-bert",
            "confidence percentage", "similarity score", "readiness score", "meaning of score"
        ]):
            reply = (
                "### Understanding CareerAI Evaluation Scores\n\n"
                "CareerAI uses decoupled mathematical models to evaluate different dimensions of your profile:\n\n"
                "1. **DistilBERT Classification Confidence (Job Prediction):**\n"
                "   * *What it is:* A fine-tuned transformer predicting categorical fit across 24 career domains via a softmax probability distribution.\n"
                "   * *Important:* A 75% score means the model's text classifier assigns 75% relative probability to that category; it is **NOT** a 75% probability of getting hired.\n\n"
                "2. **Sentence-BERT Cosine Similarity (Semantic Matching):**\n"
                "   * *What it is:* Dense 384-dimensional document embedding comparison measuring contextual semantic alignment between your resume and a target job description.\n\n"
                "3. **Skill Coverage Matrix (Deterministic):**\n"
                "   * *What it is:* Direct keyword intersection showing exactly which required technical skills appear in your resume.\n\n"
                "4. **Resume Structural Readiness (0–100):**\n"
                "   * *What it is:* A completeness heuristic evaluating contact info, quantifiable metrics, section balance, and ATS readability."
            )
            followups = [
                "How do I raise my Sentence-BERT semantic matching score?",
                "What can I do if my DistilBERT top score is low?",
                "How do I improve my resume completeness score?",
            ]
            return reply, followups

        # ---------------------------------------------------------------------
        # Default / Broad Career Inquiry
        # ---------------------------------------------------------------------
        readiness_part = f"with a structural completeness score of **{context.readiness_score}/100**" if context.readiness_score else ""
        domain_part = f"Your profile strongly aligns with **{domain}**." if domain else ""

        reply = (
            f"### CareerAI Advisory Summary for **{role}**\n\n"
            f"Hello! I am your local CareerAI Assistant. {domain_part}\n\n"
            f"**Current Profile Overview:**\n"
            f"* **Verified Skills:** {skills_sample}\n"
            f"* **Target Role:** {role}\n"
            f"* **Identified Growth Areas:** {missing_sample}\n\n"
            "**Recommended Next Steps:**\n"
            "1. **Bridge Missing Competencies:** Focus on your top missing skill through targeted project deliverables.\n"
            "2. **Quantify Resume Accomplishments:** Ensure your project descriptions follow the Google XYZ formula.\n"
            "3. **Execute Weekly Milestones:** Build a standalone repository showcasing end-to-end implementation.\n\n"
            "Feel free to ask about project ideas, interview questions, resume rewrites, or learning roadmaps!"
        )

        followups = [
            f"How should I tackle my top missing skills for {role}?",
            f"Suggest a portfolio project using my {skills[0] if skills else 'current'} skills",
            "How do I improve my resume bullet points using the XYZ formula?",
        ]
        return reply, followups
