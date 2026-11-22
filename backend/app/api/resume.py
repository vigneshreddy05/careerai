from typing import Optional
from fastapi import APIRouter, File, Header, HTTPException, UploadFile, status, Depends

try:
    from backend.app.schemas.resume import ResumeAnalysisResponse
    from backend.app.services.resume_parser import MAX_UPLOAD_SIZE, parse_resume
    from backend.app.core.database import get_db, DatabaseManager
    from backend.app.core.security import decode_access_token
except ModuleNotFoundError:
    from app.schemas.resume import ResumeAnalysisResponse
    from app.services.resume_parser import MAX_UPLOAD_SIZE, parse_resume
    from app.core.database import get_db, DatabaseManager
    from app.core.security import decode_access_token

router = APIRouter()


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Analyze uploaded resume document",
    description="Upload a PDF or DOCX resume for in-memory parsing, skill extraction, and structural analysis.",
)
async def analyze_resume(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: DatabaseManager = Depends(get_db),
):
    """
    In-memory resume analysis endpoint.
    Processes PDF and DOCX documents with PyMuPDF and python-docx.
    Automatically captures a submission record for platform administration.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided in the upload request.",
        )

    # Read document content in-memory
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read upload stream.",
        ) from exc

    # Enforce size limit
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of 5 MB ({len(content) / (1024 * 1024):.2f} MB).",
        )

    # Resolve optional user identity if authenticated
    user_id = None
    user_email = None
    if authorization and authorization.strip().startswith("Bearer "):
        token = authorization.strip().split(" ", 1)[1].strip()
        try:
            if not db.is_token_blocklisted(token):
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                user_email = payload.get("email")
        except Exception:
            user_id = None
            user_email = None

    # Process and extract resume information
    try:
        result = parse_resume(file_bytes=content, filename=file.filename)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as err:
        # Do not expose internal server paths, file descriptors or stack traces
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the document. Please ensure the file is not corrupted.",
        ) from err

    # Persist resume submission for administrative review
    try:
        contact_dict = (
            result.contact_info.model_dump()
            if hasattr(result.contact_info, "model_dump")
            else result.contact_info.dict()
        )
        education_list = [
            (e.model_dump() if hasattr(e, "model_dump") else e.dict())
            for e in result.education
        ]
        experience_dict = (
            result.experience.model_dump()
            if hasattr(result.experience, "model_dump")
            else result.experience.dict()
        )
        all_skills = result.skills.all_skills if hasattr(result.skills, "all_skills") else []

        db.save_resume_submission({
            "user_id": user_id,
            "user_email": user_email,
            "filename": result.filename,
            "file_type": result.file_type,
            "word_count": result.statistics.word_count,
            "contact": contact_dict,
            "skills": all_skills,
            "education": education_list,
            "experience": experience_dict.get("entries", []),
            "extracted_text": result.extracted_text,
        })
    except Exception:
        # Ensure persistence errors never block candidate analysis
        pass

    return result
