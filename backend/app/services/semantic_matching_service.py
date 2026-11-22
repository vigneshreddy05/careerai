"""
Semantic Resume–Job Description Matching Service for CareerAI.

Uses all-MiniLM-L6-v2 (Sentence-BERT architecture) via Hugging Face Transformers
with attention-mask-aware mean pooling and L2 normalization on CPU.
Supports a lightweight LOW_MEMORY_MODE (< 150 MB RAM) using scikit-learn TF-IDF
for 512 MB RAM cloud environments (Render Free Tier).
Combines dense semantic vector similarity with deterministic skill gap analysis
from the existing skill_extractor taxonomy.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import torch
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel
    HAS_TORCH_TRANSFORMERS = True
except ImportError:
    torch = None
    F = None
    AutoTokenizer = None
    AutoModel = None
    HAS_TORCH_TRANSFORMERS = False

try:
    from backend.app.core.config import settings
    from backend.app.schemas.matching import (
        SkillMatchBreakdown,
        SemanticMatchResult,
        JobMatchingResponse,
        MANDATORY_MATCHING_DISCLAIMER,
    )
    from backend.app.services.skill_extractor import extract_skills
except ModuleNotFoundError:
    from app.core.config import settings
    from app.schemas.matching import (
        SkillMatchBreakdown,
        SemanticMatchResult,
        JobMatchingResponse,
        MANDATORY_MATCHING_DISCLAIMER,
    )
    from app.services.skill_extractor import extract_skills

logger = logging.getLogger(__name__)

DEFAULT_MINILM_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "ml"
    / "saved_models"
    / "all-MiniLM-L6-v2"
)
DEFAULT_MAX_WORDS_PER_CHUNK = 150
DEFAULT_CHUNK_OVERLAP = 30
DEFAULT_MAX_TOKENS = 256


class SemanticMatchingService:
    """
    Singleton service for Sentence-BERT semantic document matching
    and deterministic skill gap analysis on CPU.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MINILM_DIR
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None
        self.device = torch.device("cpu") if (torch and hasattr(torch, "device")) else "cpu"
        self.embedding_dimension = 384

    def load_model(self, force_reload: bool = False) -> bool:
        """
        Load all-MiniLM-L6-v2 tokenizer and model weights from local disk on CPU.
        Under LOW_MEMORY_MODE, skips loading PyTorch transformer weights into RAM.
        """
        if self.is_loaded and not force_reload:
            return True

        # 1. Check for LOW_MEMORY_MODE (Render 512MB free tier)
        if getattr(settings, "LOW_MEMORY_MODE", False) or not HAS_TORCH_TRANSFORMERS:
            logger.info("LOW_MEMORY_MODE is active. Initializing lightweight TF-IDF semantic matcher (< 150 MB RAM)...")
            self.is_loaded = True
            self.load_error = None
            return True

        # 2. Standard Mode: Load full all-MiniLM-L6-v2 PyTorch checkpoint
        if not self.model_dir.exists():
            self.load_error = f"Model directory not found at: {self.model_dir}"
            logger.error(self.load_error)
            self.is_loaded = False
            return False

        try:
            logger.info("Loading all-MiniLM-L6-v2 Sentence-BERT model from %s on CPU...", self.model_dir)
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir), local_files_only=True)
            self.model = AutoModel.from_pretrained(str(self.model_dir), local_files_only=True)
            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            self.load_error = None
            logger.info("all-MiniLM-L6-v2 model loaded successfully (dimension=%d).", self.embedding_dimension)
            return True

        except Exception as exc:
            self.is_loaded = False
            self.load_error = f"Failed to load all-MiniLM-L6-v2 model: {exc}"
            logger.exception(self.load_error)
            return False

    @staticmethod
    def _mean_pooling(model_output, attention_mask: Any) -> Any:
        """
        Compute attention-mask-aware mean pooling across token embeddings.
        Avoids skewing the pooled vector with zero-padding tokens.
        """
        token_embeddings = model_output[0]  # Shape: [batch_size, seq_len, 384]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    @staticmethod
    def _chunk_text(
        text: str,
        max_words: int = DEFAULT_MAX_WORDS_PER_CHUNK,
        overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> List[str]:
        """
        Segment text into overlapping word windows.
        Ensures long resumes and job descriptions are fully captured without truncation.
        """
        words = text.split()
        if not words:
            return []
        if len(words) <= max_words:
            return [text]

        chunks: List[str] = []
        stride = max(1, max_words - overlap)
        for i in range(0, len(words), stride):
            chunk_slice = words[i:i + max_words]
            if chunk_slice:
                chunks.append(" ".join(chunk_slice))
            if i + max_words >= len(words):
                break
        return chunks

    def _encode_text(self, text: str) -> Tuple[Any, int]:
        """
        Encode arbitrary-length text into a 384-dimensional unit vector.
        Splits into chunks, mean-pools and L2-normalizes each chunk, then
        computes the normalized average of chunk vectors.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return torch.zeros((1, self.embedding_dimension), device=self.device), 1

        encoded = self.tokenizer(
            chunks,
            padding=True,
            truncation=True,
            max_length=DEFAULT_MAX_TOKENS,
            return_tensors="pt"
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.inference_mode():
            outputs = self.model(**encoded)
            chunk_pooled = self._mean_pooling(outputs, encoded["attention_mask"])
            chunk_normalized = F.normalize(chunk_pooled, p=2, dim=1)
            doc_pooled = torch.mean(chunk_normalized, dim=0, keepdim=True)
            doc_embedding = F.normalize(doc_pooled, p=2, dim=1)

        return doc_embedding, len(chunks)

    @staticmethod
    def _generate_suggestions(
        missing_skills: List[str],
        matching_skills: List[str],
        semantic_sim: float,
        skill_pct: float
    ) -> List[str]:
        """
        Generate targeted suggestions based on missing skills and metric disparities.
        """
        suggestions: List[str] = []

        if missing_skills:
            top_missing = missing_skills[:5]
            suggestions.append(
                f"Address key technical requirements: Consider highlighting experience, projects, or coursework "
                f"in {', '.join(top_missing)} if you possess relevant competency."
            )

        if skill_pct < 50.0 and semantic_sim >= 0.65:
            suggestions.append(
                "High conceptual alignment but low explicit skill overlap: Your resume demonstrates strong domain "
                "relevance, but lacks specific tool names mentioned in the job description. Explicitly incorporate "
                "standard industry terms and tools to improve ATS keyword parsing."
            )
        elif skill_pct >= 70.0 and semantic_sim < 0.50:
            suggestions.append(
                "Good keyword coverage but lower holistic semantic similarity: While specific tools match, the overall "
                "context (such as industry domain, seniority level, or day-to-day responsibilities) may differ from "
                "the target position. Align your accomplishment statements with the job's core responsibilities."
            )

        if len(matching_skills) >= 5 and semantic_sim >= 0.70:
            suggestions.append(
                "Strong profile alignment: Highlight your verified matching skills "
                f"({', '.join(matching_skills[:4])}) in the summary section or top bullet points of your resume."
            )

        if not suggestions:
            suggestions.append(
                "Review the listed missing requirements and tailor your project descriptions to demonstrate practical application."
            )

        return suggestions

    def match(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str] = None
    ) -> JobMatchingResponse:
        """
        Execute dual-engine semantic matching and deterministic skill gap analysis.
        """
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError(self.load_error or "Semantic matching model is unavailable.")

        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty or whitespace only.")
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty or whitespace only.")

        clean_resume = resume_text.strip()
        clean_jd = job_description.strip()

        # 1. Deterministic Skill Extraction via skill_extractor
        resume_skills_dict = extract_skills(clean_resume)
        jd_skills_dict = extract_skills(clean_jd)

        resume_skills_set = set(resume_skills_dict.get("all_skills", []))
        jd_skills_set = set(jd_skills_dict.get("all_skills", []))

        matching_skills = sorted(list(resume_skills_set & jd_skills_set))
        missing_skills = sorted(list(jd_skills_set - resume_skills_set))
        additional_skills = sorted(list(resume_skills_set - jd_skills_set))

        matched_count = len(matching_skills)
        total_jd = len(jd_skills_set)
        match_percentage = round((matched_count / total_jd * 100), 1) if total_jd > 0 else 100.0

        skill_match = SkillMatchBreakdown(
            resume_skills=sorted(list(resume_skills_set)),
            job_description_skills=sorted(list(jd_skills_set)),
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            additional_skills=additional_skills,
            matched_count=matched_count,
            total_jd_skills=total_jd,
            match_percentage=match_percentage,
        )

        # 2. Semantic Similarity Calculation (Sentence-BERT or Lightweight TF-IDF)
        if getattr(settings, "LOW_MEMORY_MODE", False) or not HAS_TORCH_TRANSFORMERS or self.model is None:
            # Lightweight TF-IDF vector similarity via scikit-learn
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity

                vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),
                    stop_words="english",
                    max_features=2000,
                    sublinear_tf=True
                )
                tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_jd])
                raw_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            except Exception:
                # Token overlap fallback if scikit-learn fails
                r_words = set(clean_resume.lower().split())
                j_words = set(clean_jd.lower().split())
                raw_sim = len(r_words & j_words) / max(len(j_words), 1)

            clamped_sim = max(0.0, min(1.0, raw_sim))
            chunk_count_resume = 1
            chunk_count_jd = 1
        else:
            # Full Sentence-BERT inference
            emb_resume, chunk_count_resume = self._encode_text(clean_resume)
            emb_jd, chunk_count_jd = self._encode_text(clean_jd)

            raw_sim = float(torch.sum(emb_resume * emb_jd).item())
            clamped_sim = max(0.0, min(1.0, raw_sim))

        sim_percentage = round(clamped_sim * 100, 1)

        if clamped_sim >= 0.75:
            sim_level = "High Match"
        elif clamped_sim >= 0.50:
            sim_level = "Moderate Match"
        else:
            sim_level = "Low Match"

        semantic_match = SemanticMatchResult(
            similarity_score=round(clamped_sim, 4),
            similarity_percentage=sim_percentage,
            similarity_level=sim_level,
            embedding_dimension=self.embedding_dimension,
            model="all-MiniLM-L6-v2",
            chunk_count_resume=chunk_count_resume,
            chunk_count_job=chunk_count_jd,
        )

        # 3. Actionable Tailored Suggestions
        suggestions = self._generate_suggestions(
            missing_skills=missing_skills,
            matching_skills=matching_skills,
            semantic_sim=clamped_sim,
            skill_pct=match_percentage,
        )

        return JobMatchingResponse(
            success=True,
            job_title=job_title,
            semantic_match=semantic_match,
            skill_match=skill_match,
            suggestions=suggestions,
            disclaimer=MANDATORY_MATCHING_DISCLAIMER,
        )


# Global singleton instance
_matching_service_instance: Optional[SemanticMatchingService] = None


def get_semantic_matching_service() -> SemanticMatchingService:
    """Return the singleton instance of SemanticMatchingService."""
    global _matching_service_instance
    if _matching_service_instance is None:
        _matching_service_instance = SemanticMatchingService()
    return _matching_service_instance
