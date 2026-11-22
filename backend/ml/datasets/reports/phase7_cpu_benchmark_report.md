# Phase 7: Controlled One-Epoch DistilBERT CPU Benchmark Report

> **Project:** CareerAI Job Role Prediction Engine  
> **Model Target:** `distilbert-base-uncased` (24 Professional Categories)  
> **Hardware:** Intel Core i7-1355U (10 Cores / 12 Logical Processors), 16 GB RAM, Intel Iris Xe (CPU only)  
> **Benchmark Outcome:** **COMPLETED SUCCESSFULLY (Exit Code 0)**  
> **Backend Pytest Status:** **15 passed, 0 failed (0.84s)**  
> **Frontend Build Status:** **Passed (Vite production build 7.85s)**

---

## 1. Environment & Installed Package Versions

The required machine learning packages were installed into the existing project virtual environment (`.venv`). No global packages were installed, and CUDA dependencies were omitted:

| Package Name | Installed Version | Build / Target | Status |
| :--- | :--- | :--- | :--- |
| **PyTorch** | `2.15.0+cpu` | CPU-only wheel (OpenMP/MKL) | Verified (`torch.device('cpu')`) |
| **Transformers** | `5.24.0` | Hugging Face NLP library | Verified |
| **Scikit-learn** | `1.9.1` | Metrics & evaluation | Verified |
| **psutil** | `7.2.2` | Process & hardware monitoring | Verified |
| **NumPy** | `2.4.6` | Numerical computing | Verified |
| **CUDA Available** | **False** | Intentionally disabled (No NVIDIA GPU) | Verified |

- **Dependency Consistency (`pip check`):** `No broken requirements found.`
- **Application Compatibility:** All 15 existing backend tests pass without errors or warnings.

---

## 2. Benchmark Architecture & Dataset Split

The benchmark was executed using the primary sanitized dataset (`opensporks_sanitized.csv`), deduplicated to $N = 2,481$ unique resumes across the 24 categories:

- **Partition Isolation:** Verified **0 cluster crossover** between Train, Validation, and Test sets.
- **Tokenization:** `distilbert-base-uncased` tokenizer with `max_length=256`, completed in **1.23 seconds** (1,608.4 samples/second).

---

## 3. Empirical Benchmark Measurements (1 Full Epoch)

The benchmark executed **1 complete training epoch** consisting of 124 gradient steps on 1,979 training samples:

| Metric | Measured Value | Notes & Analysis |
| :--- | :--- | :--- |
| **Total Elapsed Training Time** | **1,125.73 seconds (18.76 minutes)** | Measured with `time.perf_counter()` |
| **Average Step Time** | **9.078 seconds / step** | 16 samples processed per gradient step |
| **Throughput** | **1.76 samples / second** | 0.11 steps / second |
| **Initial Process RSS Memory** | **1,038.11 MB** (~1.01 GB) | Baseline with model & tokenizer loaded |
| **Peak Process RSS Memory** | **2,052.20 MB (2.00 GB)** | Maximum resident memory during backward pass |
| **Final Process RSS Memory** | **1,290.21 MB** (~1.26 GB) | Post-training memory state |
| **Safety Threshold Margin** | **2.00 GB vs. 12.0 GB limit** | Consumed only 16.7% of safety ceiling |
| **Average CPU Utilization** | **78.2%** | Utilizing 8 PyTorch worker threads |
| **Loss Trajectory** | **$3.1719 \rightarrow 2.1078$** | Steady descent across 124 steps |
| **Checkpoint Saved** | `backend/ml/saved_models/benchmark_checkpoint` | Complete 268 MB `model.safetensors` + config |

---

## 4. Hardware Limitations & Duration Analysis

Now that we have **real empirical data** from the laptop's Intel Core i7-1355U CPU:

### Wall-Clock Time Projections for Future Phases

| Experiment / Task | Total Epochs | Projected Runtime on Intel i7-1355U CPU | Projected Runtime on Free T4 GPU (Colab) |
| :--- | :--- | :--- | :--- |
| **Single 3-Epoch Model** (e.g. Unmasked Baseline) | 3 epochs | **~56.3 minutes** (~1 hour) | **~30 to 45 seconds** |
| **Three Masking Ablations** (Unmasked + Header + Entity) | 9 epochs | **~2.8 hours** | **~2 to 3 minutes** |
| **Full 5-Fold Cross-Validation** (5 folds $\times$ 3 epochs) | 15 epochs | **~4.7 hours** | **~3.5 to 5 minutes** |

### Memory & Stability Assessment
- **Stability:** **Excellent**. The process ran continuously for 18.76 minutes with zero crashes, zero memory leaks, and no thermal aborts.
- **Memory Footprint:** Peak RSS was **2.00 GB**, leaving ~13.7 GB of total RAM available on the machine. Batch size 16 did not cause swapping or out-of-memory errors. There is no need to downscale to batch size 8 for memory reasons (which would double the step count to 249 steps and increase overhead).

---

## 5. Strategic Recommendations for Next Phase

We have two fully viable execution paths:

### Option A: Local CPU Training (100% Offline & Free)
- **Feasible Scope:** Train a single, high-quality **3-epoch DistilBERT model** on the holdout split (80% Train, 10% Val, 10% Test).
- **Expected Runtime:** **~56 minutes**.
- **Pros:** Completely self-contained, no external accounts needed, model weights save directly into `backend/ml/saved_models/`.
- **Limitation:** Running full 5-fold cross-validation or all 3 masking variants locally would tie up CPU resources for 3 to 5 hours.

### Option B: Hybrid Cloud Acceleration (Google Colab Free Tier)
- **Feasible Scope:** Run the full 5-fold cross-validation and the 3 diagnostic masking experiments using a free Google Colab T4 GPU notebook.
- **Expected Runtime:** **~3 to 5 minutes total** for all 15 epochs.
- **Pros:** 40x faster; allows thorough 5-fold cross-validation and ablation studies without tying up the laptop CPU.
- **Limitation:** Requires uploading the clean `opensporks_sanitized.csv` file to Google Drive / Colab and downloading the final model weights back to the local repository.

---

## 6. Verification Status Summary

- [x] PyTorch CPU wheel installed and verified (`2.15.0+cpu`).
- [x] Hugging Face `transformers`, `scikit-learn`, `psutil` installed cleanly.
- [x] Zero broken requirements (`python -m pip check` passed).
- [x] 1-epoch controlled benchmark completed with exit code 0.
- [x] Empirical time (18.76 min), throughput (1.76 samples/s), and peak memory (2.00 GB) recorded.
- [x] Checkpoint saved successfully in `backend/ml/saved_models/benchmark_checkpoint`.
- [x] Backend tests: **15 passed, 0 failed in 0.84s**.
- [x] Frontend build: **Built in 7.85s**.
- [x] Preserved all previous audit files and reports.
