# CareerAI Phase 6: Dataset Quality & Sanitization Audit Report

**Audit Execution Timestamp:** 2026-11-21T18:02:40.763693

## 1. Executive Summary

- **Total Records Analyzed:** 3446 (2484 primary opensporks + 962 supplementary Gaurav Dutta)
- **Unique Resume Texts:** 2648 (798 redundant exact duplicates)
- **Near-Duplicate Pairs Detected:** 3090 (at Jaccard similarity threshold $\ge 0.8$)
- **Cluster Groups Formed:** 2636 cluster IDs assigned for Group-Stratified splitting
- **Short Records (< 50 words):** 30 records flagged for review (none auto-deleted)
- **Non-ASCII Characters:** 2666 records (77.37%) contain preserved international characters
- **Personally Identifiable Information:** 227 records (6.59%) contained emails/phones/URLs; all masked to `[EMAIL]`, `[PHONE]`, `[URL]` in sanitized copy
- **Target Leakage Risk:** 91.93% of resumes contain explicit category keywords
- **Zero Code Regressions:** All 15 existing backend tests pass cleanly

---

## 2. Dataset Ingestion & Overview

| Metric | Primary (`opensporks/resumes`) | Supplementary (`gaurav_dutta`) | Combined |
| :--- | :--- | :--- | :--- |
| **Raw Record Count** | 2484 | 962 | 3446 |
| **Number of Classes** | 24 | 25 | 48 |
| **Empty Records (0 words)** | 1 | 0 | 1 |
| **Short Records (< 50 words)** | 0 | 30 | 30 |
| **Mean Word Count** | 817.02 | 445.22 | 713.23 |
| **Median Word Count** | 761 | 320 | 709 |
| **Unique Resume Texts** | 2482 | 166 | 2648 |

> [!IMPORTANT]
> **Crucial Quality Finding on Gaurav Dutta Dataset:**
> The Gaurav Dutta dataset contains only **166 unique resumes** repeated across 962 rows (796 redundant exact duplicate rows).
> If split naively without cluster-group tracking, train and test sets would share identical resumes, causing massive evaluation leakage.

---

## 3. Duplicate and Cluster Audit

### Exact Duplicates (SHA-256 on Normalized Text)
- **Total Exact Duplicate Groups:** 164
- **Total Rows in Duplicate Groups:** 962
- **Cross-Dataset Duplication:** 0 groups (0 overlap between opensporks and Gaurav Dutta)

### Near Duplicates (MinHash + Jaccard Similarity)
- **MinHash Configuration:** 32 permutation hashes, 8 LSH bands (4 rows/band)
- **Pairs with Jaccard $\ge 0.80$:** 3090
- **Similarity Breakdown:**
  - $\ge 0.95$: 3081 pairs
  - $0.90 - 0.95$: 4 pairs
  - $0.80 - 0.90$: 5 pairs
  - $0.70 - 0.80$: 6 pairs

### Cluster Group Assignment (`cluster_id`)
- **Total Clusters Formed:** 2636
- **Singleton Clusters:** 2461
- **Multi-Member Clusters:** 175
- **Data Leakage Mitigation:** Every record in the sanitized copy now contains `cluster_id`. In Phase 7, GroupShuffleSplit or GroupKFold will ensure all members of a cluster remain in either Train OR Test, never split across both.

---

## 4. Short Records & Non-ASCII Character Audit

### Short Records (< 50 words)
- Total flagged records: 30 (0 in opensporks, 30 in Gaurav Dutta).
- **Opensporks Record (ID `opensporks_12632728`):** 0 words (completely empty div stubs in HTML, empty text). Recommended for exclusion during model training.
- **Gaurav Dutta Short Records (30 rows):** Primarily 6 distinct resume snippets (e.g. short HR credentials, Advocate qualifications) repeated 4-5 times each. Kept in sanitized dataset with flag `is_short=True`.

### Non-ASCII Character Audit
- **Records Containing Non-ASCII:** 2666 (77.37%)
- **Character Types Detected:** Unicode typographic quotes (`‘`, `’`, `“`, `”`), en/em-dashes (`–`, `—`), bullet points (`•`, `·`), accented Latin characters (`é`, `ü`, `ñ`), and non-breaking spaces.
- **Preservation Status:** All non-ASCII characters have been preserved intact in both raw and processed files.

---

## 5. PII Audit & Sanitization Summary

| PII Entity | Detections Count | Unique Instances | Sanitization Replacement |
| :--- | :--- | :--- | :--- |
| **Email Addresses** | 40 | 35 | `[EMAIL]` |
| **Phone Numbers** | 234 | 203 | `[PHONE]` |
| **URLs / Web Links** | 346 | 183 | `[URL]` |

> [!NOTE]
> Raw data files under `backend/ml/datasets/raw/` remain completely untouched.
> Sanitized copies under `backend/ml/datasets/processed/` have all contact identifiers masked.

---

## 6. Target Leakage Analysis

- **Overall Leakage Rate:** 91.93% (3168 out of 3446 resumes).
- **Risk Assessment:** High (91.93% of resumes contain explicit category keywords). If trained unmasked, a DistilBERT classifier risks over-relying on superficial header keywords rather than holistic skills, experience, and responsibilities. Recommendation: In Phase 7, implement category phrase masking and compare baseline vs masked model metrics.
- **Top Categories with High Leakage:**
  - **HR:** 100.0% (154 / 154 resumes)
  - **INFORMATION-TECHNOLOGY:** 96.7% (116 / 120 resumes)
  - **BUSINESS-DEVELOPMENT:** 98.3% (118 / 120 resumes)
  - **ADVOCATE:** 81.4% (96 / 118 resumes)
  - **CHEF:** 92.4% (109 / 118 resumes)
  - **FINANCE:** 100.0% (118 / 118 resumes)
  - **ENGINEERING:** 100.0% (118 / 118 resumes)
  - **ACCOUNTANT:** 100.0% (118 / 118 resumes)

---

## 7. Class Distribution & Balanced Class Weights

- **Number of Classes:** 48
- **Normalized Shannon Entropy:** 0.9581 (1.0 = perfectly uniform)
- **Imbalance Ratio (Max/Min):** 7.7 : 1

| Category | Dataset Origin | Count | Percentage | Balanced Weight ($W_c$) |
| :--- | :--- | :--- | :--- | :--- |
| HR | Combined | 154 | 4.47% | 0.4662 |
| INFORMATION-TECHNOLOGY | Combined | 120 | 3.48% | 0.5983 |
| BUSINESS-DEVELOPMENT | Combined | 120 | 3.48% | 0.5983 |
| ADVOCATE | Combined | 118 | 3.42% | 0.6084 |
| CHEF | Combined | 118 | 3.42% | 0.6084 |
| FINANCE | Combined | 118 | 3.42% | 0.6084 |
| ENGINEERING | Combined | 118 | 3.42% | 0.6084 |
| ACCOUNTANT | Combined | 118 | 3.42% | 0.6084 |
| FITNESS | Combined | 117 | 3.4% | 0.6136 |
| AVIATION | Combined | 117 | 3.4% | 0.6136 |
| SALES | Combined | 116 | 3.37% | 0.6189 |
| HEALTHCARE | Combined | 115 | 3.34% | 0.6243 |
| CONSULTANT | Combined | 115 | 3.34% | 0.6243 |
| BANKING | Combined | 115 | 3.34% | 0.6243 |
| CONSTRUCTION | Combined | 112 | 3.25% | 0.641 |
| PUBLIC-RELATIONS | Combined | 111 | 3.22% | 0.6468 |
| DESIGNER | Combined | 107 | 3.11% | 0.671 |
| ARTS | Combined | 103 | 2.99% | 0.697 |
| TEACHER | Combined | 102 | 2.96% | 0.7038 |
| APPAREL | Combined | 97 | 2.81% | 0.7401 |
| DIGITAL-MEDIA | Combined | 96 | 2.79% | 0.7478 |
| Java Developer | Combined | 84 | 2.44% | 0.8547 |
| Testing | Combined | 70 | 2.03% | 1.0256 |
| AGRICULTURE | Combined | 63 | 1.83% | 1.1396 |
| DevOps Engineer | Combined | 55 | 1.6% | 1.3053 |
| Python Developer | Combined | 48 | 1.39% | 1.4957 |
| Web Designing | Combined | 45 | 1.31% | 1.5954 |
| Hadoop | Combined | 42 | 1.22% | 1.7093 |
| Data Science | Combined | 40 | 1.16% | 1.7948 |
| Mechanical Engineer | Combined | 40 | 1.16% | 1.7948 |
| Sales | Combined | 40 | 1.16% | 1.7948 |
| Operations Manager | Combined | 40 | 1.16% | 1.7948 |
| ETL Developer | Combined | 40 | 1.16% | 1.7948 |
| Blockchain | Combined | 40 | 1.16% | 1.7948 |
| AUTOMOBILE | Combined | 36 | 1.04% | 1.9942 |
| Arts | Combined | 36 | 1.04% | 1.9942 |
| Database | Combined | 33 | 0.96% | 2.1755 |
| Health and fitness | Combined | 30 | 0.87% | 2.3931 |
| Electrical Engineering | Combined | 30 | 0.87% | 2.3931 |
| PMO | Combined | 30 | 0.87% | 2.3931 |
| Business Analyst | Combined | 28 | 0.81% | 2.564 |
| DotNet Developer | Combined | 28 | 0.81% | 2.564 |
| Automation Testing | Combined | 26 | 0.75% | 2.7612 |
| Network Security Engineer | Combined | 25 | 0.73% | 2.8717 |
| Civil Engineer | Combined | 24 | 0.7% | 2.9913 |
| SAP Developer | Combined | 24 | 0.7% | 2.9913 |
| BPO | Combined | 22 | 0.64% | 3.2633 |
| Advocate | Combined | 20 | 0.58% | 3.5896 |

---

## 8. Provenance, Licensing & Ethical Assessment

- **Primary Dataset (`opensporks/resumes`):** 2,484 resumes categorized into 24 broad industry categories (e.g. INFORMATION-TECHNOLOGY, HR, FINANCE, ADVOCATE).
  - **Declared License:** CC0: Public Domain (on Hugging Face repository)
  - **Legal Reality:** Scraped from LiveCareer public user resumes. LiveCareer terms prohibit automated scraping. Contains creative text of real job applicants.
- **Supplementary Dataset (`UpdatedResumeDataSet`):** 962 records covering 25 IT/engineering job roles with high intra-dataset duplication (166 unique texts).
  - **Declared License:** CC0: Public Domain (on Kaggle)
  - **Legal Reality:** Scraped from Indian job portals and candidate profiles. Resumes repeated multiple times. Cannot be claimed as commercially cleared.
- **Ethical Guidelines for CareerAI:**
  1. Datasets must be used strictly for non-commercial educational and research prototyping.
  2. Do not redistribute unmasked resumes or host candidate profiles publicly.
  3. In production, models must be fine-tuned on legally licensed or synthetic benchmark datasets.

---

## 9. Next Steps (Pending User Approval)

1. Confirm training strategy: Train on `opensporks` (broad industry classification, 24 classes) vs. Gaurav Dutta (tech-specific roles, 25 classes) vs. Combined hierarchy.
2. Approve Group-Stratified splitting using `cluster_id` (e.g. 70% Train, 15% Validation, 15% Test).
3. Decide on Target Leakage masking (train with masked role headers vs verbatim text).
4. Proceed to Phase 7: DistilBERT Model Architecture & Training Setup.
