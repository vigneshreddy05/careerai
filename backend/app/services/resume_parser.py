import io
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import docx
import pymupdf

try:
    from backend.app.schemas.resume import (
        ContactInfo,
        EducationEntry,
        ExperienceEntry,
        ExperienceSummary,
        ProjectEntry,
        ResumeAnalysisResponse,
        ResumeStatistics,
        SkillsCategorized,
    )
    from backend.app.services.skill_extractor import extract_skills
except ModuleNotFoundError:
    from app.schemas.resume import (
        ContactInfo,
        EducationEntry,
        ExperienceEntry,
        ExperienceSummary,
        ProjectEntry,
        ResumeAnalysisResponse,
        ResumeStatistics,
        SkillsCategorized,
    )
    from app.services.skill_extractor import extract_skills

# Maximum file upload size: 5 MB
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

# Magic byte signatures for genuine format validation
PDF_MAGIC_BYTES = b"%PDF-"
DOCX_MAGIC_BYTES = b"PK\x03\x04"

# Comprehensive Education Level Patterns (ordered from most specific to general)
EDUCATION_PATTERNS = [
    (r"\b(Ph\.?D\.?|Doctor of Philosophy)\b", "Doctor of Philosophy (Ph.D.)"),
    (r"\b(M\.?Tech|Master of Technology)\b", "Master of Technology (M.Tech)"),
    (r"\b(M\.?E\.?|Master of Engineering)\b", "Master of Engineering (M.E.)"),
    (r"\b(M\.?S\.?|Master of Science)\b", "Master of Science (M.S.)"),
    (r"\b(M\.?C\.?A\.?|Master of Computer Applications)\b", "Master of Computer Applications (MCA)"),
    (r"\b(M\.?B\.?A\.?|Master of Business Administration)\b", "Master of Business Administration (MBA)"),
    (r"\b(B\.?Tech|Bachelor of Technology)\b", "Bachelor of Technology (B.Tech)"),
    (r"\b(B\.?E\.?|Bachelor of Engineering)\b", "Bachelor of Engineering (B.E.)"),
    (r"\b(B\.?S\.?|Bachelor of Science)\b", "Bachelor of Science (B.S.)"),
    (r"\b(B\.?C\.?A\.?|Bachelor of Computer Applications)\b", "Bachelor of Computer Applications (BCA)"),
    (r"\b(Bachelor(?:'s)? Degree|Bachelors?)\b", "Bachelor's Degree"),
    (r"\b(Master(?:'s)? Degree|Masters?)\b", "Master's Degree"),
    (r"\b(Diploma|Polytechnic|Associate Degree)\b", "Diploma / Polytechnic"),
    # Class 12 / Intermediate / HSC / Senior Secondary
    (
        r"(?i)\b(?:Class\s*(?:12th?|XII)|12th\s*(?:Grade|Standard|Class|Board)?|Intermediate(?:\s*\([A-Za-z]+\))?|HSC\b|Higher\s+Secondary(?:\s+Certificate)?|Senior\s+Secondary|PUC\b|Pre-University)",
        "Class XII / Intermediate"
    ),
    # Class 10 / SSC / Matriculation / Secondary School
    (
        r"(?i)\b(?:Class\s*(?:10th?|X)|10th\s*(?:Grade|Standard|Class|Board)?|SSC\b|Secondary\s+School(?:\s+Certificate)?|Matriculation|High\s+School)",
        "Class X / Secondary"
    ),
]

FIELDS_OF_STUDY = [
    "Computer Science and Engineering", "Computer Science", "Information Technology",
    "Software Engineering", "Data Science", "Artificial Intelligence",
    "Electrical and Electronics", "Electrical Engineering", "Electronics and Communication",
    "Mechanical Engineering", "Civil Engineering", "Mathematics", "Physics",
    "Cyber Security", "Computer Applications", "MPC", "BiPC", "Commerce"
]

INSTITUTION_KEYWORDS = [
    "University", "Institute of Technology", "Institute", "College of Engineering",
    "Engineering College", "College", "School", "Academy", "IIT", "NIT", "BITS",
    "IIIT", "Polytechnic", "Vidyalaya", "Public School", "Junior College"
]


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize filename to prevent directory traversal or script injection."""
    if not filename:
        return "unnamed_resume"
    basename = os.path.basename(filename)
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
    return sanitized or "unnamed_resume"


def validate_document_signature(file_bytes: bytes, filename: str) -> str:
    """Validate file format using both extension and file magic bytes."""
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("The uploaded file is empty.")

    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise ValueError(f"File exceeds maximum allowed size of 5 MB ({len(file_bytes) / (1024 * 1024):.2f} MB).")

    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise ValueError("Invalid PDF file: Missing standard PDF header signature.")
        return "pdf"
    elif lower_name.endswith(".docx"):
        if not file_bytes.startswith(DOCX_MAGIC_BYTES):
            raise ValueError("Invalid DOCX file: Missing standard Office Open XML signature.")
        return "docx"
    else:
        raise ValueError("Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF in-memory using PyMuPDF."""
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("Failed to parse PDF document: The file appears corrupted or unreadable.") from exc

    text_parts = []
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text.strip())
    finally:
        doc.close()

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("No extractable text found in PDF. Scanned images or password-protected files are not supported.")
    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX in-memory using python-docx."""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError("Failed to parse DOCX document: The file appears corrupted or invalid.") from exc

    text_parts = []
    for p in doc.paragraphs:
        if p.text.strip():
            text_parts.append(p.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text_parts.append(" | ".join(row_text))

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("No extractable text found in Word document.")
    return full_text


def extract_contact_info(text: str) -> ContactInfo:
    """Extract contact information (email and phone number) using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    phone_pattern = r'(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}'
    phone = None
    for match in re.finditer(phone_pattern, text):
        candidate = match.group(0).strip()
        digits = re.sub(r'\D', '', candidate)
        if 7 <= len(digits) <= 15:
            if not (len(digits) == 4 and (candidate.startswith("19") or candidate.startswith("20"))):
                phone = candidate
                break

    return ContactInfo(email=email, phone=phone)


def extract_academic_score(line: str) -> Optional[str]:
    """Extract CGPA, GPA, or percentage score string from line."""
    score_patterns = [
        r'(?i)\b(?:CGPA|GPA|Grade|Score)\s*[:=-]?\s*(\d+(?:\.\d+)?(?:\s*/\s*(?:10|4|100))?)',
        r'(\b\d+(?:\.\d+)?\s*(?:CGPA|GPA)\b)',
        r'(?i)\b(?:Percentage|Aggregate|Marks)\s*[:=-]?\s*(\d+(?:\.\d+)?\s*%?)',
        r'(\b\d{2}(?:\.\d+)?\s*%)',
    ]
    for pattern in score_patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(0).strip()
    return None


def clean_institution_name(text: str, score: Optional[str] = None) -> Optional[str]:
    """Clean institution name by removing CGPA, percentage, dates, and degree terms."""
    cleaned = text
    if score:
        cleaned = cleaned.replace(score, " ")

    # Strip extraneous score patterns
    cleaned = re.sub(r'(?i)\b(?:CGPA|GPA|Percentage|Marks|Score)\b[:\s=-]*\d+(?:\.\d+)?(?:\s*/\s*\d+)?%?', ' ', cleaned)
    cleaned = re.sub(r'\b\d{2}(?:\.\d+)?\s*%', ' ', cleaned)
    # Strip date ranges and years
    cleaned = re.sub(r'\b(?:20\d{2}|19\d{2})\s*[-–to]+\s*(?:20\d{2}|19\d{2}|Present)\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:20\d{2}|19\d{2})\b', ' ', cleaned)

    # Split by pipe, tab, semicolon, bullet, or newline
    segments = re.split(r'[|\t•;\n]', cleaned)
    for seg in segments:
        seg = seg.strip()
        # Search for institution keywords
        for inst_kw in INSTITUTION_KEYWORDS:
            if re.search(rf'\b{re.escape(inst_kw)}\b', seg, re.IGNORECASE):
                # Clean leading prepositions
                seg = re.sub(r'(?i)^\s*(?:from|at|in|completed\s+at)\s+', '', seg)
                # Clean degree names if accidentally at the beginning
                for deg_pat, _ in EDUCATION_PATTERNS:
                    seg = re.sub(deg_pat, '', seg, flags=re.IGNORECASE)
                # Clean leading/trailing punctuation and extra whitespace
                seg = re.sub(r'^[^\w]+|[^\w]+$', '', seg).strip()
                if len(seg) >= 3 and not re.search(r'^\d+$', seg):
                    return seg

    # Fallback search across line if no pipe/delimiter was used
    for inst_kw in INSTITUTION_KEYWORDS:
        inst_match = re.search(rf'([^.\n|;•]*\b{re.escape(inst_kw)}\b[^.\n|;•]*)', cleaned, re.IGNORECASE)
        if inst_match:
            candidate = inst_match.group(0).strip()
            candidate = re.sub(r'(?i)^\s*(?:from|at|in|completed\s+at)\s+', '', candidate)
            candidate = re.sub(r'^[^\w]+|[^\w]+$', '', candidate).strip()
            if len(candidate) >= 3 and not re.search(r'^\d+$', candidate):
                return candidate

    return None


def extract_education(text: str) -> List[EducationEntry]:
    """Identify education qualifications, degrees, institutions, scores, and years."""
    entries: List[EducationEntry] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for idx, line in enumerate(lines):
        for deg_pattern, canonical_degree in EDUCATION_PATTERNS:
            if re.search(deg_pattern, line, re.IGNORECASE):
                # Build context window: current line, next 1-2 lines (if not a new degree), and previous line
                context_lines = [line]
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    if not any(re.search(p, next_line, re.IGNORECASE) for p, _ in EDUCATION_PATTERNS):
                        if not re.match(r'(?i)^(?:Experience|Work|Professional|Projects?|Skills|Summary|Technical)', next_line):
                            context_lines.append(next_line)
                            if idx + 2 < len(lines):
                                next_next_line = lines[idx + 2]
                                if not any(re.search(p, next_next_line, re.IGNORECASE) for p, _ in EDUCATION_PATTERNS):
                                    if not re.match(r'(?i)^(?:Experience|Work|Professional|Projects?|Skills|Summary|Technical)', next_next_line):
                                        context_lines.append(next_next_line)

                if idx - 1 >= 0:
                    prev_line = lines[idx - 1]
                    if not any(re.search(p, prev_line, re.IGNORECASE) for p, _ in EDUCATION_PATTERNS):
                        if not re.match(r'(?i)^(?:Education|Academic|Qualifications?)', prev_line):
                            context_lines.insert(0, prev_line)

                combined_context = " | ".join(context_lines)

                # Extract academic score separately (CGPA or percentage)
                score_found = extract_academic_score(combined_context)

                # Extract field of study
                field_found = None
                for field in FIELDS_OF_STUDY:
                    if re.search(rf'\b{re.escape(field)}\b', combined_context, re.IGNORECASE):
                        field_found = field
                        break

                # Extract cleaned institution name
                institution_found = clean_institution_name(combined_context, score_found)

                # Extract graduation year
                year_match = re.search(
                    r'\b(20\d{2}(?:\s*[-–]\s*20\d{2}|\s*[-–]\s*Present)?|19\d{2})\b',
                    combined_context,
                    re.IGNORECASE
                )
                year_found = year_match.group(0).strip() if year_match else None

                entries.append(EducationEntry(
                    degree=canonical_degree,
                    field_of_study=field_found,
                    institution=institution_found,
                    year=year_found,
                    score=score_found
                ))
                break

    # Deduplicate entries by degree
    seen_degrees = set()
    unique_entries = []
    for entry in entries:
        if entry.degree not in seen_degrees:
            seen_degrees.add(entry.degree)
            unique_entries.append(entry)

    return unique_entries


def extract_experience_and_projects(text: str) -> Tuple[ExperienceSummary, List[ProjectEntry]]:
    """
    Separate professional employment experience from academic or personal projects.
    Academic and personal projects are never counted as paid work experience.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Section tracking
    current_section = "GENERAL"
    project_lines: List[str] = []
    experience_lines: List[str] = []

    for line in lines:
        upper = line.upper()
        if re.match(r'^(?:ACADEMIC\s+)?PROJECTS?(?:\s+AND\s+PUBLICATIONS)?[:\s-]*$', upper) or "PROJECTS" in upper and len(line) < 30:
            current_section = "PROJECTS"
            continue
        elif re.match(r'^(?:WORK|PROFESSIONAL|EMPLOYMENT)?\s*(?:EXPERIENCE|HISTORY)[:\s-]*$', upper) or "EXPERIENCE" in upper and len(line) < 30:
            current_section = "EXPERIENCE"
            continue
        elif re.match(r'^(?:EDUCATION|ACADEMIC\s+BACKGROUND|QUALIFICATIONS)[:\s-]*$', upper) or "EDUCATION" in upper and len(line) < 30:
            current_section = "EDUCATION"
            continue
        elif re.match(r'^(?:TECHNICAL\s+)?(?:SKILLS|COMPETENCIES)[:\s-]*$', upper) or "SKILLS" in upper and len(line) < 30:
            current_section = "SKILLS"
            continue

        if current_section == "PROJECTS":
            project_lines.append(line)
        elif current_section == "EXPERIENCE":
            experience_lines.append(line)

    # 1. Parse Projects
    projects: List[ProjectEntry] = []
    # If no explicit project section was found, check for project prefixes across all lines
    if not project_lines:
        for line in lines:
            if re.search(r'(?i)\b(?:Academic\s+Project|Personal\s+Project|Capstone\s+Project|Project\s*Title|Project\s*Name)\b', line):
                project_lines.append(line)

    # Group project items
    for line in project_lines:
        # Check if line indicates a project title
        title_match = re.search(r'(?i)(?:Project\s*[:=-]?\s*)?([A-Za-z0-9\s-]{4,60})(?:\s*[-|–]\s*(.*))?$', line)
        if title_match:
            raw_title = title_match.group(1).strip()
            # Clean title
            clean_title = re.sub(r'(?i)^(?:Academic\s+Project|Personal\s+Project|Capstone|Project)\s*[:=-]?\s*', '', raw_title).strip()
            if len(clean_title) >= 4 and not re.match(r'(?i)^(?:Key\s+Features|Technologies|Tools|Description)$', clean_title):
                # Extract technologies from the line/description
                tech_data = extract_skills(line)
                projects.append(ProjectEntry(
                    title=clean_title,
                    description=line[:250],
                    technologies=tech_data["all_skills"]
                ))

    # Deduplicate projects
    seen_proj = set()
    unique_projects = []
    for p in projects:
        if p.title.lower() not in seen_proj:
            seen_proj.add(p.title.lower())
            unique_projects.append(p)

    # 2. Parse Professional Experience
    role_titles = [
        "Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Developer",
        "Data Scientist", "Data Analyst", "Machine Learning Engineer", "DevOps Engineer",
        "Cloud Architect", "Product Manager", "QA Engineer", "Software Developer",
        "System Administrator", "Solutions Architect", "Technical Lead", "Engineering Manager",
        "Intern", "Software Engineering Intern", "Web Development Intern"
    ]

    experience_entries: List[ExperienceEntry] = []
    target_exp_lines = experience_lines if experience_lines else lines

    for idx, line in enumerate(target_exp_lines):
        # Exclude project markers from experience
        if re.search(r'(?i)\b(?:academic\s+project|personal\s+project|capstone|coursework|mini\s+project)\b', line):
            continue

        for role in role_titles:
            if re.search(rf'\b{re.escape(role)}\b', line, re.IGNORECASE):
                # Date range search
                date_match = re.search(
                    r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}\s*[-–to]+\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}))\b',
                    line,
                    re.IGNORECASE
                )
                duration_str = date_match.group(0).strip() if date_match else None

                desc_snippet = line
                if idx + 1 < len(target_exp_lines):
                    desc_snippet += " | " + target_exp_lines[idx + 1]

                experience_entries.append(ExperienceEntry(
                    title=role,
                    organization=None,
                    duration=duration_str,
                    description=desc_snippet[:250]
                ))
                break

    # Calculate total professional experience (ignoring projects)
    total_years: Optional[float] = None
    explicit_exp_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?\s+experience', text, re.IGNORECASE)
    if explicit_exp_match:
        try:
            total_years = float(explicit_exp_match.group(1))
        except ValueError:
            pass

    # Deduplicate experience entries
    seen_exp = set()
    unique_exp = []
    for entry in experience_entries:
        key = (entry.title, entry.duration)
        if key not in seen_exp:
            seen_exp.add(key)
            unique_exp.append(entry)

    summary = ExperienceSummary(
        total_years_estimated=total_years,
        entries=unique_exp
    )

    return summary, unique_projects


def parse_resume(file_bytes: bytes, filename: str) -> ResumeAnalysisResponse:
    """
    Main orchestration function: validates, extracts text in memory,
    and structures all resume sections without logging PII or storing files.
    """
    clean_filename = sanitize_filename(filename)
    file_type = validate_document_signature(file_bytes, clean_filename)

    if file_type == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif file_type == "docx":
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported format.")

    # Extract modular sections
    contact_info = extract_contact_info(text)
    skills_data = extract_skills(text)
    education = extract_education(text)
    experience, projects = extract_experience_and_projects(text)

    # Calculate statistics
    words = text.split()
    stats = ResumeStatistics(
        word_count=len(words),
        character_count=len(text),
        skill_count=len(skills_data["all_skills"]),
        education_count=len(education),
        experience_count=len(experience.entries),
        project_count=len(projects)
    )

    # Safe text preview truncated to first 1,500 characters
    text_preview = text[:1500] + ("..." if len(text) > 1500 else "")

    return ResumeAnalysisResponse(
        success=True,
        filename=clean_filename,
        file_type=file_type.upper(),
        contact_info=contact_info,
        skills=SkillsCategorized(**skills_data),
        education=education,
        experience=experience,
        projects=projects,
        statistics=stats,
        text_preview=text_preview,
        extracted_text=text
    )
