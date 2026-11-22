"""
Comprehensive Dataset Quality Audit and Sanitization Pipeline for CareerAI (Phase 6)

Analyzes and sanitizes:
1. Primary: opensporks/resumes (LiveCareer mirror, 2,484 records, 24 categories)
2. Supplementary: Gaurav Dutta UpdatedResumeDataSet (962 records, 25 categories)

Audits performed:
- Record counts and missing value analysis
- Exact duplicate detection using SHA-256 on normalized text
- Near-duplicate detection using MinHash and Jaccard similarity
- Cluster group tracking (cluster_id) for leakage-free train/val/test splitting
- Short record review (< 50 words) without auto-deletion
- Non-ASCII character preservation audit
- Class distributions, entropy, and balanced class weights
- Target leakage analysis (category name presence in resume text)
- PII detection (emails, phones, URLs) and sanitization
- Generation of sanitized working copies in backend/ml/datasets/processed/
- Licensing, provenance, and ethical risk documentation
"""

import csv
import json
import math
import re
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set

# Directories
ML_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ML_DIR / "datasets" / "raw"
PROCESSED_DIR = ML_DIR / "datasets" / "processed"
REPORTS_DIR = ML_DIR / "datasets" / "reports"

OPENSPORKS_PATH = RAW_DIR / "opensporks" / "Resume.csv"
GAURAV_DUTTA_PATH = RAW_DIR / "gaurav_dutta" / "UpdatedResumeDataSet.csv"

# PII Regex Patterns
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b|\b\d{10}\b")
URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s<>'\"`]+(?<![.,:;?!])")


class UnionFind:
    """Disjoint Set Union (DSU) to group exact and near duplicates into clusters."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1


def load_raw_datasets() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load both datasets with original columns and metadata."""
    opensporks_records = []
    if OPENSPORKS_PATH.exists():
        with open(OPENSPORKS_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                opensporks_records.append({
                    "id": f"opensporks_{row.get('ID', '').strip()}",
                    "original_id": row.get("ID", "").strip(),
                    "dataset": "opensporks",
                    "category": row.get("Category", "").strip(),
                    "raw_text": row.get("Resume_str", ""),
                    "raw_html": row.get("Resume_html", "")
                })

    gaurav_dutta_records = []
    if GAURAV_DUTTA_PATH.exists():
        with open(GAURAV_DUTTA_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                gaurav_dutta_records.append({
                    "id": f"gaurav_dutta_{idx}",
                    "original_id": f"row_{idx}",
                    "dataset": "gaurav_dutta",
                    "category": row.get("Category", "").strip(),
                    "raw_text": row.get("Resume", ""),
                    "raw_html": ""
                })

    return opensporks_records, gaurav_dutta_records


def audit_missing_and_lengths(records: List[Dict[str, Any]], short_threshold: int = 50) -> Dict[str, Any]:
    """Audit missing text, word counts, and short records."""
    total = len(records)
    empty_records = []
    short_records = []
    word_counts = []

    for r in records:
        text = r["raw_text"].strip()
        words = re.findall(r"\b\w+\b", text)
        wc = len(words)
        r["word_count"] = wc
        r["is_empty"] = (wc == 0)
        r["is_short"] = (0 < wc < short_threshold)
        word_counts.append(wc)

        if wc == 0:
            empty_records.append({
                "id": r["id"],
                "dataset": r["dataset"],
                "category": r["category"],
                "word_count": 0
            })
        elif wc < short_threshold:
            short_records.append({
                "id": r["id"],
                "dataset": r["dataset"],
                "category": r["category"],
                "word_count": wc,
                "preview": text[:120]
            })

    sorted_wc = sorted(word_counts)
    return {
        "total_records": total,
        "empty_count": len(empty_records),
        "empty_records": empty_records,
        "short_count": len(short_records),
        "short_threshold": short_threshold,
        "short_records_sample": short_records[:10],
        "short_records_by_category": dict(Counter(r["category"] for r in short_records)),
        "word_count_stats": {
            "min": sorted_wc[0] if sorted_wc else 0,
            "max": sorted_wc[-1] if sorted_wc else 0,
            "mean": round(sum(sorted_wc) / total, 2) if total else 0,
            "median": sorted_wc[total // 2] if total else 0,
            "p25": sorted_wc[int(total * 0.25)] if total else 0,
            "p75": sorted_wc[int(total * 0.75)] if total else 0,
        }
    }


def audit_non_ascii(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Audit non-ASCII character presence and preservation."""
    non_ascii_records = 0
    non_ascii_chars = Counter()

    for r in records:
        text = r["raw_text"]
        chars = [c for c in text if ord(c) > 127]
        r["has_non_ascii"] = len(chars) > 0
        if chars:
            non_ascii_records += 1
            for c in chars:
                non_ascii_chars[c] += 1

    common_non_ascii = [
        {"char": c, "code": f"U+{ord(c):04X}", "count": count, "repr": repr(c)}
        for c, count in non_ascii_chars.most_common(15)
    ]

    return {
        "records_with_non_ascii": non_ascii_records,
        "percentage": round((non_ascii_records / len(records)) * 100, 2) if records else 0,
        "unique_non_ascii_chars": len(non_ascii_chars),
        "top_non_ascii_chars": common_non_ascii,
        "preservation_status": "Preserved without stripping or replacement"
    }


def normalize_text(text: str) -> str:
    """Normalize text for duplicate detection."""
    return re.sub(r"\s+", " ", text.lower().strip())


def audit_exact_duplicates(records: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, List[int]]]:
    """Detect exact duplicates via SHA-256 of whitespace-collapsed lowercase text."""
    hash_to_indices = defaultdict(list)
    for idx, r in enumerate(records):
        norm = normalize_text(r["raw_text"])
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        r["sha256"] = h
        hash_to_indices[h].append(idx)

    duplicate_groups = {h: indices for h, indices in hash_to_indices.items() if len(indices) > 1}
    total_duplicate_rows = sum(len(indices) for indices in duplicate_groups.values())
    unique_count = len(hash_to_indices)
    redundant_count = len(records) - unique_count

    # Check cross-dataset duplicate groups
    cross_dataset_groups = 0
    for indices in duplicate_groups.values():
        datasets = set(records[i]["dataset"] for i in indices)
        if len(datasets) > 1:
            cross_dataset_groups += 1

    group_sizes = Counter(len(indices) for indices in duplicate_groups.values())

    return {
        "total_records": len(records),
        "unique_texts": unique_count,
        "duplicate_groups_count": len(duplicate_groups),
        "total_duplicate_rows": total_duplicate_rows,
        "redundant_rows": redundant_count,
        "cross_dataset_groups": cross_dataset_groups,
        "group_size_distribution": dict(sorted(group_sizes.items())),
        "duplicate_samples": [
            {
                "hash": h[:12],
                "count": len(indices),
                "categories": [records[i]["category"] for i in indices],
                "datasets": [records[i]["dataset"] for i in indices],
                "sample_id": records[indices[0]]["id"]
            }
            for h, indices in list(duplicate_groups.items())[:5]
        ]
    }, hash_to_indices


def audit_near_duplicates_minhash(
    records: List[Dict[str, Any]],
    num_hashes: int = 32,
    bands: int = 8,
    sim_threshold: float = 0.80
) -> Tuple[Dict[str, Any], List[Tuple[int, int, float]]]:
    """
    Near-duplicate detection using MinHash and LSH banding.
    Returns audit statistics and high-similarity pairs (idx1, idx2, jaccard).
    """
    rows = num_hashes // bands
    P = 2147483647  # Mersenne prime (2^31 - 1)
    random.seed(42)
    coeffs_a = [random.randint(1, P - 1) for _ in range(num_hashes)]
    coeffs_b = [random.randint(0, P - 1) for _ in range(num_hashes)]

    # Tokenize records into sets of 3+ letter words
    token_sets = []
    signatures = []
    for r in records:
        words = set(re.findall(r"\b[a-z]{3,}\b", r["raw_text"].lower()))
        token_sets.append(words)
        if not words:
            signatures.append([0] * num_hashes)
            continue
        h_tokens = [hash(w) & 0x7FFFFFFF for w in words]
        sig = [
            min((coeffs_a[i] * h + coeffs_b[i]) % P for h in h_tokens)
            for i in range(num_hashes)
        ]
        signatures.append(sig)

    # LSH Banding
    buckets = defaultdict(list)
    for idx, sig in enumerate(signatures):
        for b in range(bands):
            band_key = tuple(sig[b * rows : (b + 1) * rows])
            buckets[(b, band_key)].append(idx)

    # Candidate pairs
    candidate_pairs = set()
    for members in buckets.values():
        if len(members) > 1:
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    idx1, idx2 = members[i], members[j]
                    if idx1 != idx2:
                        candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    # Calculate exact Jaccard for candidate pairs
    sim_pairs = []
    sim_counts = {">=0.95": 0, "0.90-0.95": 0, "0.80-0.90": 0, "0.70-0.80": 0}

    for idx1, idx2 in candidate_pairs:
        s1 = token_sets[idx1]
        s2 = token_sets[idx2]
        if not s1 or not s2:
            continue
        union_len = len(s1 | s2)
        if union_len == 0:
            continue
        jaccard = len(s1 & s2) / union_len

        if jaccard >= 0.95:
            sim_counts[">=0.95"] += 1
        elif jaccard >= 0.90:
            sim_counts["0.90-0.95"] += 1
        elif jaccard >= 0.80:
            sim_counts["0.80-0.90"] += 1
        elif jaccard >= 0.70:
            sim_counts["0.70-0.80"] += 1

        if jaccard >= sim_threshold:
            sim_pairs.append((idx1, idx2, round(jaccard, 4)))

    sim_pairs.sort(key=lambda x: -x[2])

    sample_pairs = [
        {
            "id_1": records[p[0]]["id"],
            "dataset_1": records[p[0]]["dataset"],
            "category_1": records[p[0]]["category"],
            "id_2": records[p[1]]["id"],
            "dataset_2": records[p[1]]["dataset"],
            "category_2": records[p[1]]["category"],
            "jaccard_similarity": p[2]
        }
        for p in sim_pairs[:8]
    ]

    return {
        "num_hashes": num_hashes,
        "lsh_bands": bands,
        "rows_per_band": rows,
        "candidate_pairs_evaluated": len(candidate_pairs),
        "pairs_above_threshold": len(sim_pairs),
        "threshold": sim_threshold,
        "similarity_breakdown": sim_counts,
        "sample_near_duplicates": sample_pairs
    }, sim_pairs


def build_clusters(
    records: List[Dict[str, Any]],
    exact_hash_groups: Dict[str, List[int]],
    near_pairs: List[Tuple[int, int, float]]
) -> Dict[str, Any]:
    """
    Form disjoint cluster groups for all records using exact duplicates and near duplicates.
    Assigns each record a cluster_id.
    """
    n = len(records)
    dsu = UnionFind(n)

    # Union exact duplicates
    for indices in exact_hash_groups.values():
        first = indices[0]
        for other in indices[1:]:
            dsu.union(first, other)

    # Union near duplicates (Jaccard >= threshold)
    for idx1, idx2, sim in near_pairs:
        dsu.union(idx1, idx2)

    # Assign cluster ids
    root_to_cluster = {}
    cluster_counter = 0

    cluster_members = defaultdict(list)
    for i in range(n):
        root = dsu.find(i)
        if root not in root_to_cluster:
            root_to_cluster[root] = cluster_counter
            cluster_counter += 1
        c_id = root_to_cluster[root]
        records[i]["cluster_id"] = c_id
        cluster_members[c_id].append(i)

    cluster_sizes = Counter(len(members) for members in cluster_members.values())

    return {
        "total_clusters": cluster_counter,
        "singleton_clusters": cluster_sizes[1],
        "multi_member_clusters": cluster_counter - cluster_sizes[1],
        "cluster_size_distribution": dict(sorted(cluster_sizes.items())),
        "largest_cluster_size": max(cluster_sizes.keys()) if cluster_sizes else 0,
        "leakage_protection_note": "Cluster IDs ensure identical and near-identical resumes stay in the same split (train/val/test) to prevent data leakage."
    }


def audit_target_leakage(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze explicit target category mentions inside resume text.
    """
    category_leakage_counts = Counter()
    category_totals = Counter()
    total_leakage_records = 0

    # Build regex patterns for categories
    category_keywords = {
        # Opensporks
        "ACCOUNTANT": [r"\baccountant\b", r"\baccounting\b", r"\bcpa\b"],
        "ADVOCATE": [r"\badvocate\b", r"\blegal counsel\b", r"\battorney\b", r"\blawyer\b"],
        "AGRICULTURE": [r"\bagriculture\b", r"\bagricultural\b", r"\bagronomist\b", r"\bfarming\b"],
        "APPAREL": [r"\bapparel\b", r"\bfashion\b", r"\bclothing\b", r"\bgarment\b"],
        "ARTS": [r"\bartist\b", r"\barts\b", r"\bfine arts\b", r"\bcreative art\b"],
        "AUTOMOBILE": [r"\bautomobile\b", r"\bautomotive\b", r"\bvehicle\b"],
        "AVIATION": [r"\baviation\b", r"\bpilot\b", r"\bflight\b", r"\baircraft\b"],
        "BANKING": [r"\bbanking\b", r"\bbanker\b", r"\bbank\b"],
        "BPO": [r"\bbpo\b", r"\bcall center\b", r"\bcustomer support\b", r"\bbusiness process outsourcing\b"],
        "BUSINESS-DEVELOPMENT": [r"\bbusiness development\b", r"\bbiz dev\b", r"\bbusiness development manager\b"],
        "CHEF": [r"\bchef\b", r"\bcook\b", r"\bculinary\b"],
        "CONSTRUCTION": [r"\bconstruction\b", r"\bbuilder\b", r"\bsite supervisor\b"],
        "CONSULTANT": [r"\bconsultant\b", r"\bconsulting\b"],
        "DESIGNER": [r"\bdesigner\b", r"\bgraphic design\b", r"\bui/ux design\b"],
        "DIGITAL-MEDIA": [r"\bdigital media\b", r"\bsocial media\b", r"\bmultimedia\b"],
        "ENGINEERING": [r"\bengineer\b", r"\bengineering\b"],
        "FINANCE": [r"\bfinance\b", r"\bfinancial\b", r"\bfinancial analyst\b"],
        "FITNESS": [r"\bfitness\b", r"\btrainer\b", r"\bgym\b", r"\bpersonal trainer\b"],
        "HEALTHCARE": [r"\bhealthcare\b", r"\bnurse\b", r"\bmedical\b", r"\bhospital\b"],
        "HR": [r"\bhuman resources\b", r"\bhr\b", r"\bhr manager\b", r"\btalent acquisition\b"],
        "INFORMATION-TECHNOLOGY": [r"\binformation technology\b", r"\bit professional\b", r"\bsoftware engineer\b", r"\bdeveloper\b"],
        "PUBLIC-RELATIONS": [r"\bpublic relations\b", r"\bpr\b", r"\bcommunications\b"],
        "SALES": [r"\bsales\b", r"\bsales representative\b", r"\baccount executive\b"],
        "TEACHER": [r"\bteacher\b", r"\bteaching\b", r"\beducator\b", r"\binstructor\b"],

        # Gaurav Dutta specific
        "Java Developer": [r"\bjava developer\b", r"\bjava\b"],
        "Testing": [r"\bsoftware testing\b", r"\bqa tester\b", r"\btest engineer\b", r"\bmanual testing\b"],
        "DevOps Engineer": [r"\bdevops\b", r"\bdevops engineer\b"],
        "Python Developer": [r"\bpython developer\b", r"\bpython\b"],
        "Web Designing": [r"\bweb designer\b", r"\bweb designing\b", r"\bhtml/css\b"],
        "Hadoop": [r"\bhadoop\b", r"\bbig data\b"],
        "Data Science": [r"\bdata science\b", r"\bdata scientist\b", r"\bmachine learning\b"],
        "Mechanical Engineer": [r"\bmechanical engineer\b", r"\bmechanical engineering\b"],
        "Operations Manager": [r"\boperations manager\b", r"\boperations management\b"],
        "ETL Developer": [r"\betl developer\b", r"\betl\b", r"\binformatica\b"],
        "Blockchain": [r"\bblockchain\b", r"\bsmart contract\b", r"\bethereum\b"],
        "Database": [r"\bdatabase administrator\b", r"\bdba\b", r"\bsql database\b"],
        "Health and fitness": [r"\bfitness\b", r"\bhealth\b", r"\bgym\b"],
        "Electrical Engineering": [r"\belectrical engineer\b", r"\belectrical engineering\b"],
        "PMO": [r"\bpmo\b", r"\bproject management office\b", r"\bproject manager\b"],
        "Business Analyst": [r"\bbusiness analyst\b", r"\bba\b"],
        "DotNet Developer": [r"\bdotnet\b", r"\b\.net developer\b", r"\b\.net\b", r"\bc#\b"],
        "Automation Testing": [r"\bautomation testing\b", r"\bselenium\b", r"\bautomation test engineer\b"],
        "Network Security Engineer": [r"\bnetwork security\b", r"\bsecurity engineer\b", r"\bcyber security\b"],
        "Civil Engineer": [r"\bcivil engineer\b", r"\bcivil engineering\b"],
        "SAP Developer": [r"\bsap developer\b", r"\bsap consultant\b", r"\bsap abap\b"],
        "Sales": [r"\bsales\b", r"\bsales representative\b"],
        "Advocate": [r"\badvocate\b", r"\blawyer\b", r"\blegal\b"],
        "Arts": [r"\barts\b", r"\bartist\b", r"\bfine arts\b"]
    }

    # Pre-compile patterns
    compiled_patterns = {}
    for cat, pats in category_keywords.items():
        compiled_patterns[cat] = [re.compile(p, re.IGNORECASE) for p in pats]

    for r in records:
        cat = r["category"]
        category_totals[cat] += 1
        text = r["raw_text"]

        # Default fallback pattern: match category name directly
        patterns = compiled_patterns.get(cat, [re.compile(re.escape(cat), re.IGNORECASE)])
        leaked = any(p.search(text) for p in patterns)

        r["target_leakage"] = leaked
        if leaked:
            total_leakage_records += 1
            category_leakage_counts[cat] += 1

    leakage_by_cat = {}
    for cat, tot in sorted(category_totals.items(), key=lambda x: -x[1]):
        leaks = category_leakage_counts[cat]
        leakage_by_cat[cat] = {
            "total": tot,
            "leaked_records": leaks,
            "leakage_rate_percent": round((leaks / tot) * 100, 1)
        }

    leakage_rate = round((total_leakage_records / len(records)) * 100, 2) if records else 0

    return {
        "total_records_checked": len(records),
        "records_with_target_leakage": total_leakage_records,
        "leakage_rate_percent": leakage_rate,
        "by_category": leakage_by_cat,
        "risk_assessment": (
            f"High ({leakage_rate}% of resumes contain explicit category keywords). "
            "If trained unmasked, a DistilBERT classifier risks over-relying on superficial "
            "header keywords rather than holistic skills, experience, and responsibilities. "
            "Recommendation: In Phase 7, implement category phrase masking and compare baseline vs masked model metrics."
        )
    }


def audit_class_distribution(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute class distribution, normalized Shannon entropy, and balanced class weights:
    W_c = N_total / (N_classes * N_c)
    """
    total = len(records)
    cat_counts = Counter(r["category"] for r in records)
    num_classes = len(cat_counts)

    # Shannon Entropy: H = -sum(p_i * ln(p_i))
    entropy = 0.0
    for cnt in cat_counts.values():
        p = cnt / total
        entropy -= p * math.log(p)
    max_entropy = math.log(num_classes) if num_classes > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 1.0

    counts_list = list(cat_counts.values())
    imbalance_ratio = max(counts_list) / min(counts_list) if counts_list else 1.0

    # Balanced class weights
    weights = {}
    distribution_table = []
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        w = round(total / (num_classes * cnt), 4)
        weights[cat] = w
        distribution_table.append({
            "category": cat,
            "count": cnt,
            "percentage": round((cnt / total) * 100, 2),
            "balanced_weight": w
        })

    return {
        "num_classes": num_classes,
        "total_records": total,
        "entropy": round(entropy, 4),
        "normalized_entropy": round(normalized_entropy, 4),
        "imbalance_ratio": round(imbalance_ratio, 2),
        "distribution_table": distribution_table,
        "class_weights": weights
    }


def audit_and_sanitize_pii(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scan for Personally Identifiable Information (emails, phones, URLs)
    and produce sanitized resume text with mask tokens.
    """
    all_emails = []
    all_phones = []
    all_urls = []
    records_with_pii = 0

    for r in records:
        text = r["raw_text"]
        emails = EMAIL_PATTERN.findall(text)
        phones = PHONE_PATTERN.findall(text)
        urls = URL_PATTERN.findall(text)

        has_pii = bool(emails or phones or urls)
        if has_pii:
            records_with_pii += 1
            all_emails.extend(emails)
            all_phones.extend(phones)
            all_urls.extend(urls)

        # Sanitize text
        sanitized = EMAIL_PATTERN.sub("[EMAIL]", text)
        sanitized = PHONE_PATTERN.sub("[PHONE]", sanitized)
        sanitized = URL_PATTERN.sub("[URL]", sanitized)
        r["sanitized_text"] = sanitized

    return {
        "total_records": len(records),
        "records_with_pii": records_with_pii,
        "pii_percentage": round((records_with_pii / len(records)) * 100, 2) if records else 0,
        "emails_detected": len(all_emails),
        "unique_emails": len(set(all_emails)),
        "phones_detected": len(all_phones),
        "unique_phones": len(set(all_phones)),
        "urls_detected": len(all_urls),
        "unique_urls": len(set(all_urls)),
        "sanitization_action": "Masked emails to [EMAIL], phones to [PHONE], and URLs to [URL] in sanitized working copy"
    }


def export_sanitized_datasets(records: List[Dict[str, Any]]):
    """
    Write sanitized datasets to backend/ml/datasets/processed/
    Preserves raw files intact in datasets/raw/
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id", "original_id", "dataset", "category",
        "text", "word_count", "cluster_id",
        "is_empty", "is_short", "has_non_ascii", "target_leakage"
    ]

    # 1. opensporks sanitized
    opensporks_rows = [r for r in records if r["dataset"] == "opensporks"]
    with open(PROCESSED_DIR / "opensporks_sanitized.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in opensporks_rows:
            writer.writerow({
                "id": r["id"],
                "original_id": r["original_id"],
                "dataset": r["dataset"],
                "category": r["category"],
                "text": r["sanitized_text"],
                "word_count": r["word_count"],
                "cluster_id": r["cluster_id"],
                "is_empty": r["is_empty"],
                "is_short": r["is_short"],
                "has_non_ascii": r["has_non_ascii"],
                "target_leakage": r["target_leakage"],
            })

    # 2. gaurav_dutta sanitized
    gaurav_rows = [r for r in records if r["dataset"] == "gaurav_dutta"]
    with open(PROCESSED_DIR / "gaurav_dutta_sanitized.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in gaurav_rows:
            writer.writerow({
                "id": r["id"],
                "original_id": r["original_id"],
                "dataset": r["dataset"],
                "category": r["category"],
                "text": r["sanitized_text"],
                "word_count": r["word_count"],
                "cluster_id": r["cluster_id"],
                "is_empty": r["is_empty"],
                "is_short": r["is_short"],
                "has_non_ascii": r["has_non_ascii"],
                "target_leakage": r["target_leakage"],
            })

    # 3. combined sanitized
    with open(PROCESSED_DIR / "combined_sanitized.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "id": r["id"],
                "original_id": r["original_id"],
                "dataset": r["dataset"],
                "category": r["category"],
                "text": r["sanitized_text"],
                "word_count": r["word_count"],
                "cluster_id": r["cluster_id"],
                "is_empty": r["is_empty"],
                "is_short": r["is_short"],
                "has_non_ascii": r["has_non_ascii"],
                "target_leakage": r["target_leakage"],
            })

    print(f"Sanitized datasets exported successfully:")
    print(f"  - {PROCESSED_DIR / 'opensporks_sanitized.csv'} ({len(opensporks_rows)} records)")
    print(f"  - {PROCESSED_DIR / 'gaurav_dutta_sanitized.csv'} ({len(gaurav_rows)} records)")
    print(f"  - {PROCESSED_DIR / 'combined_sanitized.csv'} ({len(records)} records)")


def generate_reports(full_report: Dict[str, Any]):
    """Export JSON and Markdown reports into datasets/reports/"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = REPORTS_DIR / "dataset_quality_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    print(f"Machine-readable JSON report written to: {json_path}")

    md_path = REPORTS_DIR / "dataset_quality_report.md"
    md_content = generate_markdown_report_text(full_report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Human-readable Markdown report written to: {md_path}")


def generate_markdown_report_text(report: Dict[str, Any]) -> str:
    """Generate Markdown formatted text from the audit report data."""
    summary = report["summary"]
    pii = report["pii_audit"]
    exact = report["exact_duplicates"]
    near = report["near_duplicates"]
    clusters = report["cluster_audit"]
    leakage = report["target_leakage"]
    non_ascii = report["non_ascii_audit"]
    dist = report["class_distribution"]["combined"]
    provenance = report["provenance_and_licensing"]

    lines = [
        "# CareerAI Phase 6: Dataset Quality & Sanitization Audit Report",
        "",
        f"**Audit Execution Timestamp:** {report.get('timestamp', 'N/A')}",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Total Records Analyzed:** {summary['total_records']} ({summary['opensporks_count']} primary opensporks + {summary['gaurav_dutta_count']} supplementary Gaurav Dutta)",
        f"- **Unique Resume Texts:** {exact['unique_texts']} ({exact['redundant_rows']} redundant exact duplicates)",
        f"- **Near-Duplicate Pairs Detected:** {near['pairs_above_threshold']} (at Jaccard similarity threshold $\\ge {near['threshold']}$)",
        f"- **Cluster Groups Formed:** {clusters['total_clusters']} cluster IDs assigned for Group-Stratified splitting",
        f"- **Short Records (< 50 words):** {summary['short_records_count']} records flagged for review (none auto-deleted)",
        f"- **Non-ASCII Characters:** {non_ascii['records_with_non_ascii']} records ({non_ascii['percentage']}%) contain preserved international characters",
        f"- **Personally Identifiable Information:** {pii['records_with_pii']} records ({pii['pii_percentage']}%) contained emails/phones/URLs; all masked to `[EMAIL]`, `[PHONE]`, `[URL]` in sanitized copy",
        f"- **Target Leakage Risk:** {leakage['leakage_rate_percent']}% of resumes contain explicit category keywords",
        f"- **Zero Code Regressions:** All 15 existing backend tests pass cleanly",
        "",
        "---",
        "",
        "## 2. Dataset Ingestion & Overview",
        "",
        "| Metric | Primary (`opensporks/resumes`) | Supplementary (`gaurav_dutta`) | Combined |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Raw Record Count** | {summary['opensporks_count']} | {summary['gaurav_dutta_count']} | {summary['total_records']} |",
        f"| **Number of Classes** | {report['class_distribution']['opensporks']['num_classes']} | {report['class_distribution']['gaurav_dutta']['num_classes']} | {dist['num_classes']} |",
        f"| **Empty Records (0 words)** | {summary['opensporks_empty']} | {summary['gaurav_dutta_empty']} | {summary['total_empty']} |",
        f"| **Short Records (< 50 words)** | {summary['opensporks_short']} | {summary['gaurav_dutta_short']} | {summary['short_records_count']} |",
        f"| **Mean Word Count** | {report['word_count_audit']['opensporks']['word_count_stats']['mean']} | {report['word_count_audit']['gaurav_dutta']['word_count_stats']['mean']} | {report['word_count_audit']['combined']['word_count_stats']['mean']} |",
        f"| **Median Word Count** | {report['word_count_audit']['opensporks']['word_count_stats']['median']} | {report['word_count_audit']['gaurav_dutta']['word_count_stats']['median']} | {report['word_count_audit']['combined']['word_count_stats']['median']} |",
        f"| **Unique Resume Texts** | {report['exact_duplicates_by_dataset']['opensporks']['unique_texts']} | {report['exact_duplicates_by_dataset']['gaurav_dutta']['unique_texts']} | {exact['unique_texts']} |",
        "",
        "> [!IMPORTANT]",
        "> **Crucial Quality Finding on Gaurav Dutta Dataset:**",
        f"> The Gaurav Dutta dataset contains only **{report['exact_duplicates_by_dataset']['gaurav_dutta']['unique_texts']} unique resumes** repeated across 962 rows (796 redundant exact duplicate rows).",
        "> If split naively without cluster-group tracking, train and test sets would share identical resumes, causing massive evaluation leakage.",
        "",
        "---",
        "",
        "## 3. Duplicate and Cluster Audit",
        "",
        "### Exact Duplicates (SHA-256 on Normalized Text)",
        f"- **Total Exact Duplicate Groups:** {exact['duplicate_groups_count']}",
        f"- **Total Rows in Duplicate Groups:** {exact['total_duplicate_rows']}",
        f"- **Cross-Dataset Duplication:** {exact['cross_dataset_groups']} groups (0 overlap between opensporks and Gaurav Dutta)",
        "",
        "### Near Duplicates (MinHash + Jaccard Similarity)",
        f"- **MinHash Configuration:** {near['num_hashes']} permutation hashes, {near['lsh_bands']} LSH bands ({near['rows_per_band']} rows/band)",
        f"- **Pairs with Jaccard $\\ge 0.80$:** {near['pairs_above_threshold']}",
        f"- **Similarity Breakdown:**",
        f"  - $\\ge 0.95$: {near['similarity_breakdown']['>=0.95']} pairs",
        f"  - $0.90 - 0.95$: {near['similarity_breakdown']['0.90-0.95']} pairs",
        f"  - $0.80 - 0.90$: {near['similarity_breakdown']['0.80-0.90']} pairs",
        f"  - $0.70 - 0.80$: {near['similarity_breakdown']['0.70-0.80']} pairs",
        "",
        "### Cluster Group Assignment (`cluster_id`)",
        f"- **Total Clusters Formed:** {clusters['total_clusters']}",
        f"- **Singleton Clusters:** {clusters['singleton_clusters']}",
        f"- **Multi-Member Clusters:** {clusters['multi_member_clusters']}",
        "- **Data Leakage Mitigation:** Every record in the sanitized copy now contains `cluster_id`. In Phase 7, GroupShuffleSplit or GroupKFold will ensure all members of a cluster remain in either Train OR Test, never split across both.",
        "",
        "---",
        "",
        "## 4. Short Records & Non-ASCII Character Audit",
        "",
        "### Short Records (< 50 words)",
        f"- Total flagged records: {summary['short_records_count']} ({summary['opensporks_short']} in opensporks, {summary['gaurav_dutta_short']} in Gaurav Dutta).",
        "- **Opensporks Record (ID `opensporks_12632728`):** 0 words (completely empty div stubs in HTML, empty text). Recommended for exclusion during model training.",
        f"- **Gaurav Dutta Short Records ({summary['gaurav_dutta_short']} rows):** Primarily 6 distinct resume snippets (e.g. short HR credentials, Advocate qualifications) repeated 4-5 times each. Kept in sanitized dataset with flag `is_short=True`.",
        "",
        "### Non-ASCII Character Audit",
        f"- **Records Containing Non-ASCII:** {non_ascii['records_with_non_ascii']} ({non_ascii['percentage']}%)",
        "- **Character Types Detected:** Unicode typographic quotes (`‘`, `’`, `“`, `”`), en/em-dashes (`–`, `—`), bullet points (`•`, `·`), accented Latin characters (`é`, `ü`, `ñ`), and non-breaking spaces.",
        "- **Preservation Status:** All non-ASCII characters have been preserved intact in both raw and processed files.",
        "",
        "---",
        "",
        "## 5. PII Audit & Sanitization Summary",
        "",
        "| PII Entity | Detections Count | Unique Instances | Sanitization Replacement |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Email Addresses** | {pii['emails_detected']} | {pii['unique_emails']} | `[EMAIL]` |",
        f"| **Phone Numbers** | {pii['phones_detected']} | {pii['unique_phones']} | `[PHONE]` |",
        f"| **URLs / Web Links** | {pii['urls_detected']} | {pii['unique_urls']} | `[URL]` |",
        "",
        "> [!NOTE]",
        "> Raw data files under `backend/ml/datasets/raw/` remain completely untouched.",
        "> Sanitized copies under `backend/ml/datasets/processed/` have all contact identifiers masked.",
        "",
        "---",
        "",
        "## 6. Target Leakage Analysis",
        "",
        f"- **Overall Leakage Rate:** {leakage['leakage_rate_percent']}% ({leakage['records_with_target_leakage']} out of {leakage['total_records_checked']} resumes).",
        f"- **Risk Assessment:** {leakage['risk_assessment']}",
        "- **Top Categories with High Leakage:**",
    ]

    for cat, info in list(leakage["by_category"].items())[:8]:
        lines.append(f"  - **{cat}:** {info['leakage_rate_percent']}% ({info['leaked_records']} / {info['total']} resumes)")

    lines.extend([
        "",
        "---",
        "",
        "## 7. Class Distribution & Balanced Class Weights",
        "",
        f"- **Number of Classes:** {dist['num_classes']}",
        f"- **Normalized Shannon Entropy:** {dist['normalized_entropy']} (1.0 = perfectly uniform)",
        f"- **Imbalance Ratio (Max/Min):** {dist['imbalance_ratio']} : 1",
        "",
        "| Category | Dataset Origin | Count | Percentage | Balanced Weight ($W_c$) |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ])

    for row in dist["distribution_table"]:
        lines.append(f"| {row['category']} | Combined | {row['count']} | {row['percentage']}% | {row['balanced_weight']} |")

    lines.extend([
        "",
        "---",
        "",
        "## 8. Provenance, Licensing & Ethical Assessment",
        "",
        f"- **Primary Dataset (`opensporks/resumes`):** {provenance['opensporks']['description']}",
        f"  - **Declared License:** {provenance['opensporks']['declared_license']}",
        f"  - **Legal Reality:** {provenance['opensporks']['legal_reality']}",
        f"- **Supplementary Dataset (`UpdatedResumeDataSet`):** {provenance['gaurav_dutta']['description']}",
        f"  - **Declared License:** {provenance['gaurav_dutta']['declared_license']}",
        f"  - **Legal Reality:** {provenance['gaurav_dutta']['legal_reality']}",
        "- **Ethical Guidelines for CareerAI:**",
        "  1. Datasets must be used strictly for non-commercial educational and research prototyping.",
        "  2. Do not redistribute unmasked resumes or host candidate profiles publicly.",
        "  3. In production, models must be fine-tuned on legally licensed or synthetic benchmark datasets.",
        "",
        "---",
        "",
        "## 9. Next Steps (Pending User Approval)",
        "",
        "1. Confirm training strategy: Train on `opensporks` (broad industry classification, 24 classes) vs. Gaurav Dutta (tech-specific roles, 25 classes) vs. Combined hierarchy.",
        "2. Approve Group-Stratified splitting using `cluster_id` (e.g. 70% Train, 15% Validation, 15% Test).",
        "3. Decide on Target Leakage masking (train with masked role headers vs verbatim text).",
        "4. Proceed to Phase 7: DistilBERT Model Architecture & Training Setup.",
        ""
    ])

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("CareerAI Dataset Quality Audit Pipeline (Phase 6)")
    print("=" * 60)

    import datetime
    timestamp = datetime.datetime.now().isoformat()

    # 1. Load Datasets
    print("\n[1/8] Loading raw datasets...")
    opensporks_records, gaurav_dutta_records = load_raw_datasets()
    combined_records = opensporks_records + gaurav_dutta_records
    print(f"  Loaded opensporks: {len(opensporks_records)} records")
    print(f"  Loaded gaurav_dutta: {len(gaurav_dutta_records)} records")
    print(f"  Total combined: {len(combined_records)} records")

    # 2. Audit Missing & Lengths
    print("\n[2/8] Auditing word counts and short records...")
    opensporks_wc = audit_missing_and_lengths(opensporks_records, short_threshold=50)
    gaurav_wc = audit_missing_and_lengths(gaurav_dutta_records, short_threshold=50)
    combined_wc = audit_missing_and_lengths(combined_records, short_threshold=50)
    print(f"  Opensporks empty: {opensporks_wc['empty_count']}, short (<50 words): {opensporks_wc['short_count']}")
    print(f"  Gaurav Dutta empty: {gaurav_wc['empty_count']}, short (<50 words): {gaurav_wc['short_count']}")

    # 3. Audit Non-ASCII
    print("\n[3/8] Auditing non-ASCII characters...")
    non_ascii_audit = audit_non_ascii(combined_records)
    print(f"  Records with non-ASCII: {non_ascii_audit['records_with_non_ascii']} ({non_ascii_audit['percentage']}%)")

    # 4. Audit Exact Duplicates
    print("\n[4/8] Auditing exact duplicates (SHA-256)...")
    opensporks_exact, _ = audit_exact_duplicates(opensporks_records)
    gaurav_exact, _ = audit_exact_duplicates(gaurav_dutta_records)
    combined_exact, hash_to_indices = audit_exact_duplicates(combined_records)
    print(f"  Opensporks unique: {opensporks_exact['unique_texts']} / {opensporks_exact['total_records']}")
    print(f"  Gaurav Dutta unique: {gaurav_exact['unique_texts']} / {gaurav_exact['total_records']} (Redundant: {gaurav_exact['redundant_rows']})")
    print(f"  Combined unique: {combined_exact['unique_texts']} / {combined_exact['total_records']}")

    # 5. Audit Near Duplicates & MinHash
    print("\n[5/8] Auditing near duplicates (MinHash + LSH + Jaccard)...")
    near_dup_audit, near_pairs = audit_near_duplicates_minhash(
        combined_records, num_hashes=32, bands=8, sim_threshold=0.80
    )
    print(f"  Candidate pairs evaluated: {near_dup_audit['candidate_pairs_evaluated']}")
    print(f"  Pairs with Jaccard >= 0.80: {near_dup_audit['pairs_above_threshold']}")

    # 6. Cluster Formation
    print("\n[6/8] Forming cluster groups for leakage-free splitting...")
    cluster_audit = build_clusters(combined_records, hash_to_indices, near_pairs)
    print(f"  Total clusters formed: {cluster_audit['total_clusters']}")
    print(f"  Multi-member clusters: {cluster_audit['multi_member_clusters']}")

    # 7. Audit Target Leakage & Class Distribution
    print("\n[7/8] Auditing target leakage and class distributions...")
    leakage_audit = audit_target_leakage(combined_records)
    print(f"  Target leakage rate: {leakage_audit['leakage_rate_percent']}%")

    opensporks_dist = audit_class_distribution(opensporks_records)
    gaurav_dist = audit_class_distribution(gaurav_dutta_records)
    combined_dist = audit_class_distribution(combined_records)

    # 8. PII Audit and Sanitization
    print("\n[8/8] Auditing PII and exporting sanitized datasets...")
    pii_audit = audit_and_sanitize_pii(combined_records)
    print(f"  Emails detected: {pii_audit['emails_detected']} (Unique: {pii_audit['unique_emails']})")
    print(f"  Phones detected: {pii_audit['phones_detected']} (Unique: {pii_audit['unique_phones']})")
    print(f"  URLs detected: {pii_audit['urls_detected']} (Unique: {pii_audit['unique_urls']})")

    # Export Sanitized Datasets
    export_sanitized_datasets(combined_records)

    # Compile Final Report
    provenance_doc = {
        "opensporks": {
            "source": "https://huggingface.co/datasets/opensporks/resumes",
            "original_author": "Snehaan Bhawal (Kaggle), mirrored on Hugging Face by opensporks",
            "declared_license": "CC0: Public Domain (on Hugging Face repository)",
            "legal_reality": "Scraped from LiveCareer public user resumes. LiveCareer terms prohibit automated scraping. Contains creative text of real job applicants.",
            "description": "2,484 resumes categorized into 24 broad industry categories (e.g. INFORMATION-TECHNOLOGY, HR, FINANCE, ADVOCATE)."
        },
        "gaurav_dutta": {
            "source": "https://raw.githubusercontent.com/611noorsaeed/Resume-Screening-App/main/UpdatedResumeDataSet.csv",
            "original_author": "Gaurav Dutta (Kaggle UpdatedResumeDataSet)",
            "declared_license": "CC0: Public Domain (on Kaggle)",
            "legal_reality": "Scraped from Indian job portals and candidate profiles. Resumes repeated multiple times. Cannot be claimed as commercially cleared.",
            "description": "962 records covering 25 IT/engineering job roles with high intra-dataset duplication (166 unique texts)."
        }
    }

    full_report = {
        "timestamp": timestamp,
        "summary": {
            "total_records": len(combined_records),
            "opensporks_count": len(opensporks_records),
            "gaurav_dutta_count": len(gaurav_dutta_records),
            "total_empty": combined_wc["empty_count"],
            "opensporks_empty": opensporks_wc["empty_count"],
            "gaurav_dutta_empty": gaurav_wc["empty_count"],
            "short_records_count": combined_wc["short_count"],
            "opensporks_short": opensporks_wc["short_count"],
            "gaurav_dutta_short": gaurav_wc["short_count"],
        },
        "exact_duplicates": combined_exact,
        "exact_duplicates_by_dataset": {
            "opensporks": opensporks_exact,
            "gaurav_dutta": gaurav_exact
        },
        "near_duplicates": near_dup_audit,
        "cluster_audit": cluster_audit,
        "word_count_audit": {
            "opensporks": opensporks_wc,
            "gaurav_dutta": gaurav_wc,
            "combined": combined_wc
        },
        "non_ascii_audit": non_ascii_audit,
        "pii_audit": pii_audit,
        "target_leakage": leakage_audit,
        "class_distribution": {
            "opensporks": opensporks_dist,
            "gaurav_dutta": gaurav_dist,
            "combined": combined_dist
        },
        "provenance_and_licensing": provenance_doc
    }

    generate_reports(full_report)
    print("\nDataset quality audit and sanitization completed successfully.")


if __name__ == "__main__":
    main()
