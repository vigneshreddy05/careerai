from fastapi import APIRouter, File, HTTPException, UploadFile, status

try:
    from backend.app.schemas.resume import ResumeAnalysisResponse
    from backend.app.services.resume_parser import MAX_UPLOAD_SIZE, parse_resume
except ModuleNotFoundError:
    from app.schemas.resume import ResumeAnalysisResponse
    from app.services.resume_parser import MAX_UPLOAD_SIZE, parse_resume

router = APIRouter()


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Analyze uploaded resume document",
    description="Upload a PDF or DOCX resume for in-memory parsing, skill extraction, and structural analysis.",
)
async def analyze_resume(file: UploadFile = File(...)):
    """
    In-memory resume analysis endpoint.
    Processes PDF and DOCX documents with PyMuPDF and python-docx.
    Does not persist files to disk or database.
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

    # Process and extract resume information
    try:
        result = parse_resume(file_bytes=content, filename=file.filename)
        return result
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
