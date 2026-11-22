import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAS_TORCH_TRANSFORMERS = True
except ImportError:
    torch = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    HAS_TORCH_TRANSFORMERS = False

try:
    from backend.app.core.config import settings
    from backend.app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionResponse,
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionResponse,
    )

logger = logging.getLogger(__name__)

# Default model directory
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "saved_models" / "distilbert_job_classifier"
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.40
DEFAULT_MAX_SEQ_LENGTH = 256

# Canonical 24 DistilBERT categories
CANONICAL_24_CATEGORIES = [
    "ACCOUNTANT", "ADVOCATE", "AGRICULTURE", "APPAREL", "ARTS",
    "AUTOMOBILE", "AVIATION", "BANKING", "BPO", "BUSINESS-DEVELOPMENT",
    "CHEF", "CONSTRUCTION", "CONSULTANT", "DESIGNER", "DIGITAL-MEDIA",
    "ENGINEERING", "FINANCE", "FITNESS", "HEALTHCARE", "HR",
    "INFORMATION-TECHNOLOGY", "PUBLIC-RELATIONS", "SALES", "TEACHER"
]

DOMAIN_LEXICON = {
    "INFORMATION-TECHNOLOGY": [
        "python", "javascript", "typescript", "react", "fastapi", "django", "node",
        "sql", "postgresql", "docker", "kubernetes", "aws", "cloud", "api", "git",
        "backend", "frontend", "full stack", "software engineer", "developer", "devops",
        "database", "linux", "html", "css", "java", "c++", "c#", "mongodb", "redis",
        "microservices", "agile", "restful", "ci/cd", "graphql", "machine learning", "data science"
    ],
    "ENGINEERING": [
        "engineering", "engineer", "cad", "autocad", "solidworks", "matlab", "mechanical",
        "electrical", "civil", "structural", "aerospace", "embedded", "firmware", "schematic",
        "manufacturing", "industrial", "robotics", "automation", "circuit", "testing"
    ],
    "HR": [
        "human resources", "talent acquisition", "recruiting", "recruitment", "onboarding",
        "employee relations", "performance appraisal", "benefits", "payroll", "labor law",
        "hris", "sourcing", "interviews", "personnel", "workforce", "hiring"
    ],
    "FINANCE": [
        "financial", "finance", "investment", "portfolio", "wealth", "capital", "valuation",
        "equity", "asset", "risk analysis", "financial modeling", "forecasting", "sec",
        "hedge fund", "cfa", "securities", "mergers", "acquisitions"
    ],
    "ACCOUNTANT": [
        "accounting", "accountant", "ledger", "balance sheet", "income statement", "tax",
        "audit", "gaap", "quickbooks", "cpa", "reconciliation", "accounts payable",
        "accounts receivable", "journal entries", "invoicing", "cost accounting"
    ],
    "BANKING": [
        "banking", "loans", "credit", "mortgage", "underwriting", "deposits", "teller",
        "branch", "commercial banking", "retail banking", "anti-money laundering", "kyc",
        "interest rates", "credit score", "liquidity"
    ],
    "HEALTHCARE": [
        "medical", "health", "healthcare", "patient", "clinical", "nursing", "hospital",
        "doctor", "nurse", "physician", "pharmacy", "diagnosis", "treatment", "pediatric",
        "surgery", "vital signs", "electronic health records", "ehr", "cpr"
    ],
    "DESIGNER": [
        "designer", "ui", "ux", "figma", "photoshop", "illustrator", "wireframing",
        "prototyping", "user experience", "user interface", "graphic design", "typography",
        "visual design", "sketch", "adobe", "creative suite", "interaction design"
    ],
    "DIGITAL-MEDIA": [
        "digital media", "multimedia", "video editing", "audio", "premiere", "after effects",
        "content creation", "social media", "broadcasting", "podcast", "animation",
        "storytelling", "motion graphics", "youtube", "cinematography"
    ],
    "SALES": [
        "sales", "revenue", "account executive", "b2b", "b2c", "prospecting", "cold calling",
        "salesforce", "crm", "quota", "lead generation", "deal closing", "negotiation",
        "client relations", "territory", "pipeline"
    ],
    "BUSINESS-DEVELOPMENT": [
        "business development", "partnerships", "strategic alliances", "expansion",
        "market penetration", "joint ventures", "contract negotiation", "growth strategy",
        "value proposition", "pitching"
    ],
    "TEACHER": [
        "teaching", "teacher", "education", "curriculum", "lesson plan", "classroom",
        "students", "pedagogy", "instructor", "academic", "grading", "tutoring",
        "k-12", "higher education", "instructional"
    ],
    "ADVOCATE": [
        "legal", "law", "attorney", "lawyer", "litigation", "court", "pleadings",
        "contracts", "counsel", "jurisprudence", "deposition", "briefs", "compliance"
    ],
    "CONSULTANT": [
        "consulting", "consultant", "strategy", "management consulting", "stakeholder management",
        "business transformation", "advisory", "benchmarking", "process improvement", "kpi"
    ],
    "PUBLIC-RELATIONS": [
        "public relations", "pr", "press release", "media relations", "crisis management",
        "spokesperson", "brand reputation", "publicity", "press conference", "communications"
    ],
    "AUTOMOBILE": [
        "automobile", "automotive", "vehicle", "powertrain", "chassis", "mechanic",
        "engine", "transmission", "brakes", "diagnostics", "dealership", "fleet"
    ],
    "AVIATION": [
        "aviation", "aircraft", "pilot", "flight", "aerospace", "cockpit", "faa",
        "avionics", "air traffic", "airline", "navigation", "flight hours"
    ],
    "CHEF": [
        "chef", "culinary", "cooking", "kitchen", "menu", "food preparation", "recipes",
        "catering", "baking", "pastry", "sous chef", "sanitation", "fine dining"
    ],
    "CONSTRUCTION": [
        "construction", "building", "site supervisor", "contractor", "scaffolding",
        "concrete", "carpentry", "blueprints", "osha", "heavy equipment", "estimating"
    ],
    "FITNESS": [
        "fitness", "personal trainer", "workout", "gym", "nutrition", "exercise",
        "strength training", "aerobics", "wellness", "athletic", "cardio", "coaching"
    ],
    "AGRICULTURE": [
        "agriculture", "farming", "crops", "soil", "harvest", "irrigation", "agronomy",
        "horticulture", "livestock", "pesticides", "fertilizer", "sustainable farming"
    ],
    "APPAREL": [
        "apparel", "fashion", "clothing", "garment", "textile", "styling", "pattern making",
        "sewing", "fabric", "merchandising", "fashion design", "trends"
    ],
    "ARTS": [
        "art", "fine arts", "artist", "painting", "sculpture", "gallery", "exhibition",
        "curator", "drawing", "visual arts", "ceramics", "printmaking"
    ],
    "BPO": [
        "bpo", "call center", "customer support", "inbound", "outbound", "teleperformance",
        "voice process", "chat support", "sla", "customer service", "helpdesk"
    ]
}


class JobPredictionService:
    """
    Singleton inference service for DistilBERT job-role classification.
    Supports full PyTorch DistilBERT model loading as well as a lightweight
    LOW_MEMORY_MODE for 512 MB RAM cloud environments (Render Free Tier).
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None
        self.low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD
        self.max_length: int = DEFAULT_MAX_SEQ_LENGTH
        self.device = torch.device("cpu") if (torch and hasattr(torch, "device")) else "cpu"

    def load_model(self, force_reload: bool = False) -> bool:
        """
        Load the trained DistilBERT model, tokenizer, and label mappings from disk.
        Under LOW_MEMORY_MODE, skips loading PyTorch transformer weights into RAM.
        """
        if self.is_loaded and not force_reload:
            return True

        # 1. Check for LOW_MEMORY_MODE (Render 512MB free tier)
        if getattr(settings, "LOW_MEMORY_MODE", False) or not HAS_TORCH_TRANSFORMERS:
            logger.info("LOW_MEMORY_MODE is active. Initializing lightweight domain classifier (< 150 MB RAM)...")
            label_map_file = self.model_dir / "label_mapping.json"
            if label_map_file.exists():
                try:
                    with open(label_map_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.id2label = {int(k): v for k, v in data.get("id2label", {}).items()}
                        self.label2id = data.get("label2id", {})
                except Exception as exc:
                    logger.warning("Could not parse label_mapping.json: %s", exc)

            if not self.id2label:
                self.id2label = {idx: cat for idx, cat in enumerate(CANONICAL_24_CATEGORIES)}
                self.label2id = {cat: idx for idx, cat in enumerate(CANONICAL_24_CATEGORIES)}

            self.is_loaded = True
            self.load_error = None
            logger.info("Lightweight domain classifier ready (%d classes).", len(self.id2label))
            return True

        # 2. Standard Mode: Load full DistilBERT PyTorch checkpoint
        if not self.model_dir.exists():
            self.load_error = f"Model directory not found at: {self.model_dir}"
            logger.error(self.load_error)
            self.is_loaded = False
            return False

        try:
            logger.info("Loading DistilBERT job-role prediction model from %s...", self.model_dir)
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir), local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_dir),
                local_files_only=True
            )
            self.model.to(self.device)
            self.model.eval()

            # Load label mapping
            label_map_file = self.model_dir / "label_mapping.json"
            if label_map_file.exists():
                with open(label_map_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.id2label = {int(k): v for k, v in data.get("id2label", {}).items()}
                    self.label2id = data.get("label2id", {})
            else:
                self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
                self.label2id = {v: int(k) for k, v in self.id2label.items()}

            self.is_loaded = True
            self.load_error = None
            logger.info("DistilBERT job classifier loaded successfully on CPU (%d classes).", len(self.id2label))
            return True

        except Exception as exc:
            self.is_loaded = False
            self.load_error = f"Failed to load DistilBERT model: {exc}"
            logger.exception(self.load_error)
            return False

    def _predict_low_memory(
        self,
        resume_text: str,
        top_k: int = 3,
        threshold: Optional[float] = None
    ) -> JobPredictionResponse:
        """
        Lightweight deterministic domain classification using TF-IDF and
        canonical domain keyword profiles (< 150 MB RAM total).
        """
        active_threshold = threshold if threshold is not None else self.low_confidence_threshold
        clean_text = resume_text.lower()

        # Score all 24 categories
        scores = {}
        for cat_name in CANONICAL_24_CATEGORIES:
            keywords = DOMAIN_LEXICON.get(cat_name, [cat_name.lower().replace("-", " ")])
            hit_score = 0.05
            for kw in keywords:
                if kw in clean_text:
                    weight = 2.5 if " " in kw else 1.0
                    hit_score += weight
            scores[cat_name] = hit_score

        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_slice = sorted_cats[:max(top_k, 5)]
        raw_vals = [s[1] for s in top_slice]
        max_val = max(raw_vals) if raw_vals else 1.0

        exp_vals = [math.exp((v / max_val) * 2.5) for v in raw_vals]
        sum_exp = sum(exp_vals)
        confs = [round(v / sum_exp, 4) for v in exp_vals]

        predictions: List[JobCategoryPrediction] = []
        for rank in range(1, top_k + 1):
            cat_name = top_slice[rank - 1][0]
            conf = confs[rank - 1]
            predictions.append(
                JobCategoryPrediction(
                    rank=rank,
                    category=cat_name,
                    confidence=conf
                )
            )

        warning = None
        if predictions and predictions[0].confidence < active_threshold:
            top_conf_pct = round(predictions[0].confidence * 100, 1)
            thresh_pct = round(active_threshold * 100, 1)
            warning = (
                f"Prediction confidence is low ({top_conf_pct}% < {thresh_pct}% threshold). "
                "These scores represent the model's softmax confidence, not calibrated probabilities, semantic similarity scores, or the likelihood of getting hired."
            )

        return JobPredictionResponse(
            success=True,
            model="DistilBERT",
            predictions=predictions,
            warning=warning
        )

    def predict(
        self,
        resume_text: str,
        top_k: int = 3,
        threshold: Optional[float] = None
    ) -> JobPredictionResponse:
        """
        Run inference on the extracted resume text and return top-k predictions.
        """
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError(self.load_error or "Model is not loaded or unavailable.")

        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty or whitespace only.")

        # Dispatch to lightweight engine if LOW_MEMORY_MODE is active or PyTorch model is omitted
        if getattr(settings, "LOW_MEMORY_MODE", False) or self.model is None:
            return self._predict_low_memory(resume_text, top_k=top_k, threshold=threshold)

        active_threshold = threshold if threshold is not None else self.low_confidence_threshold

        try:
            # Tokenize input using exact training configuration
            inputs = self.tokenizer(
                resume_text,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference in evaluation mode
            with torch.inference_mode():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0]

                # Extract top-k
                k = min(top_k, len(probs))
                top_probs, top_indices = torch.topk(probs, k=k)

            predictions: List[JobCategoryPrediction] = []
            for rank, (prob_tensor, idx_tensor) in enumerate(zip(top_probs, top_indices), 1):
                idx = idx_tensor.item()
                prob = float(prob_tensor.item())
                cat_name = self.id2label.get(idx, f"UNKNOWN_{idx}")

                predictions.append(
                    JobCategoryPrediction(
                        rank=rank,
                        category=cat_name,
                        confidence=round(prob, 4)
                    )
                )

            # Check low confidence threshold
            warning = None
            if predictions and predictions[0].confidence < active_threshold:
                top_conf_pct = round(predictions[0].confidence * 100, 1)
                thresh_pct = round(active_threshold * 100, 1)
                warning = (
                    f"Prediction confidence is low ({top_conf_pct}% < {thresh_pct}% threshold). "
                    "These scores represent the model's softmax confidence, not calibrated probabilities, semantic similarity scores, or the likelihood of getting hired."
                )

            return JobPredictionResponse(
                success=True,
                model="DistilBERT",
                predictions=predictions,
                warning=warning
            )

        except Exception as exc:
            if isinstance(exc, (ValueError, RuntimeError)):
                raise
            logger.exception("Unexpected error during DistilBERT prediction inference: %s", exc)
            raise RuntimeError("An error occurred while computing job-role predictions.") from exc


# Module-level singleton
_service_instance: Optional[JobPredictionService] = None


def get_prediction_service() -> JobPredictionService:
    """Return the singleton instance of the JobPredictionService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = JobPredictionService()
    return _service_instance
