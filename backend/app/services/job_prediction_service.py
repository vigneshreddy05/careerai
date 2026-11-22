"""
Job Role Prediction Inference Service for CareerAI
Loads the trained DistilBERT sequence classification model once on CPU
and delivers top-3 predicted job categories with confidence scores and
low-confidence warnings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    from backend.app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionResponse,
    )
except ModuleNotFoundError:
    from app.schemas.prediction import (
        JobCategoryPrediction,
        JobPredictionResponse,
    )

logger = logging.getLogger(__name__)

# Default model directory
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "saved_models" / "distilbert_job_classifier"
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.40
DEFAULT_MAX_SEQ_LENGTH = 256


class JobPredictionService:
    """
    Singleton inference service for DistilBERT job-role classification.
    Ensures model weights and tokenizer are loaded into memory only once.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.model: Optional[AutoModelForSequenceClassification] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None
        self.low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD
        self.max_length: int = DEFAULT_MAX_SEQ_LENGTH
        self.device = torch.device("cpu")

    def load_model(self, force_reload: bool = False) -> bool:
        """
        Load the trained DistilBERT model, tokenizer, and label mappings from disk.
        Returns True if successful, False otherwise.
        """
        if self.is_loaded and not force_reload:
            return True

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
                # Fallback to model config
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
            # Try to load if not already loaded
            if not self.load_model():
                raise RuntimeError(self.load_error or "Model is not loaded or unavailable.")

        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty or whitespace only.")

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
