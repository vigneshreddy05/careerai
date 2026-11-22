from typing import List, Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Extracted contact information from resume."""
    email: Optional[str] = Field(None, description="Extracted email address")
    phone: Optional[str] = Field(None, description="Extracted phone number")


class SkillsCategorized(BaseModel):
    """Categorized technical skills identified in the document."""
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_libraries: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud_and_devops: List[str] = Field(default_factory=list)
    ai_and_machine_learning: List[str] = Field(default_factory=list)
    all_skills: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """Education qualification record."""
    degree: str = Field(..., description="Identified qualification or degree title")
    field_of_study: Optional[str] = Field(None, description="Major or specialization")
    institution: Optional[str] = Field(None, description="University, college or school")
    year: Optional[str] = Field(None, description="Graduation year or date range")
    score: Optional[str] = Field(None, description="Extracted CGPA, GPA, or percentage score")


class ProjectEntry(BaseModel):
    """Academic, personal, or capstone project record."""
    title: str = Field(..., description="Project title or topic")
    description: Optional[str] = Field(None, description="Summary or description of the project")
    technologies: List[str] = Field(default_factory=list, description="Technologies referenced in project")


class ExperienceEntry(BaseModel):
    """Identified professional employment or internship record."""
    title: Optional[str] = Field(None, description="Job or role title")
    organization: Optional[str] = Field(None, description="Company or organization name")
    duration: Optional[str] = Field(None, description="Date range or duration string")
    description: str = Field(..., description="Relevant employment description text")


class ExperienceSummary(BaseModel):
    """Professional experience summary and detected entries."""
    total_years_estimated: Optional[float] = Field(
        None, description="Estimated total years of professional employment if determinable"
    )
    entries: List[ExperienceEntry] = Field(default_factory=list)


class ResumeStatistics(BaseModel):
    """Structural text statistics for the uploaded document."""
    word_count: int
    character_count: int
    skill_count: int
    education_count: int
    experience_count: int
    project_count: int = Field(0, description="Number of identified projects")


class ResumeAnalysisResponse(BaseModel):
    """Standardized response schema for resume analysis."""
    success: bool = True
    filename: str
    file_type: str
    contact_info: ContactInfo
    skills: SkillsCategorized
    education: List[EducationEntry]
    experience: ExperienceSummary
    projects: List[ProjectEntry] = Field(default_factory=list, description="Extracted academic or personal projects")
    statistics: ResumeStatistics
    text_preview: str = Field(..., description="Truncated preview of extracted text")
    extracted_text: Optional[str] = Field(None, description="Complete extracted text for downstream ML pipelines")
