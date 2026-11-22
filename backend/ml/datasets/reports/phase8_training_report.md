# Phase 8: First DistilBERT Job Role Prediction Model Training Report

> **Project:** CareerAI Job Prediction & Career Recommendation System  
> **Model Target:** `distilbert-base-uncased` (24 Professional Categories)  
> **Hardware:** Intel Core i7-1355U (10 Cores / 12 Threads), 16 GB RAM, CPU only  
> **Training Status:** **COMPLETED SUCCESSFULLY (3 Epochs, 372 Gradient Steps)**  
> **Final Test Accuracy:** **82.87%**  
> **Final Test Macro F1:** **0.7696** (Weighted F1: **0.8148**)  
> **Best Model Checkpoint:** `backend/ml/saved_models/distilbert_job_classifier/`  
> **Backend Pytest Status:** **15 passed, 0 failed (0.94s)**  
> **Frontend Build Status:** **Passed (4.32s)**

---

## 1. Executive Summary

In Phase 8, we trained the first working DistilBERT job-role classification model entirely on the local CPU (`Intel Core i7-1355U`) using the approved primary dataset (`opensporks/resumes`). The training completed in **50.44 minutes** across 3 full epochs (372 total gradient steps) with stable resource utilization (peak process RSS: **1.75 GB**, average CPU load: **72.3%**).

---

## 2. Dataset & Partition Breakdown

The training pipeline utilized exclusively the sanitized primary dataset (`opensporks_sanitized.csv`), deduplicated to $N = 2,481$ unique resumes:
- **Total Unique Resumes:** 2,481 across 24 professional categories.
- **Training Set (79.8%):** 1,979 resumes (124 steps per epoch at batch size 16).
- **Validation Set (10.1%):** 251 resumes (used strictly for end-of-epoch checkpoint selection).
- **Test Set (10.1%):** 251 resumes (held out completely untouched until final evaluation).
- **Group Isolation:** Verified **0 cluster crossover** between partitions using MinHash LSH / SHA-256 cluster IDs.

---

## 3. Model & Hyperparameter Configuration

| Hyperparameter | Value | Rationale |
| :--- | :--- | :--- |
| **Base Architecture** | `distilbert-base-uncased` | Lightweight (66.9M params), fast CPU execution, 256 subword capacity. |
| **Output Classes** | **24 categories** | Broad industry professional categories. |
| **Max Sequence Length** | **256 tokens** | Captures executive summary, top skills, and recent work history. |
| **Batch Size** | **16** | Empirically verified safe batch size from Phase 7 benchmark. |
| **Epochs** | **3** | Exactly 3 epochs ($124 \times 3 = 372$ total gradient steps). |
| **Learning Rate** | **$2 \times 10^{-5}$** | Standard AdamW rate for DistilBERT classification head tuning. |
| **Optimizer** | **AdamW** | Weight decay = 0.01. |
| **Learning Rate Schedule** | Linear Warmup + Decay | 10% warmup (37 steps), followed by linear decay to 0.0. |
| **Loss Function** | **Weighted Cross-Entropy** | Balanced class weights ($W_c = \frac{N_{\text{train}}}{24 \times N_{\text{train}, c}}$): $W_{\text{BPO}} = 4.5810$ to $W_{\text{IT}} = 0.8589$. |

---

## 4. Hardware Resource Monitoring & Duration

| Resource Metric | Recorded Value | Status & Observations |
| :--- | :--- | :--- |
| **Total Wall-Clock Training Time** | **50.44 minutes (3,026.64 seconds)** | ~16.8 minutes per epoch average |
| **Peak Process RSS Memory** | **1,795.93 MB (1.75 GB)** | Well within 16 GB RAM; zero memory leakage |
| **System RAM Usage Range** | **60.1% to 67.1%** | Safely below the 90.0% safety abort threshold |
| **Average CPU Load** | **72.3%** | Efficiently distributed across 8 PyTorch CPU worker threads |
| **Throughput** | **1.96 samples / second** | 0.12 steps / second (~8.1 seconds per batch) |

---

## 5. Epoch-by-Epoch Training & Validation Progression

Validation metrics were computed at the end of each epoch on the 251 validation resumes. The model with the highest **Validation Macro F1** was automatically saved as the best checkpoint:

| Epoch | Train Loss | Validation Loss | Validation Accuracy | Validation Macro F1 (Primary) | Validation Weighted F1 | Epoch Runtime | Checkpoint Action |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Epoch 1** | 2.9985 | 2.4100 | 66.53% | **0.5753** | 0.6226 | 16.09 min | Saved initial best |
| **Epoch 2** | 2.0227 | 1.5489 | 78.49% | **0.6995** | 0.7597 | 15.79 min | Saved new best (+0.1242) |
| **Epoch 3** | 1.5230 | 1.3782 | 79.28% | **0.7172** | 0.7729 | 16.93 min | **Saved final best (+0.0177)** |

---

## 6. Final Test Evaluation (Untouched Test Partition, $N = 251$)

The best checkpoint (Epoch 3, Validation Macro F1 = 0.7172) was loaded from disk and evaluated **exactly once** on the untouched holdout test partition:

### Primary & Overall Test Metrics

| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **Overall Accuracy** | **82.87%** | 208 out of 251 test resumes correctly predicted |
| **Macro F1 (Primary Metric)** | **0.7696** (76.96%) | Unweighted arithmetic mean across all 24 categories |
| **Weighted F1** | **0.8148** (81.48%) | Sample-weighted average across all classes |
| **Macro Precision** | **0.8034** (80.34%) | Average precision across all classes |
| **Macro Recall** | **0.7763** (77.63%) | Average recall across all classes |
| **Test Loss** | **1.3352** | Consistent with validation loss (no severe overfitting) |

---

## 7. Per-Category Performance Breakdown

Complete classification report across all 24 professional categories:

| Category Name | Support (Test N) | Precision | Recall | F1-Score | Qualitative Tier |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **ACCOUNTANT** | 12 | **1.0000** | **1.0000** | **1.0000** | Perfect Classification |
| **BUSINESS-DEVELOPMENT** | 12 | **1.0000** | **1.0000** | **1.0000** | Perfect Classification |
| **ENGINEERING** | 12 | **1.0000** | **1.0000** | **1.0000** | Perfect Classification |
| **HR** | 11 | **1.0000** | **1.0000** | **1.0000** | Perfect Classification |
| **DESIGNER** | 11 | 0.9167 | **1.0000** | **0.9565** | Exceptional ($>0.95$) |
| **SALES** | 12 | 0.8571 | **1.0000** | **0.9231** | Exceptional ($>0.90$) |
| **CONSTRUCTION** | 11 | 0.8462 | **1.0000** | **0.9167** | Exceptional ($>0.90$) |
| **CONSULTANT** | 12 | 0.8000 | **1.0000** | **0.8889** | High ($0.85 - 0.90$) |
| **FINANCE** | 12 | 0.8000 | **1.0000** | **0.8889** | High ($0.85 - 0.90$) |
| **INFORMATION-TECHNOLOGY** | 12 | 0.8462 | 0.9167 | **0.8800** | High ($0.85 - 0.90$) |
| **TEACHER** | 10 | 0.7692 | **1.0000** | **0.8696** | High ($0.85 - 0.90$) |
| **FITNESS** | 12 | 0.9000 | 0.7500 | **0.8182** | Good ($0.80 - 0.85$) |
| **CHEF** | 12 | 0.7333 | 0.9167 | **0.8148** | Good ($0.80 - 0.85$) |
| **AGRICULTURE** | 6 | **1.0000** | 0.6667 | **0.8000** | Good ($0.80 - 0.85$) |
| **HEALTHCARE** | 11 | 0.8889 | 0.7273 | **0.8000** | Good ($0.80 - 0.85$) |
| **PUBLIC-RELATIONS** | 11 | **1.0000** | 0.6364 | **0.7778** | Moderate ($0.75 - 0.80$) |
| **DIGITAL-MEDIA** | 10 | 0.6429 | 0.9000 | **0.7500** | Moderate ($0.75 - 0.80$) |
| **AVIATION** | 12 | 0.6923 | 0.7500 | **0.7200** | Moderate ($0.70 - 0.75$) |
| **BANKING** | 12 | 0.7273 | 0.6667 | **0.6957** | Moderate ($0.65 - 0.70$) |
| **ADVOCATE** | 12 | 0.5625 | 0.7500 | **0.6429** | Moderate ($0.60 - 0.65$) |
| **APPAREL** | 10 | 0.8000 | 0.4000 | **0.5333** | Challenging ($0.50 - 0.60$) |
| **ARTS** | 10 | **1.0000** | 0.3000 | **0.4615** | Challenging (overlaps with Teaching/Design) |
| **AUTOMOBILE** | 4 | 0.5000 | 0.2500 | **0.3333** | Sparse Class (4 test samples) |
| **BPO** | 2 | 0.0000 | 0.0000 | **0.0000** | Extreme Scarcity (2 test samples) |

---

## 8. Misclassification & Confusion Matrix Insights

Analysis of the $24 \times 24$ confusion matrix (`backend/ml/evaluation/confusion_matrix.json`):

1. **Perfect Separation:** `ACCOUNTANT`, `BUSINESS-DEVELOPMENT`, `ENGINEERING`, and `HR` achieved 100% recall with 0 false negatives.
2. **The Minority Scarcity Effect on BPO and Automobile:**
   - **BPO (Support = 2):** With only 2 test samples, both were misclassified (1 as `ADVOCATE`, 1 as `APPAREL`). Because precision and recall were 0.0, this single minority class reduced the overall unweighted Macro F1 by ~3.2 percentage points (from ~80.2% down to 76.96%).
   - **Automobile (Support = 4):** 1 correct, 3 misclassified (predicted as `ADVOCATE`, `BANKING`, and `CONSULTANT`).
3. **Semantic Boundary Overlap:**
   - **Arts (Support = 10, Recall = 30%):** Misclassified as `TEACHER` (2), `DESIGNER` (1), `DIGITAL-MEDIA` (1), and `SALES` (1). Resumes of art instructors and graphic artists naturally share vocabulary with teaching and digital design.
   - **Apparel (Support = 10, Recall = 40%):** Misclassified as `DESIGNER` (1), `DIGITAL-MEDIA` (1), `SALES` (1), and `ADVOCATE` (2).

---

## 9. Checkpoint & Artifacts Preserved

All training checkpoints and evaluation artifacts have been saved under proper directory structures:

- **Best Model Checkpoint:**
  - `backend/ml/saved_models/distilbert_job_classifier/`
    - `model.safetensors` (268 MB)
    - `config.json`
    - `tokenizer.json` & `tokenizer_config.json`
    - `label_mapping.json` (maps 24 strings to label IDs)
    - `training_summary.json` (complete training telemetry)
- **Epoch Checkpoints:**
  - `backend/ml/saved_models/epoch_checkpoints/epoch_1.pt`
  - `backend/ml/saved_models/epoch_checkpoints/epoch_2.pt`
  - `backend/ml/saved_models/epoch_checkpoints/epoch_3.pt`
- **Evaluation Outputs:**
  - `backend/ml/evaluation/test_metrics.json`
  - `backend/ml/evaluation/per_category_metrics.json`
  - `backend/ml/evaluation/classification_report.txt`
  - `backend/ml/evaluation/confusion_matrix.json`
  - `backend/ml/evaluation/confusion_matrix.csv`

---

## 10. Suitability for Further Development & Important Limitations

> **Model Suitability Verdict:**
> The model is **highly suitable as our Phase 8 foundational job-role prediction engine**. Achieving **82.87% overall accuracy** and **0.7696 Macro F1** across 24 diverse categories with only 3 CPU fine-tuning epochs demonstrates strong contextual feature learning.

### Limitations & Ethical Disclaimers
1. **Model Confidence $\neq$ Hiring Probability:** The model outputs a softmax probability distribution indicating linguistic similarity to historical resume profiles in that category. It **does NOT** represent a candidate's likelihood of being hired or their qualification quality.
2. **Data Scarcity in Minority Classes:** Categories with fewer than 40 samples (`BPO`, `AUTOMOBILE`) require data augmentation or 5-fold cross-validation before their specific scores can be considered conclusive.
3. **Target Title Leakage:** The current model was evaluated on unmasked sanitized resumes. In future phases, comparing against header-masked and entity-masked models will determine how much accuracy relies on verbatim title words versus latent skills.
4. **Not Production-Ready:** This model is an experimental research prototype. It requires inference API integration, confidence thresholding, and top-3 recommendation ranking before user-facing deployment.
