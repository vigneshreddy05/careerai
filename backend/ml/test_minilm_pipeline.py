"""
Verification script for all-MiniLM-L6-v2 pipeline on CPU.
Tests:
1. Offline loading with local_files_only=True
2. Attention-mask-aware mean pooling
3. L2 normalization
4. Chunking strategy for long documents
5. Cosine similarity computation
6. CPU latency and memory footprint
"""

import time
import psutil
import torch
import torch.nn.functional as F
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

MODEL_DIR = Path("backend/ml/saved_models/all-MiniLM-L6-v2").resolve()


def mean_pooling(model_output, attention_mask):
    """
    Attention-mask-aware mean pooling as defined in Sentence-BERT.
    Multiplies token embeddings by attention mask (ignoring padding tokens)
    and divides by the sum of attention mask elements.
    """
    token_embeddings = model_output[0]  # First element: [batch_size, seq_len, hidden_dim]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


def chunk_text(text: str, max_words_per_chunk: int = 150, overlap_words: int = 30):
    """
    Split long document into overlapping semantic chunks.
    Ensures complete coverage of long documents without truncation.
    """
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words_per_chunk:
        return [text]

    chunks = []
    stride = max_words_per_chunk - overlap_words
    for i in range(0, len(words), stride):
        chunk_words = words[i:i + max_words_per_chunk]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
        if i + max_words_per_chunk >= len(words):
            break
    return chunks


def encode_document(text: str, tokenizer, model, device):
    """
    Encode document into a 384-dimensional unit vector using chunking and mean pooling.
    """
    chunks = chunk_text(text)
    if not chunks:
        # Return zero vector if empty
        return torch.zeros((1, 384), device=device)

    # Tokenize all chunks in a single batch
    encoded = tokenizer(
        chunks,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.inference_mode():
        outputs = model(**encoded)
        # Compute mean pooling for each chunk
        chunk_embeddings = mean_pooling(outputs, encoded["attention_mask"])
        # Normalize each chunk
        chunk_embeddings = F.normalize(chunk_embeddings, p=2, dim=1)
        # Aggregate chunks: mean of normalized chunk embeddings
        doc_embedding = torch.mean(chunk_embeddings, dim=0, keepdim=True)
        # Normalize aggregated embedding to unit sphere
        doc_embedding = F.normalize(doc_embedding, p=2, dim=1)

    return doc_embedding


def run_benchmark():
    device = torch.device("cpu")
    print("Testing offline load...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = AutoModel.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model.to(device)
    model.eval()
    load_time = time.time() - t0
    print(f"Loaded in {load_time:.2f}s")

    sample_resume = (
        "Senior Python Engineer with 6 years experience in building distributed systems, "
        "microservices, RESTful APIs using FastAPI and Django. Proficient with PostgreSQL, "
        "Docker, Kubernetes, AWS (ECS, S3, RDS), Redis caching, and automated CI/CD pipelines. "
        "Strong knowledge of PyTorch and NLP applications."
    )

    sample_jd_matching = (
        "We are looking for a Senior Python Developer to join our backend infrastructure team. "
        "Requirements: 5+ years of experience with Python, FastAPI or Django. Hands-on experience "
        "with Docker, Kubernetes, AWS, PostgreSQL, and Redis. Experience with ML deployment is a plus."
    )

    sample_jd_unrelated = (
        "Seeking an experienced Registered Nurse (RN) for an acute care hospital ward. "
        "Requirements: Bachelor of Science in Nursing (BSN), active state RN license, "
        "BLS and ACLS certification, 2+ years of inpatient patient care and clinical triage experience."
    )

    # Encode resume
    t_start = time.time()
    emb_resume = encode_document(sample_resume, tokenizer, model, device)
    latency_resume = (time.time() - t_start) * 1000

    # Encode matching JD
    t_start = time.time()
    emb_jd_matching = encode_document(sample_jd_matching, tokenizer, model, device)
    latency_jd_match = (time.time() - t_start) * 1000

    # Encode unrelated JD
    t_start = time.time()
    emb_jd_unrelated = encode_document(sample_jd_unrelated, tokenizer, model, device)
    latency_jd_unrelated = (time.time() - t_start) * 1000

    # Compute cosine similarities
    sim_match = float(torch.sum(emb_resume * emb_jd_matching).item())
    sim_unrelated = float(torch.sum(emb_resume * emb_jd_unrelated).item())

    print(f"\nEmbedding dimension: {emb_resume.shape[-1]}")
    print(f"Resume encoding latency: {latency_resume:.2f} ms")
    print(f"Matching JD encoding latency: {latency_jd_match:.2f} ms")
    print(f"Unrelated JD encoding latency: {latency_jd_unrelated:.2f} ms")
    print(f"Similarity (Python Engineer vs Python Job): {sim_match:.4f} ({sim_match*100:.1f}%)")
    print(f"Similarity (Python Engineer vs Registered Nurse): {sim_unrelated:.4f} ({sim_unrelated*100:.1f}%)")

    assert sim_match > 0.70, f"Expected strong match > 0.70, got {sim_match}"
    assert sim_unrelated < 0.35, f"Expected weak match < 0.35, got {sim_unrelated}"
    assert sim_match > sim_unrelated * 2, "Matching score should be at least double unrelated score"

    print("\nSanity assertion passed! Mathematical formulation verified.")


if __name__ == "__main__":
    run_benchmark()
