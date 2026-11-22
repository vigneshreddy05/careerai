"""
Phase 7: Controlled One-Epoch CPU Benchmark for DistilBERT Role Classifier
Hardware: Intel Core i7-1355U (12 logical cores), 16 GB RAM, Intel Iris Xe (CPU only)
Model: distilbert-base-uncased (24 categories)
Dataset: 2,481 unique resumes from opensporks_sanitized.csv
Split: Group-Stratified 80/10/10 (1,985 training records, 0 cluster crossover)

Records:
- Wall-clock elapsed training time via time.perf_counter()
- Throughput (samples/sec and steps/sec)
- Peak Resident Set Size (RSS) memory via psutil
- CPU utilization via psutil
- Step-by-step progress and loss trajectory
- Safety memory guard (>12 GB abort)
"""

import os
import sys
import csv
import time
import json
import math
import hashlib
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any

import psutil
import torch
from torch.utils.data import TensorDataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SANITIZED_CSV = BASE_DIR / "datasets" / "processed" / "opensporks_sanitized.csv"
CHECKPOINT_DIR = BASE_DIR / "saved_models" / "benchmark_checkpoint"
REPORTS_DIR = BASE_DIR / "datasets" / "reports"
BENCHMARK_JSON = REPORTS_DIR / "cpu_benchmark_results.json"


def get_process_memory_mb() -> float:
    """Return current process RSS memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_system_memory_info() -> Dict[str, float]:
    """Return system memory usage info in GB."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent": mem.percent
    }


def load_unique_dataset() -> Tuple[List[Dict[str, Any]], Dict[str, int], Dict[int, str]]:
    """Load sanitized opensporks dataset and deduplicate to exactly 2,481 unique resumes."""
    rows = []
    with open(SANITIZED_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if int(r["word_count"]) > 0:
                rows.append(r)

    # Deduplicate via SHA-256 of normalized text
    hashes = defaultdict(list)
    for r in rows:
        norm = re.sub(r"\s+", " ", r["text"].lower().strip())
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        hashes[h].append(r)

    # Take the first record for each unique hash
    unique_resumes = [items[0] for items in hashes.values()]
    assert len(unique_resumes) == 2481, f"Expected 2481 unique resumes, got {len(unique_resumes)}"

    # Build deterministic label mappings
    categories = sorted(list(set(r["category"] for r in unique_resumes)))
    label2id = {cat: idx for idx, cat in enumerate(categories)}
    id2label = {idx: cat for idx, cat in enumerate(categories)}

    return unique_resumes, label2id, id2label


def group_stratified_split(
    records: List[Dict[str, Any]],
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Perform group-stratified 80/10/10 split ensuring cluster isolation."""
    import random
    random.seed(seed)

    # Group records by cluster_id
    cluster_to_records = defaultdict(list)
    for r in records:
        cluster_to_records[r["cluster_id"]].append(r)

    # Group clusters by majority category
    cat_to_clusters = defaultdict(list)
    for cid, members in cluster_to_records.items():
        primary_cat = Counter(m["category"] for m in members).most_common(1)[0][0]
        cat_to_clusters[primary_cat].append((cid, members))

    train_cids, val_cids, test_cids = set(), set(), set()
    train_records, val_records, test_records = [], [], []

    for cat in sorted(cat_to_clusters.keys()):
        clusters = cat_to_clusters[cat]
        random.shuffle(clusters)
        n_clusters = len(clusters)
        n_val = max(1, round(n_clusters * 0.10))
        n_test = max(1, round(n_clusters * 0.10))
        n_train = n_clusters - n_val - n_test

        for cid, members in clusters[:n_train]:
            train_cids.add(cid)
            train_records.extend(members)
        for cid, members in clusters[n_train:n_train + n_val]:
            val_cids.add(cid)
            val_records.extend(members)
        for cid, members in clusters[n_train + n_val:]:
            test_cids.add(cid)
            test_records.extend(members)

    # Assert strict cluster disjointness
    assert len(train_cids & val_cids) == 0, "Cluster leak between Train and Val"
    assert len(train_cids & test_cids) == 0, "Cluster leak between Train and Test"
    assert len(val_cids & test_cids) == 0, "Cluster leak between Val and Test"

    return train_records, val_records, test_records


def run_cpu_benchmark(
    batch_size: int = 16,
    max_length: int = 256,
    learning_rate: float = 2e-5,
    max_memory_gb_guard: float = 12.0
) -> Dict[str, Any]:
    print("=" * 65)
    print("CareerAI Phase 7: Controlled One-Epoch CPU Benchmark")
    print("=" * 65)

    system_mem = get_system_memory_info()
    print(f"System Hardware: Intel Core i7-1355U (12 logical cores, CPU only)")
    print(f"System RAM: {system_mem['total_gb']} GB total ({system_mem['available_gb']} GB available, {system_mem['percent']}% used)")
    print(f"PyTorch Version: {torch.__version__} | Device: cpu | CUDA: {torch.cuda.is_available()}")

    # 1. Dataset & Splitting
    print("\n[1/5] Loading unique dataset and preparing group-stratified splits...")
    unique_resumes, label2id, id2label = load_unique_dataset()
    train_records, val_records, test_records = group_stratified_split(unique_resumes, seed=42)
    print(f"  Total Unique Resumes: {len(unique_resumes)}")
    print(f"  Training Split (80%): {len(train_records)} records")
    print(f"  Validation Split (10%): {len(val_records)} records")
    print(f"  Test Split (10%): {len(test_records)} records")
    print(f"  Categories: {len(label2id)} classes")

    # 2. Tokenization
    print(f"\n[2/5] Initializing tokenizer ('distilbert-base-uncased', max_length={max_length})...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    train_texts = [r["text"] for r in train_records]
    train_labels = [label2id[r["category"]] for r in train_records]

    t_tok_start = time.perf_counter()
    encoded = tokenizer(
        train_texts,
        max_length=max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    t_tok_elapsed = time.perf_counter() - t_tok_start
    print(f"  Tokenization completed in {t_tok_elapsed:.2f}s ({len(train_texts)/t_tok_elapsed:.1f} samples/sec)")

    dataset = TensorDataset(
        encoded["input_ids"],
        encoded["attention_mask"],
        torch.tensor(train_labels, dtype=torch.long)
    )
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    total_steps = len(dataloader)
    print(f"  DataLoader initialized: {len(dataset)} samples, batch_size={batch_size}, total_steps={total_steps}")

    # 3. Model Initialization
    print(f"\n[3/5] Loading 'distilbert-base-uncased' with 24 classification heads...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id
    )
    model.to("cpu")
    model.train()

    # Configure CPU threads
    num_threads = min(os.cpu_count() or 4, 8)
    torch.set_num_threads(num_threads)
    print(f"  Model loaded onto CPU. PyTorch OpenMP/MKL threads configured: {torch.get_num_threads()}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    initial_rss_mb = get_process_memory_mb()
    print(f"  Initial process memory (RSS): {initial_rss_mb:.2f} MB")

    # 4. Benchmark Execution Loop (1 Epoch)
    print(f"\n[4/5] Executing Benchmark Training Epoch (1 Epoch = {total_steps} steps)...")
    peak_rss_mb = initial_rss_mb
    step_times = []
    loss_history = []
    cpu_percents = []

    # Prime CPU percent measurement
    psutil.cpu_percent(interval=None)

    t_train_start = time.perf_counter()

    for step, batch in enumerate(dataloader, 1):
        step_t0 = time.perf_counter()

        input_ids, attention_mask, labels = batch
        optimizer.zero_grad()

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss
        loss.backward()
        optimizer.step()

        step_elapsed = time.perf_counter() - step_t0
        step_times.append(step_elapsed)
        loss_val = loss.item()
        loss_history.append(loss_val)

        # Track memory and CPU
        current_rss_mb = get_process_memory_mb()
        if current_rss_mb > peak_rss_mb:
            peak_rss_mb = current_rss_mb

        if step % 25 == 0 or step == total_steps or step == 1:
            step_cpu = psutil.cpu_percent(interval=None)
            cpu_percents.append(step_cpu)
            samples_done = min(step * batch_size, len(dataset))
            avg_step_sec = sum(step_times[-25:]) / len(step_times[-25:])
            print(
                f"  Step {step:3d}/{total_steps} | "
                f"Samples: {samples_done:4d}/{len(dataset)} | "
                f"Loss: {loss_val:.4f} | "
                f"Step Time: {step_elapsed:.2f}s (Avg: {avg_step_sec:.2f}s) | "
                f"RSS: {current_rss_mb:.1f} MB | CPU: {step_cpu:.1f}%"
            )

        # Safety memory guard
        current_rss_gb = current_rss_mb / 1024
        if current_rss_gb > max_memory_gb_guard:
            print(f"\n[ABORT GUARD] Process RSS memory exceeded safety threshold: {current_rss_gb:.2f} GB > {max_memory_gb_guard} GB")
            raise MemoryError(f"Safety guard triggered: process memory reached {current_rss_gb:.2f} GB")

    t_train_elapsed = time.perf_counter() - t_train_start
    final_rss_mb = get_process_memory_mb()

    # Throughput metrics
    total_samples = len(dataset)
    samples_per_sec = total_samples / t_train_elapsed
    steps_per_sec = total_steps / t_train_elapsed
    avg_step_time = t_train_elapsed / total_steps
    avg_cpu_percent = round(sum(cpu_percents) / len(cpu_percents), 1) if cpu_percents else 0.0

    print("\nBenchmark Execution Complete!")
    print(f"  Actual Elapsed Time:  {t_train_elapsed:.2f} seconds ({t_train_elapsed/60:.2f} minutes)")
    print(f"  Throughput:           {samples_per_sec:.2f} samples/sec ({steps_per_sec:.2f} steps/sec)")
    print(f"  Average Step Time:    {avg_step_time:.3f} seconds/step")
    print(f"  Initial Process RSS:  {initial_rss_mb:.2f} MB")
    print(f"  Peak Process RSS:     {peak_rss_mb:.2f} MB ({peak_rss_mb/1024:.2f} GB)")
    print(f"  Final Process RSS:    {final_rss_mb:.2f} MB")
    print(f"  Average CPU Load:     {avg_cpu_percent}%")
    print(f"  Loss Reduction:       {loss_history[0]:.4f} (Step 1) -> {loss_history[-1]:.4f} (Step {total_steps})")

    # 5. Checkpoint Saving
    print(f"\n[5/5] Saving benchmark checkpoint to: {CHECKPOINT_DIR}...")
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(CHECKPOINT_DIR)
    tokenizer.save_pretrained(CHECKPOINT_DIR)

    # Save metadata JSON
    results = {
        "benchmark_status": "SUCCESS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": {
            "processor": "Intel Core i7-1355U (12 logical cores)",
            "device": "cpu",
            "threads_used": torch.get_num_threads(),
            "cuda_available": False,
            "system_ram_gb": system_mem["total_gb"]
        },
        "model_configuration": {
            "model_name": "distilbert-base-uncased",
            "parameters": sum(p.numel() for p in model.parameters()),
            "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
            "num_classes": len(label2id),
            "sequence_length": max_length,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "epochs_run": 1,
            "total_steps": total_steps
        },
        "dataset_split": {
            "total_unique_resumes": len(unique_resumes),
            "train_samples": len(train_records),
            "val_samples": len(val_records),
            "test_samples": len(test_records),
            "cluster_leakage_check": "VERIFIED_ZERO_LEAKAGE"
        },
        "empirical_measurements": {
            "elapsed_training_seconds": round(t_train_elapsed, 2),
            "elapsed_training_minutes": round(t_train_elapsed / 60, 2),
            "samples_per_second": round(samples_per_sec, 2),
            "steps_per_second": round(steps_per_sec, 2),
            "average_step_time_seconds": round(avg_step_time, 3),
            "initial_process_rss_mb": round(initial_rss_mb, 2),
            "peak_process_rss_mb": round(peak_rss_mb, 2),
            "peak_process_rss_gb": round(peak_rss_mb / 1024, 2),
            "final_process_rss_mb": round(final_rss_mb, 2),
            "average_cpu_percent": avg_cpu_percent,
            "initial_loss": round(loss_history[0], 4),
            "final_loss": round(loss_history[-1], 4)
        },
        "saved_checkpoint_path": str(CHECKPOINT_DIR)
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Benchmark results JSON written to: {BENCHMARK_JSON}")

    return results


if __name__ == "__main__":
    try:
        run_cpu_benchmark(batch_size=16, max_length=256, learning_rate=2e-5)
    except Exception as exc:
        print(f"\nBenchmark Error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
