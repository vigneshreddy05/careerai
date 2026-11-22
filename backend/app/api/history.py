"""
Prediction & Resume Analysis History API Router.
Implements:
- POST   /api/history/save       (Persist/sync session snapshot respecting privacy)
- GET    /api/history            (List saved records newest-first)
- GET    /api/history/{id}       (Retrieve full historical snapshot with ownership check)
- DELETE /api/history/{id}       (Delete individual record with ownership check)
- DELETE /api/history            (Clear all history for authenticated user)
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

try:
    from backend.app.schemas.history import (
        HistorySaveRequest,
        HistoryItemSummary,
        HistoryListResponse,
        HistoryDetailResponse,
        HistorySaveResponse,
        HistoryActionResponse,
        HistoryAnalyticsResponse,
        SkillFrequencyItem,
        DomainDistributionItem,
        ScoreProgressionItem,
    )
    from backend.app.core.database import get_db, DatabaseManager
    from backend.app.core.security import get_current_user
except ModuleNotFoundError:
    from app.schemas.history import (
        HistorySaveRequest,
        HistoryItemSummary,
        HistoryListResponse,
        HistoryDetailResponse,
        HistorySaveResponse,
        HistoryActionResponse,
        HistoryAnalyticsResponse,
        SkillFrequencyItem,
        DomainDistributionItem,
        ScoreProgressionItem,
    )
    from app.core.database import get_db, DatabaseManager
    from app.core.security import get_current_user

router = APIRouter()


@router.post(
    "/save",
    response_model=HistorySaveResponse,
    summary="Save or sync current analysis session snapshot"
)
async def save_history_record(
    payload: HistorySaveRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Persist structured analysis session snapshot for the authenticated candidate.
    Enforces user's save_resume_text privacy preference: raw resume text is only
    saved if the user explicitly opted in.
    """
    user_id = current_user["id"]
    save_resume_text = bool(current_user.get("save_resume_text", False))

    saved = db.save_history_record(
        user_id=user_id,
        data=payload.model_dump(),
        allow_save_text=save_resume_text
    )

    return HistorySaveResponse(
        success=True,
        record_id=saved["id"],
        message="Resume analysis record persisted successfully."
    )


@router.get(
    "",
    response_model=HistoryListResponse,
    summary="List past analysis records for current user"
)
async def list_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieve all saved analysis records for the authenticated candidate, ordered newest first."""
    records = db.list_history_records(current_user["id"])

    summaries: List[HistoryItemSummary] = []
    for r in records:
        skills_obj = r.get("skills") or {}
        all_skills = skills_obj.get("all_skills") or []
        skill_count = len(all_skills) if isinstance(all_skills, list) else 0

        # Top prediction extraction
        top_pred = r.get("top_prediction") or {}
        top_role = top_pred.get("category")
        top_conf = top_pred.get("confidence")
        if not top_role and "predictions" in top_pred and isinstance(top_pred["predictions"], list) and len(top_pred["predictions"]) > 0:
            top_role = top_pred["predictions"][0].get("category")
            top_conf = top_pred["predictions"][0].get("confidence")

        # Latest match extraction
        match_obj = r.get("latest_match") or {}
        latest_job_title = match_obj.get("job_title")
        latest_match_score = match_obj.get("semantic_score") or match_obj.get("match_percentage")

        # Latest roadmap extraction
        roadmap_obj = r.get("latest_roadmap") or {}
        target_roadmap_role = roadmap_obj.get("role_title") or roadmap_obj.get("target_role")

        summaries.append(
            HistoryItemSummary(
                id=r["id"],
                user_id=r["user_id"],
                filename=r["filename"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                skill_count=skill_count,
                top_role=top_role,
                top_confidence=top_conf,
                latest_job_title=latest_job_title,
                latest_match_score=latest_match_score,
                target_roadmap_role=target_roadmap_role,
                has_extracted_text=bool(r.get("extracted_text")),
            )
        )

    return HistoryListResponse(
        success=True,
        records=summaries,
        total=len(summaries)
    )


@router.get(
    "/analytics",
    response_model=HistoryAnalyticsResponse,
    summary="Retrieve aggregated analytics and score progressions across user history"
)
async def get_history_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Aggregates real statistics across saved analyses for dashboard charts and metrics."""
    records = db.list_history_records(current_user["id"])
    if not records:
        return HistoryAnalyticsResponse(
            success=True,
            total_analyses=0,
            unique_skills_count=0,
            top_skills=[],
            domain_distribution=[],
            score_progression=[],
            latest_analysis=None
        )

    total_analyses = len(records)
    skill_counts: Dict[str, int] = {}
    domain_counts: Dict[str, int] = {}
    score_progression: List[ScoreProgressionItem] = []

    # Records are newest-first; for progression chart we reverse so it is chronological (oldest to newest)
    for r in reversed(records):
        # Skills aggregation
        skills_obj = r.get("skills") or {}
        all_skills = skills_obj.get("all_skills") or []
        if isinstance(all_skills, list):
            for s in all_skills:
                s_clean = str(s).strip()
                if s_clean:
                    skill_counts[s_clean] = skill_counts.get(s_clean, 0) + 1

        # Domain aggregation
        top_pred = r.get("top_prediction") or {}
        top_role = top_pred.get("category")
        top_conf = top_pred.get("confidence")
        if not top_role and "predictions" in top_pred and isinstance(top_pred["predictions"], list) and len(top_pred["predictions"]) > 0:
            top_role = top_pred["predictions"][0].get("category")
            top_conf = top_pred["predictions"][0].get("confidence")

        if top_role:
            domain_counts[top_role] = domain_counts.get(top_role, 0) + 1

        # Match extraction
        match_obj = r.get("latest_match") or {}
        semantic_score = match_obj.get("semantic_score")
        if semantic_score is None and "semantic_match" in match_obj and isinstance(match_obj["semantic_match"], dict):
            semantic_score = match_obj["semantic_match"].get("similarity_score")

        skill_coverage = match_obj.get("match_percentage")
        if skill_coverage is None and "skill_match" in match_obj and isinstance(match_obj["skill_match"], dict):
            skill_coverage = match_obj["skill_match"].get("match_percentage")

        # Readiness score extraction from full snapshot if present
        readiness_score = None
        snap = r.get("full_snapshot") or {}
        if isinstance(snap, dict):
            sugg_data = snap.get("suggestionsData") or {}
            if isinstance(sugg_data, dict):
                readiness_score = sugg_data.get("readiness_score", {}).get("overall_score")

        raw_date = r.get("created_at", "")
        display_date = raw_date[:10] if len(raw_date) >= 10 else "N/A"

        conf_pct = None
        if top_conf is not None:
            conf_pct = round(top_conf * 100, 1) if top_conf <= 1.0 else round(top_conf, 1)

        sem_pct = None
        if semantic_score is not None:
            sem_pct = round(semantic_score * 100, 1) if semantic_score <= 1.0 else round(semantic_score, 1)

        score_progression.append(
            ScoreProgressionItem(
                record_id=r["id"],
                date=display_date,
                filename=r["filename"],
                top_role=top_role,
                top_confidence=conf_pct,
                semantic_score=sem_pct,
                skill_coverage=skill_coverage,
                readiness_score=readiness_score
            )
        )

    # Top skills sorted by frequency
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    top_skills = [
        SkillFrequencyItem(skill=k, count=v) for k, v in sorted_skills[:12]
    ]

    # Domain distribution
    domain_distribution = [
        DomainDistributionItem(domain=k, count=v, percentage=round((v / total_analyses) * 100, 1))
        for k, v in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Latest analysis summary
    latest_rec = records[0]
    latest_skills = latest_rec.get("skills") or {}
    latest_all_skills = latest_skills.get("all_skills") or []
    latest_top_pred = latest_rec.get("top_prediction") or {}
    latest_top_role = latest_top_pred.get("category")
    latest_top_conf = latest_top_pred.get("confidence")
    if not latest_top_role and "predictions" in latest_top_pred and isinstance(latest_top_pred["predictions"], list) and len(latest_top_pred["predictions"]) > 0:
        latest_top_role = latest_top_pred["predictions"][0].get("category")
        latest_top_conf = latest_top_pred["predictions"][0].get("confidence")

    latest_match_obj = latest_rec.get("latest_match") or {}
    latest_summary = HistoryItemSummary(
        id=latest_rec["id"],
        user_id=latest_rec["user_id"],
        filename=latest_rec["filename"],
        created_at=latest_rec["created_at"],
        updated_at=latest_rec["updated_at"],
        skill_count=len(latest_all_skills) if isinstance(latest_all_skills, list) else 0,
        top_role=latest_top_role,
        top_confidence=latest_top_conf,
        latest_job_title=latest_match_obj.get("job_title"),
        latest_match_score=latest_match_obj.get("semantic_score"),
        target_roadmap_role=(latest_rec.get("latest_roadmap") or {}).get("role_title"),
        has_extracted_text=bool(latest_rec.get("extracted_text")),
    )

    return HistoryAnalyticsResponse(
        success=True,
        total_analyses=total_analyses,
        unique_skills_count=len(skill_counts),
        top_skills=top_skills,
        domain_distribution=domain_distribution,
        score_progression=score_progression,
        latest_analysis=latest_summary
    )


@router.get(
    "/{record_id}",
    response_model=HistoryDetailResponse,
    summary="Retrieve full historical snapshot by record ID"
)
async def get_history_detail(
    record_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieve full analysis snapshot for reloading into active workspace."""
    record = db.get_history_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History record not found."
        )

    # Cross-user isolation check
    if record["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this record."
        )

    return HistoryDetailResponse(
        success=True,
        record=record
    )


@router.delete(
    "/{record_id}",
    response_model=HistoryActionResponse,
    summary="Delete a single analysis record"
)
async def delete_history_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Delete an individual analysis record with ownership verification."""
    record = db.get_history_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History record not found."
        )

    if record["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this record."
        )

    deleted = db.delete_history_record(record_id, current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History record could not be deleted."
        )

    return HistoryActionResponse(
        success=True,
        message="Analysis history record deleted successfully."
    )


@router.delete(
    "",
    response_model=HistoryActionResponse,
    summary="Clear all analysis history for current user"
)
async def clear_all_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Clear all saved historical records belonging to the authenticated user."""
    count = db.clear_user_history(current_user["id"])
    return HistoryActionResponse(
        success=True,
        message="All analysis history records cleared successfully.",
        deleted_count=count
    )
