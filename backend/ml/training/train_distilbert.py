"""
Phase 8: DistilBERT Job Role Prediction Model Training Pipeline
Trains the first 24-category DistilBERT job classifier on CPU.

Specifications:
- Model: distilbert-base-uncased (24 output classes)
- Sequence length: 256 tokens
- Batch size: 16
- Epochs: 3 (124 steps/epoch, 372 total steps)
- Optimizer: AdamW (lr=2e-5, weight_decay=0.01)
- Scheduler: Linear warmup (10% = 37 steps) + linear decay
- Loss: Weighted Cross-Entropy (balanced class weights)
- Primary metric: Validation Macro F1
- Dataset: 2,481 unique resumes from opensporks_sanitized.csv
- Split: Group-Stratified 80/10/10 (Train: 1,979, Val: 251, Test: 251, 0 cluster crossover)
- Checkpoints:
  * Best validation checkpoint: backend/ml/saved_models/distilbert_job_classifier/
  * Epoch resume checkpoints: backend/ml/saved_models/epoch_checkpoints/
- Evaluation: Evaluated on untouched test partition; saves metrics to backend/ml/evaluation/
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
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score, precision_score, recall_score

# Directories
ML_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = ML_DIR.parent
SANITIZED_CSV = ML_DIR / "datasets" / "processed" / "opensporks_sanitized.csv"
BEST_MODEL_DIR = ML_DIR / "saved_models" / "distilbert_job_classifier"
EPOCH_CHECKPOINTS_DIR = ML_DIR / "saved_models" / "epoch_checkpoints"
EVALUATION_DIR = ML_DIR / "evaluation"
REPORTS_DIR = ML_DIR / "datasets" / "reports"

# Hardware / Device configuration
DEVICE = torch.device("cpu")
MAX_SEQ_LENGTH = 256
BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.10
SYSTEM_RAM_LIMIT_PERCENT = 90.0


def get_process_memory_mb() -> float:
    """Return process resident set size (RSS) in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def get_system_ram_percent() -> float:
    """Return system RAM usage percent."""
    return psutil.virtual_memory().percent


def load_unique_dataset() -> Tuple[List[Dict[str, Any]], Dict[str, int], Dict[int, str]]:
    """Load sanitized primary dataset and deduplicate to exactly 2,481 unique resumes."""
    rows = []
    with open(SANITIZED_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if int(r["word_count"]) > 0:
                rows.append(r)

    # Deduplicate via SHA-256 of lowercase whitespace-collapsed text
    hashes = defaultdict(list)
    for r in rows:
        norm = re.sub(r"\s+", " ", r["text"].lower().strip())
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        hashes[h].append(r)

    unique_resumes = [items[0] for items in hashes.values()]
    assert len(unique_resumes) == 2481, f"Expected 2481 unique resumes, got {len(unique_resumes)}"

    categories = sorted(list(set(r["category"] for r in unique_resumes)))
    assert len(categories) == 24, f"Expected 24 categories, got {len(categories)}"

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

    cluster_to_records = defaultdict(list)
    for r in records:
        cluster_to_records[r["cluster_id"]].append(r)

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

    # Verification of strict disjointness
    assert len(train_cids & val_cids) == 0, "Cluster leak between Train and Val"
    assert len(train_cids & test_cids) == 0, "Cluster leak between Train and Test"
    assert len(val_cids & test_cids) == 0, "Cluster leak between Val and Test"

    return train_records, val_records, test_records


def calculate_balanced_class_weights(
    train_records: List[Dict[str, Any]],
    label2id: Dict[str, int]
) -> torch.Tensor:
    """
    Calculate balanced class weights on the training partition:
    W_c = N_train / (N_classes * N_c)
    """
    n_total = len(train_records)
    n_classes = len(label2id)
    cat_counts = Counter(r["category"] for r in train_records)

    weights = [0.0] * n_classes
    for cat, idx in label2id.items():
        cnt = cat_counts[cat]
        weights[idx] = n_total / (n_classes * cnt)

    return torch.tensor(weights, dtype=torch.float, device=DEVICE)


def tokenize_partition(
    records: List[Dict[str, Any]],
    tokenizer: AutoTokenizer,
    label2id: Dict[str, int],
    max_length: int = 256
) -> TensorDataset:
    """Tokenize texts and build a PyTorch TensorDataset."""
    texts = [r["text"] for r in records]
    labels = [label2id[r["category"]] for r in records]

    encoded = tokenizer(
        texts,
        max_length=max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )

    return TensorDataset(
        encoded["input_ids"],
        encoded["attention_mask"],
        torch.tensor(labels, dtype=torch.long)
    )


def evaluate_dataset(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    id2label: Dict[int, str]
) -> Dict[str, Any]:
    """Evaluate model on a DataLoader and compute loss, accuracy, Macro F1, and Weighted F1."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids, attention_mask, labels = [t.to(DEVICE) for t in batch]
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)

            total_loss += loss.item() * len(labels)
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(all_targets)
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    accuracy = accuracy_score(all_targets, all_preds)

    return {
        "loss": round(avg_loss, 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "accuracy": round(float(accuracy), 4),
        "predictions": all_preds,
        "targets": all_targets
    }


def train_distilbert_pipeline() -> Dict[str, Any]:
    print("=" * 70)
    print("CareerAI Phase 8: DistilBERT Job Role Prediction Model Training")
    print("=" * 70)

    # Hardware & System Info
    vm = psutil.virtual_memory()
    total_ram_gb = vm.total / (1024**3)
    avail_ram_gb = vm.available / (1024**3)
    print(f"Hardware: Intel Core i7-1355U (12 logical cores) | RAM: {total_ram_gb:.2f} GB ({avail_ram_gb:.2f} GB free)")
    print(f"Device: {DEVICE} | PyTorch: {torch.__version__} | CUDA Available: {torch.cuda.is_available()}")

    # Set CPU threads
    num_threads = min(os.cpu_count() or 4, 8)
    torch.set_num_threads(num_threads)
    print(f"Configured PyTorch OpenMP/MKL worker threads: {torch.get_num_threads()}")

    # 1. Dataset & Splitting
    print("\n[Step 1/5] Loading primary dataset and creating group-stratified splits...")
    unique_resumes, label2id, id2label = load_unique_dataset()
    train_records, val_records, test_records = group_stratified_split(unique_resumes, seed=42)

    print(f"  Total Unique Resumes: {len(unique_resumes)}")
    print(f"  Training Set:   {len(train_records)} records")
    print(f"  Validation Set: {len(val_records)} records")
    print(f"  Test Set:       {len(test_records)} records")
    print(f"  Classes:        {len(label2id)} categories")

    # 2. Class Weights Calculation
    print("\n[Step 2/5] Calculating balanced class weights for training loss...")
    class_weights = calculate_balanced_class_weights(train_records, label2id)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    train_cat_counts = Counter(r["category"] for r in train_records)
    print("  Sample Class Weights (min/max):")
    min_cat = min(train_cat_counts.keys(), key=lambda c: train_cat_counts[c])
    max_cat = max(train_cat_counts.keys(), key=lambda c: train_cat_counts[c])
    print(f"    - Min Category ({min_cat}: {train_cat_counts[min_cat]} samples) -> Weight: {class_weights[label2id[min_cat]]:.4f}")
    print(f"    - Max Category ({max_cat}: {train_cat_counts[max_cat]} samples) -> Weight: {class_weights[label2id[max_cat]]:.4f}")

    # 3. Tokenization & DataLoaders
    print(f"\n[Step 3/5] Tokenizing partitions ('distilbert-base-uncased', max_length={MAX_SEQ_LENGTH})...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    t_tok = time.perf_counter()
    train_dataset = tokenize_partition(train_records, tokenizer, label2id, max_length=MAX_SEQ_LENGTH)
    val_dataset = tokenize_partition(val_records, tokenizer, label2id, max_length=MAX_SEQ_LENGTH)
    test_dataset = tokenize_partition(test_records, tokenizer, label2id, max_length=MAX_SEQ_LENGTH)
    print(f"  Tokenization completed in {time.perf_counter() - t_tok:.2f}s")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    total_steps_per_epoch = len(train_loader)
    total_training_steps = total_steps_per_epoch * EPOCHS
    warmup_steps = round(total_training_steps * WARMUP_RATIO)
    print(f"  DataLoader steps per epoch: {total_steps_per_epoch} (Batch size: {BATCH_SIZE})")
    print(f"  Total training steps: {total_training_steps} | Warmup steps: {warmup_steps}")

    # 4. Model & Optimizer Initialization
    print(f"\n[Step 4/5] Initializing DistilBERT with 24-class classification head...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id
    )
    model.to(DEVICE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_training_steps
    )

    # Check for existing epoch checkpoints to support resuming
    EPOCH_CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    start_epoch = 1
    best_val_macro_f1 = -1.0
    history = []

    # Check if a checkpoint can be resumed
    latest_saved_epoch = 0
    for ep in range(EPOCHS, 0, -1):
        cp_file = EPOCH_CHECKPOINTS_DIR / f"epoch_{ep}.pt"
        if cp_file.exists():
            latest_saved_epoch = ep
            break

    if latest_saved_epoch > 0 and latest_saved_epoch < EPOCHS:
        print(f"  Found existing checkpoint from Epoch {latest_saved_epoch}. Loading to resume...")
        cp = torch.load(EPOCH_CHECKPOINTS_DIR / f"epoch_{latest_saved_epoch}.pt", map_location=DEVICE)
        model.load_state_dict(cp["model_state"])
        optimizer.load_state_dict(cp["optimizer_state"])
        scheduler.load_state_dict(cp["scheduler_state"])
        start_epoch = latest_saved_epoch + 1
        best_val_macro_f1 = cp.get("best_val_macro_f1", -1.0)
        history = cp.get("history", [])
        print(f"  Resuming training from Epoch {start_epoch} (Best prior Val Macro F1: {best_val_macro_f1:.4f})")
    else:
        print(f"  Starting fresh training run from Epoch 1...")

    # Tracking metrics
    peak_rss_mb = get_process_memory_mb()
    total_train_start = time.perf_counter()
    cpu_percents = []

    # Prime CPU percent measurement
    psutil.cpu_percent(interval=None)

    # 5. Training Loop
    print("\n[Step 5/5] Commencing 3-Epoch Training Loop...")
    for epoch in range(start_epoch, EPOCHS + 1):
        epoch_start_time = time.perf_counter()
        model.train()
        epoch_train_loss = 0.0
        step_times = []

        print(f"\n{'='*30} EPOCH {epoch}/{EPOCHS} {'='*30}")

        for step, batch in enumerate(train_loader, 1):
            t_step0 = time.perf_counter()

            # Safety check: system RAM
            ram_percent = get_system_ram_percent()
            if ram_percent >= SYSTEM_RAM_LIMIT_PERCENT:
                print(f"\n[SAFETY ABORT] Overall system RAM reached {ram_percent:.1f}% >= {SYSTEM_RAM_LIMIT_PERCENT}% limit!")
                raise MemoryError(f"System RAM exceeded safe limit: {ram_percent:.1f}%")

            input_ids, attention_mask, labels = [t.to(DEVICE) for t in batch]
            optimizer.zero_grad()

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)

            loss.backward()
            optimizer.step()
            scheduler.step()

            step_elapsed = time.perf_counter() - t_step0
            step_times.append(step_elapsed)
            epoch_train_loss += loss.item() * len(labels)

            current_rss_mb = get_process_memory_mb()
            if current_rss_mb > peak_rss_mb:
                peak_rss_mb = current_rss_mb

            # Display progress after every 5 batches (and batch 1, and final batch)
            if step % 5 == 0 or step == 1 or step == total_steps_per_epoch:
                step_cpu = psutil.cpu_percent(interval=None)
                cpu_percents.append(step_cpu)
                samples_done = min(step * BATCH_SIZE, len(train_dataset))
                avg_step_sec = sum(step_times[-5:]) / len(step_times[-5:])
                elapsed_epoch_sec = time.perf_counter() - epoch_start_time
                current_lr = scheduler.get_last_lr()[0]

                print(
                    f"  Epoch {epoch}/{EPOCHS} | "
                    f"Step {step:3d}/{total_steps_per_epoch} | "
                    f"Samples: {samples_done:4d}/{len(train_dataset)} | "
                    f"Loss: {loss.item():.4f} | "
                    f"Step: {step_elapsed:.2f}s (Avg5: {avg_step_sec:.2f}s) | "
                    f"Elapsed: {elapsed_epoch_sec/60:.1f}m | "
                    f"LR: {current_lr:.2e} | "
                    f"RSS: {current_rss_mb:.1f}MB | RAM: {ram_percent:.1f}% | CPU: {step_cpu:.1f}%"
                )

        epoch_elapsed_sec = time.perf_counter() - epoch_start_time
        avg_epoch_train_loss = epoch_train_loss / len(train_dataset)

        # Validation at end of epoch
        print(f"\n  Validating Epoch {epoch} on {len(val_dataset)} validation samples...")
        val_metrics = evaluate_dataset(model, val_loader, criterion, id2label)

        print(f"  --- Epoch {epoch} Validation Results ---")
        print(f"    Train Loss:      {avg_epoch_train_loss:.4f}")
        print(f"    Validation Loss: {val_metrics['loss']:.4f}")
        print(f"    Validation Acc:  {val_metrics['accuracy']*100:.2f}%")
        print(f"    Validation Macro F1:    {val_metrics['macro_f1']:.4f} (Primary Metric)")
        print(f"    Validation Weighted F1: {val_metrics['weighted_f1']:.4f}")
        print(f"    Epoch Runtime:   {epoch_elapsed_sec/60:.2f} minutes")

        is_best = val_metrics["macro_f1"] > best_val_macro_f1
        if is_best:
            best_val_macro_f1 = val_metrics["macro_f1"]
            print(f"    >>> NEW BEST VALIDATION MACRO F1: {best_val_macro_f1:.4f}! Saving checkpoint...")
            BEST_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(BEST_MODEL_DIR)
            tokenizer.save_pretrained(BEST_MODEL_DIR)

            # Save label mapping with model
            with open(BEST_MODEL_DIR / "label_mapping.json", "w", encoding="utf-8") as f:
                json.dump({"label2id": label2id, "id2label": id2label}, f, indent=2)

        # Save epoch checkpoint for resumption safety
        epoch_checkpoint_path = EPOCH_CHECKPOINTS_DIR / f"epoch_{epoch}.pt"
        torch.save({
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "best_val_macro_f1": best_val_macro_f1,
            "train_loss": avg_epoch_train_loss,
            "val_metrics": val_metrics,
            "history": history
        }, epoch_checkpoint_path)
        print(f"    Epoch state saved to: {epoch_checkpoint_path}")

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(avg_epoch_train_loss, 4),
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_weighted_f1": val_metrics["weighted_f1"],
            "epoch_runtime_seconds": round(epoch_elapsed_sec, 2),
            "epoch_runtime_minutes": round(epoch_elapsed_sec / 60, 2),
            "is_best": is_best
        }
        history.append(epoch_record)

    total_training_time_sec = time.perf_counter() - total_train_start
    avg_cpu_percent = round(sum(cpu_percents) / len(cpu_percents), 1) if cpu_percents else 0.0

    print("\n" + "=" * 70)
    print("Training Complete across all 3 Epochs!")
    print(f"Total Elapsed Time: {total_training_time_sec/60:.2f} minutes ({total_training_time_sec:.2f}s)")
    print(f"Peak Process Memory (RSS): {peak_rss_mb:.2f} MB ({peak_rss_mb/1024:.2f} GB)")
    print(f"Average CPU Load: {avg_cpu_percent}%")
    print(f"Best Validation Macro F1: {best_val_macro_f1:.4f}")
    print(f"Best Model Directory: {BEST_MODEL_DIR}")

    # Save training configuration & metrics summary
    training_summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": {
            "processor": "Intel Core i7-1355U (12 logical cores)",
            "device": "cpu",
            "threads_used": torch.get_num_threads(),
            "total_system_ram_gb": round(total_ram_gb, 2)
        },
        "hyperparameters": {
            "model_name": "distilbert-base-uncased",
            "num_classes": 24,
            "sequence_length": MAX_SEQ_LENGTH,
            "batch_size": BATCH_SIZE,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "warmup_ratio": WARMUP_RATIO,
            "total_steps": total_training_steps,
            "loss_function": "Weighted Cross-Entropy"
        },
        "dataset_split": {
            "dataset_name": "opensporks_sanitized",
            "total_unique": len(unique_resumes),
            "train_samples": len(train_records),
            "val_samples": len(val_records),
            "test_samples": len(test_records)
        },
        "training_performance": {
            "total_training_seconds": round(total_training_time_sec, 2),
            "total_training_minutes": round(total_training_time_sec / 60, 2),
            "peak_process_rss_mb": round(peak_rss_mb, 2),
            "peak_process_rss_gb": round(peak_rss_mb / 1024, 2),
            "average_cpu_percent": avg_cpu_percent,
            "best_val_macro_f1": best_val_macro_f1
        },
        "epoch_history": history
    }

    with open(BEST_MODEL_DIR / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(training_summary, f, indent=2)

    # 6. Final Test Evaluation
    print("\n" + "=" * 70)
    print("Executing Final Evaluation on Untouched Test Partition (251 samples)...")
    print("=" * 70)

    # Load best checkpoint strictly from disk
    print(f"Loading best saved checkpoint from: {BEST_MODEL_DIR}...")
    best_model = AutoModelForSequenceClassification.from_pretrained(BEST_MODEL_DIR)
    best_model.to(DEVICE)
    best_model.eval()

    test_metrics = evaluate_dataset(best_model, test_loader, criterion, id2label)
    test_preds = test_metrics["predictions"]
    test_targets = test_metrics["targets"]

    test_acc = accuracy_score(test_targets, test_preds)
    test_macro_f1 = f1_score(test_targets, test_preds, average="macro", zero_division=0)
    test_weighted_f1 = f1_score(test_targets, test_preds, average="weighted", zero_division=0)
    test_macro_p = precision_score(test_targets, test_preds, average="macro", zero_division=0)
    test_macro_r = recall_score(test_targets, test_preds, average="macro", zero_division=0)

    print(f"\nTest Set Results (N = {len(test_targets)}):")
    print(f"  Overall Accuracy:   {test_acc * 100:.2f}%")
    print(f"  Macro F1 (Primary): {test_macro_f1:.4f}")
    print(f"  Weighted F1:        {test_weighted_f1:.4f}")
    print(f"  Macro Precision:    {test_macro_p:.4f}")
    print(f"  Macro Recall:       {test_macro_r:.4f}")
    print(f"  Test Loss:          {test_metrics['loss']:.4f}")

    # Generate classification report
    category_names = [id2label[i] for i in range(len(id2label))]
    cls_report_dict = classification_report(
        test_targets,
        test_preds,
        target_names=category_names,
        output_dict=True,
        zero_division=0
    )
    cls_report_text = classification_report(
        test_targets,
        test_preds,
        target_names=category_names,
        digits=4,
        zero_division=0
    )

    print("\nClassification Report by Category:")
    print(cls_report_text)

    # Generate Confusion Matrix
    cm = confusion_matrix(test_targets, test_preds)

    # Save all evaluation outputs
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    with open(EVALUATION_DIR / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_sample_count": len(test_targets),
            "accuracy": round(float(test_acc), 4),
            "macro_f1": round(float(test_macro_f1), 4),
            "weighted_f1": round(float(test_weighted_f1), 4),
            "macro_precision": round(float(test_macro_p), 4),
            "macro_recall": round(float(test_macro_r), 4),
            "test_loss": test_metrics["loss"]
        }, f, indent=2)

    with open(EVALUATION_DIR / "per_category_metrics.json", "w", encoding="utf-8") as f:
        json.dump(cls_report_dict, f, indent=2)

    with open(EVALUATION_DIR / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(cls_report_text)

    # Save Confusion Matrix JSON & CSV
    cm_dict = {
        "categories": category_names,
        "matrix": cm.tolist()
    }
    with open(EVALUATION_DIR / "confusion_matrix.json", "w", encoding="utf-8") as f:
        json.dump(cm_dict, f, indent=2)

    with open(EVALUATION_DIR / "confusion_matrix.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["True_Category \\ Predicted"] + category_names)
        for i, row in enumerate(cm):
            writer.writerow([category_names[i]] + list(row))

    print(f"\nEvaluation files successfully saved to: {EVALUATION_DIR}")
    print(f"  - test_metrics.json")
    print(f"  - per_category_metrics.json")
    print(f"  - classification_report.txt")
    print(f"  - confusion_matrix.json")
    print(f"  - confusion_matrix.csv")

    return {
        "training_summary": training_summary,
        "test_metrics": {
            "accuracy": test_acc,
            "macro_f1": test_macro_f1,
            "weighted_f1": test_weighted_f1,
            "macro_precision": test_macro_p,
            "macro_recall": test_macro_r,
            "loss": test_metrics["loss"]
        },
        "classification_report_dict": cls_report_dict,
        "classification_report_text": cls_report_text,
        "confusion_matrix": cm.tolist()
    }


if __name__ == "__main__":
    try:
        results = train_distilbert_pipeline()
        print("\nPhase 8 Training Pipeline completed successfully.")
    except Exception as exc:
        print(f"\nTraining Pipeline Error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
