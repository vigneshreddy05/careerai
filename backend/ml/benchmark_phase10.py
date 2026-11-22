"""
Phase 10 Real Matching & Performance Measurement Script.
Measures:
1. Exact model size on disk
2. Process RAM before and after loading both DistilBERT & all-MiniLM-L6-v2
3. Real resume-to-job matching test execution
4. Exact CPU inference latency
"""

import os
import sys
import time
import psutil
from pathlib import Path

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, str(Path(".").resolve()))

# Measure disk sizes
minilm_dir = Path("backend/ml/saved_models/all-MiniLM-L6-v2")
distilbert_dir = Path("backend/ml/saved_models/distilbert_job_classifier")

minilm_disk_bytes = sum(f.stat().st_size for f in minilm_dir.iterdir() if f.is_file())
distilbert_disk_bytes = sum(f.stat().st_size for f in distilbert_dir.iterdir() if f.is_file())

proc = psutil.Process()
ram_init = proc.memory_info().rss

# Import services
from backend.app.services.job_prediction_service import get_prediction_service
from backend.app.services.semantic_matching_service import get_semantic_matching_service

# Load DistilBERT
t0 = time.time()
ps = get_prediction_service()
ps.load_model()
t_distilbert_load = time.time() - t0
ram_after_distilbert = proc.memory_info().rss

# Load all-MiniLM-L6-v2
t0 = time.time()
ms = get_semantic_matching_service()
ms.load_model()
t_minilm_load = time.time() - t0
ram_after_minilm = proc.memory_info().rss

# Real realistic resume
REAL_RESUME = (
    "Jane Doe - Senior Full Stack Software Engineer\n"
    "Email: jane.doe@example.com | Phone: 555-0199\n\n"
    "SUMMARY:\n"
    "Experienced software engineer with 6+ years of building production web applications, "
    "microservices architectures, and distributed backend systems. Proficient in Python, "
    "FastAPI, Django, React, TypeScript, PostgreSQL, Redis, and Amazon Web Services (AWS).\n\n"
    "EXPERIENCE:\n"
    "Lead Backend Engineer at CloudTech (2021 - Present)\n"
    "- Architected high-throughput REST APIs using FastAPI and Python handling 50M requests/day.\n"
    "- Managed PostgreSQL database sharding and Redis caching layers to optimize query latency by 45%.\n"
    "- Automated CI/CD deployment pipelines using GitHub Actions, Docker, and AWS ECS.\n\n"
    "Software Engineer at DataStack (2018 - 2021)\n"
    "- Developed customer-facing dashboards with React, TypeScript, and Tailwind CSS.\n"
    "- Built automated testing suites with PyTest achieving 92% code coverage.\n\n"
    "EDUCATION:\n"
    "Bachelor of Science in Computer Science, State University, 2018\n"
)

# Real realistic job description
REAL_JOB_DESCRIPTION = (
    "Senior Cloud Backend Engineer\n"
    "Role Overview:\n"
    "We are seeking an experienced Backend Engineer to scale our cloud infrastructure. "
    "You will design robust microservices, improve API latency, and maintain our database pipelines.\n\n"
    "Key Requirements:\n"
    "- 5+ years of software development experience with Python or Go.\n"
    "- In-depth experience with FastAPI, Django, or Flask.\n"
    "- Production experience with PostgreSQL, Redis, and Docker.\n"
    "- Hands-on proficiency with AWS cloud infrastructure (ECS, S3, RDS) and Kubernetes.\n"
    "- Familiarity with Terraform or CI/CD pipelines.\n\n"
    "Nice-to-Have:\n"
    "- Experience with React or frontend dashboards.\n"
    "- Knowledge of Kafka or message broker architectures.\n"
)

# Run DistilBERT Prediction
t0 = time.time()
pred_result = ps.predict(REAL_RESUME)
latency_distilbert = (time.time() - t0) * 1000

# Run Sentence-BERT Matching
t0 = time.time()
match_result = ms.match(REAL_RESUME, REAL_JOB_DESCRIPTION, job_title="Senior Cloud Backend Engineer")
latency_matching = (time.time() - t0) * 1000

print("=" * 60)
print("PHASE 10 REAL MATCHING & PERFORMANCE REPORT")
print("=" * 60)
print(f"all-MiniLM-L6-v2 Disk Size: {minilm_disk_bytes / (1024*1024):.2f} MB")
print(f"DistilBERT Disk Size:       {distilbert_disk_bytes / (1024*1024):.2f} MB")
print("-" * 60)
print(f"Initial Python Process RAM:      {ram_init / (1024*1024):.1f} MB")
print(f"RAM after DistilBERT load:       {ram_after_distilbert / (1024*1024):.1f} MB (Delta: +{(ram_after_distilbert - ram_init) / (1024*1024):.1f} MB)")
print(f"RAM after all-MiniLM-L6-v2 load: {ram_after_minilm / (1024*1024):.1f} MB (Delta: +{(ram_after_minilm - ram_after_distilbert) / (1024*1024):.1f} MB)")
print(f"Total Process RAM with Both Models: {ram_after_minilm / (1024*1024):.1f} MB")
print("-" * 60)
print(f"DistilBERT Load Time:    {t_distilbert_load:.2f} s")
print(f"all-MiniLM-L6-v2 Load:   {t_minilm_load:.2f} s")
print(f"DistilBERT CPU Latency:  {latency_distilbert:.1f} ms")
print(f"all-MiniLM CPU Latency:  {latency_matching:.1f} ms (dual-engine matching)")
print("=" * 60)
print("REAL MATCHING RESULTS:")
print(f"Role: {match_result.job_title}")
print(f"Semantic Similarity: {match_result.semantic_match.similarity_percentage}% ({match_result.semantic_match.similarity_score}) [{match_result.semantic_match.similarity_level}]")
print(f"Skill Coverage:      {match_result.skill_match.match_percentage}% ({match_result.skill_match.matched_count}/{match_result.skill_match.total_jd_skills} skills)")
print(f"Matching Skills:     {match_result.skill_match.matching_skills}")
print(f"Missing Skills:      {match_result.skill_match.missing_skills}")
print(f"Additional Skills:   {match_result.skill_match.additional_skills}")
print("\nGenerated Suggestions:")
for i, s in enumerate(match_result.suggestions, 1):
    print(f"  {i}. {s}")
print("=" * 60)
