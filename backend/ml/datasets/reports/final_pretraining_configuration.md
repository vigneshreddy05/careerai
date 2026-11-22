# Final Pre-Training Configuration & Verification Report

> **Project:** CareerAI Job Role Prediction Engine (Phase 6 Final Pre-Training Gate)  
> **Model Target:** `distilbert-base-uncased` (24 Professional Categories)  
> **Dataset:** `opensporks/resumes` (LiveCareer mirror)  
> **Backend Pytest Status:** 15 passed, 0 failed  
> **Execution Status:** Pre-training validation complete (No ML packages installed, No training initiated)

---

## 1. Exact Duplicate Pairs Verification

A cryptographic SHA-256 audit on normalized resume text identified **two exact duplicate pairs** (4 rows total) within `opensporks/resumes`:

| Duplicate Group | Category | SHA-256 Digest | Record 1 ID | Record 2 ID | Assigned `cluster_id` | Partition Isolation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Group 1** | `FINANCE` | `5cab02555e6a...` | `opensporks_19147603` | `opensporks_28398216` | **1481** | **VERIFIED: Identical Cluster** |
| **Group 2** | `AVIATION` | `3df83b3566ad...` | `opensporks_16850314` | `opensporks_37473139` | **2431** | **VERIFIED: Identical Cluster** |

### Partition Isolation Proof
Because both members in each pair share the exact same `cluster_id`:
- In an 80/10/10 holdout split, both members are assigned to the **same split** (either Train, Validation, or Test).
- In 5-fold cross-validation, both members are placed in the **same fold**.
- **Result:** Pair members can **never** cross partition boundaries, completely eliminating evaluation leakage.

---

## 2. Dataset Population Decision: 2,481 Unique Resumes vs. 2,483 Usable Rows

The raw dataset contains 2,484 rows:
- **Empty Record (0 words):** Record `12632728` in `BUSINESS-DEVELOPMENT` (contains empty HTML divs). Excluded.
- **Usable Non-Empty Rows:** **2,483 rows**.
- **Unique Resumes:** **2,481 distinct resumes** (deduplicating the 2 redundant exact duplicate rows in Finance and Aviation).

### Recommendation: Train and Evaluate Exclusively on the 2,481 Unique Resumes
1. **Mathematical Fairness:** Retaining the 2 redundant duplicate rows in training artificially doubles the gradient weight of those two specific resumes with zero new linguistic or domain information.
2. **Evaluation Integrity:** Retaining duplicate rows in test partitions inflates test accuracy on those specific samples.
3. **Decision:** We formally adopt **$N = 2,481$ unique resumes** as the official population for training, cross-validation, and holdout evaluation.

---

## 3. Near-Duplicate and Exact-Duplicate Cluster Integrity

Using MinHash LSH ($Jaccard \ge 0.80$) and Disjoint Set Union (DSU), we grouped all exact and near-duplicate resumes into **2,469 disjoint clusters**:
- **Singleton Clusters:** 2,456 (resumes with no near-duplicates).
- **Multi-Member Clusters:** 13 clusters comprising 27 resumes.

### Partition Disjointness Check
In both our 80/10/10 holdout split and 5-fold cross-validation algorithms:
$$\text{Clusters}(\text{Train}) \cap \text{Clusters}(\text{Val}) = \emptyset$$
$$\text{Clusters}(\text{Train}) \cap \text{Clusters}(\text{Test}) = \emptyset$$
$$\text{Clusters}(\text{Val}) \cap \text{Clusters}(\text{Test}) = \emptyset$$
All cluster groups remain strictly intact. **Zero near-duplicate crossover occurs.**

---

## 4. Five-Fold Group-Stratified Cross-Validation Feasibility

We simulated 5-Fold Group-Stratified Cross-Validation across all 24 categories on the 2,481 unique resumes.

### Complete Per-Fold Class Census (24 Categories)

| Category Name | Total Unique | Fold 1 (Test) | Fold 2 (Test) | Fold 3 (Test) | Fold 4 (Test) | Fold 5 (Test) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INFORMATION-TECHNOLOGY** | 120 | 24 | 24 | 24 | 25 | 23 |
| **BUSINESS-DEVELOPMENT** | 119 | 24 | 25 | 24 | 23 | 23 |
| **ACCOUNTANT** | 118 | 24 | 24 | 24 | 23 | 23 |
| **ADVOCATE** | 118 | 25 | 24 | 23 | 23 | 23 |
| **CHEF** | 118 | 24 | 24 | 23 | 24 | 23 |
| **ENGINEERING** | 118 | 24 | 23 | 23 | 25 | 23 |
| **FINANCE** | 117 | 24 | 23 | 23 | 23 | 24 |
| **FITNESS** | 117 | 24 | 24 | 23 | 23 | 23 |
| **AVIATION** | 116 | 24 | 23 | 23 | 23 | 23 |
| **SALES** | 116 | 23 | 23 | 23 | 24 | 23 |
| **BANKING** | 115 | 23 | 23 | 23 | 23 | 23 |
| **CONSULTANT** | 115 | 23 | 23 | 23 | 23 | 23 |
| **HEALTHCARE** | 115 | 23 | 24 | 23 | 23 | 22 |
| **CONSTRUCTION** | 112 | 23 | 23 | 22 | 22 | 22 |
| **PUBLIC-RELATIONS** | 111 | 23 | 22 | 22 | 22 | 22 |
| **HR** | 110 | 22 | 22 | 23 | 22 | 21 |
| **DESIGNER** | 107 | 22 | 22 | 21 | 21 | 21 |
| **ARTS** | 103 | 21 | 21 | 21 | 20 | 20 |
| **TEACHER** | 102 | 21 | 21 | 20 | 20 | 20 |
| **APPAREL** | 97 | 20 | 20 | 19 | 19 | 19 |
| **DIGITAL-MEDIA** | 96 | 20 | 19 | 19 | 19 | 19 |
| **AGRICULTURE** | **63** | **13** | **13** | **13** | **12** | **12** |
| **AUTOMOBILE** | **36** | **8** | **7** | **7** | **7** | **7** |
| **BPO** | **22** | **5** | **5** | **4** | **4** | **4** |
| **TOTAL PER FOLD** | **2,481** | **507** | **502** | **493** | **493** | **486** |

### Detailed Evaluation for Low-Sample Classes
- **BPO (Total 22):** Folds contain `[5, 5, 4, 4, 4]` test samples. In each fold, 17 to 18 BPO resumes are used for training. In contrast to an 80/10/10 split where test has only 2 samples, 5-fold CV evaluates **all 22 BPO resumes out-of-fold**, making Macro F1 highly reliable.
- **Automobile (Total 36):** Folds contain `[8, 7, 7, 7, 7]` test samples (28–29 training samples per fold).
- **Agriculture (Total 63):** Folds contain `[13, 13, 13, 12, 12]` test samples (50–51 training samples per fold).

**Verdict:** 5-Fold Group-Stratified Cross-Validation is **fully feasible, balanced, and statistically superior** to a single holdout split.

---

## 5. Correct Training Step Calculations

For $N = 2,481$ unique resumes:
- **80% Training Partition:** $N_{\text{train}} = 1,985$ samples
- **10% Validation Partition:** $N_{\text{val}} = 248$ samples
- **10% Test Partition:** $N_{\text{test}} = 248$ samples

The number of gradient steps per epoch is calculated as $\lceil N_{\text{train}} / \text{batch\_size} \rceil$:

### Step Counts Table (Static 80/10/10 Split, $N_{\text{train}} = 1,985$)

| Epochs | Batch Size 16 ($\lceil 1985/16 \rceil = \mathbf{125}$ steps/epoch) | 10% Warmup Steps | Batch Size 8 ($\lceil 1985/8 \rceil = \mathbf{249}$ steps/epoch) | 10% Warmup Steps |
| :--- | :--- | :--- | :--- | :--- |
| **1 Epoch** | **125 steps** | 12 steps | **249 steps** | 25 steps |
| **2 Epochs** | **250 steps** | 25 steps | **498 steps** | 50 steps |
| **3 Epochs** | **375 steps** | 38 steps | **747 steps** | 75 steps |
| **4 Epochs** | **500 steps** | 50 steps | **996 steps** | 100 steps |
| **5 Epochs** | **625 steps** | 62 steps | **1,245 steps** | 124 steps |

### Step Counts Table (5-Fold Cross-Validation, 4/5 Train = 1,985 per fold)

| Strategy | Batch Size 16 Steps | Batch Size 8 Steps |
| :--- | :--- | :--- |
| **Per Fold, 1 Epoch** | 125 steps | 249 steps |
| **Per Fold, 3 Epochs** | 375 steps | 747 steps |
| **Full 5-Fold Run (3 Epochs $\times$ 5 Folds)** | **1,875 total steps** | **3,735 total steps** |

---

## 6. Training Duration & Hardware Performance Statement

> **Training Duration Status: UNKNOWN (Pending Empirical Benchmark)**  
> Prior estimates of 1.5–2.5 minutes were theoretical projections. Exact wall-clock runtime on Windows with 12 logical CPU cores depends on:
> 1. PyTorch CPU backend threading (`torch.set_num_threads`) and Intel oneDNN/MKL optimizations.
> 2. CPU clock speed, thermal throttling, and cache contention during self-attention computation.
> 3. Subword token sequence length ($O(L^2)$ attention complexity).
> 
> Therefore, training duration is marked as **UNKNOWN** until the single-epoch CPU benchmark is executed.

---

## 7. Small CPU Benchmark Configuration (256 Tokens, 1 Epoch)

To establish real baseline throughput, memory, and runtime, we have prepared the following benchmark protocol:

### Benchmark Specification
- **Model:** `distilbert-base-uncased` (66M parameters)
- **Sequence Length:** **256 tokens** (captures headline, summary, core skills, and most recent job)
- **Batch Size:** 16 (fallback to 8 if memory pressure occurs)
- **Duration:** Exactly **1 epoch** (125 steps at batch size 16)
- **Hardware Metrics Recorded:**
  - **Wall-Clock Time:** High-resolution timing via `time.perf_counter()`.
  - **Throughput:** Samples per second ($N / \Delta t$) and steps per second.
  - **Peak Memory:** Resident Set Size (RSS) via `tracemalloc.get_traced_memory()` and `psutil.Process().memory_info().rss`.
  - **Loss Trajectory:** Initial loss vs final batch loss.

---

## 8. Optional 384-Token Sequence Length Comparison

We have prepared an optional comparison configuration to evaluate whether increasing the sequence length from 256 to 384 tokens improves Macro F1:
- **Sequence Length:** **384 tokens** (~270 words)
- **Theoretical Attention Cost:** $(384 / 256)^2 = 2.25\times$ more self-attention matrix operations per layer.
- **Execution Status:** **Preserved but NOT executed yet**. Will only be run after the 256-token baseline benchmark completes and receives user approval.

---

## 9. Three Diagnostic Masking Experiments

Target leakage analysis revealed that 91.93% of resumes contain explicit role keywords. To measure the model's true reliance on skills versus title keywords, we have designed three diagnostic ablation models:

### Essential Methodological Clarifications
1. **Masking is a Diagnostic Tool, Not Data Cleaning:** Masking can remove useful, legitimate domain information (e.g., an IT professional stating *"Software Engineer"* is standard, valid resume text).
2. **Purpose of the Three Models:**
   - **Model 1 (Unmasked Baseline):** Establishes the performance ceiling under standard conditions.
   - **Model 2 (Header-Masked):** Tests whether the model over-fits specifically to the standardized LiveCareer line-1 job banner while leaving all body text untouched.
   - **Model 3 (Entity-Masked):** Tests whether the model can classify resumes strictly from skills, responsibilities, tools, and context when explicit title words are obscured.
3. **Outcome Metric:** The leakage gap $\Delta = \text{Macro-F1}_{\text{unmasked}} - \text{Macro-F1}_{\text{masked}}$ directly measures how robust the classifier is to resumes with unfamiliar or omitted job titles.

---

## 10. Evaluation Metrics Hierarchy

Because class sizes range from 120 (`INFORMATION-TECHNOLOGY`) down to 22 (`BPO`), evaluation must not be obscured by simple overall accuracy.

### Metrics Specification Table

| Priority | Metric | Formula / Definition | Purpose in CareerAI |
| :--- | :--- | :--- | :--- |
| **PRIMARY** | **Macro F1** | $\frac{1}{24} \sum_{c=1}^{24} F1_c$ | Gives equal weight to every category. Prevents high accuracy on large classes from concealing poor performance on minority classes (e.g. BPO, Automobile). |
| **Secondary** | **Weighted F1** | $\sum_{c=1}^{24} \frac{N_c}{N} F1_c$ | Measures overall population-weighted classification quality. |
| **Secondary** | **Accuracy** | $\frac{N_{\text{correct}}}{N}$ | General diagnostic metric for overall correct predictions. |
| **Per-Class** | **Class Precision & Recall** | $P_c = \frac{TP_c}{TP_c + FP_c}$, $R_c = \frac{TP_c}{TP_c + FN_c}$ | Monitored individually for all 24 classes, with special focus on `BPO`, `AUTOMOBILE`, and `AGRICULTURE`. |
| **Diagnostic** | **$24 \times 24$ Confusion Matrix** | Heatmap matrix of true vs predicted labels | Identifies cross-domain semantic confusion (e.g., `ACCOUNTANT` vs `FINANCE`, `HR` vs `CONSULTANT`, `DIGITAL-MEDIA` vs `ARTS`). |

---

## 11. Verification Checks Performed & Unresolved Issues

### Checks Performed
- [x] Verified exact duplicate pairs: Group 1 (`FINANCE`) and Group 2 (`AVIATION`) have identical `cluster_id`s (1481 and 2431) and cannot cross partitions.
- [x] Established population size: Adopted 2,481 unique resumes for all training and evaluation.
- [x] Verified cluster integrity: Pairwise disjoint partition verification confirmed 0 crossover across Train, Val, and Test.
- [x] Validated 5-fold cross-validation: Simulated all 24 classes across 5 folds; confirmed BPO has 4–5 test samples per fold.
- [x] Corrected training steps: 125 steps/epoch for batch size 16; 249 steps/epoch for batch size 8.
- [x] Corrected duration claims: Marked runtime as UNKNOWN pending empirical benchmarking.
- [x] Designed CPU benchmark protocol: 256 tokens, 1 epoch, recording wall-clock time and peak memory.
- [x] Preserved 384-token comparison specification without executing it.
- [x] Documented diagnostic masking ablation methodology.
- [x] Formalized metrics hierarchy: Macro F1 established as primary metric.
- [x] Verified 15/15 existing backend tests pass (`15 passed in 0.85s`).

### Unresolved Issues
- **None.** All 10 user requirements have been fully verified, calculated, and documented.
- Zero packages have been installed; zero models have been trained; the environment and application code remain completely intact.
