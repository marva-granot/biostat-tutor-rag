"""Embed chunks with a local model, reusing cached vectors, and write the search index.

Usage:  python -I scripts/embed_chunks.py CHUNKS_JSONL INDEX_DIR CACHE_NPZ

Writes INDEX_DIR/embeddings.npy (one normalised float32 row per chunk, in the
order of CHUNKS_JSONL) and INDEX_DIR/chunk_ids.json (the chunk id of each row,
so a search can detect an index that no longer matches the chunks).

The cache maps sha256(model name + text) to a vector. Only texts missing from
it reach the model, so an unchanged second run makes no embedding calls.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"
BATCH_SIZE = 32


def cache_key(text, model_name=MODEL_NAME):
    # The model name is part of the key so another model never reuses these vectors.
    return hashlib.sha256(f"{model_name}\n{text}".encode("utf-8")).hexdigest()


def load_cache(path):
    path = Path(path)
    if not path.exists():
        return {}
    with np.load(path) as data:
        return dict(zip(data["keys"].tolist(), data["vectors"]))


def save_cache(path, cache):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(cache)
    vectors = np.stack([cache[k] for k in keys]).astype(np.float32)
    # Written to a temporary file first so an interrupted run never leaves a broken cache.
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez(tmp, keys=np.array(keys), vectors=vectors)
    os.replace(tmp, path)


def embed_texts(texts, encode, cache, model_name=MODEL_NAME):
    """Vectors for `texts` in order; returns (matrix, number of texts sent to `encode`).

    `encode` takes a list of strings and returns one normalised vector per string.
    New vectors are added to `cache` in place.
    """
    keys = [cache_key(t, model_name) for t in texts]
    missing = sorted({k: t for k, t in zip(keys, texts) if k not in cache}.items())
    if missing:
        vectors = encode([t for _, t in missing])
        for (k, _), v in zip(missing, vectors):
            cache[k] = np.asarray(v, dtype=np.float32)
    return np.stack([cache[k] for k in keys]).astype(np.float32), len(missing)


def read_chunks(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_index(chunks_path, index_dir, cache_path, encode, model_name=MODEL_NAME):
    """Embed all chunks, write the index and cache; returns (rows, newly embedded)."""
    chunks = read_chunks(chunks_path)
    cache = load_cache(cache_path)
    matrix, n_new = embed_texts([c["text"] for c in chunks], encode, cache, model_name)
    if n_new:
        save_cache(cache_path, cache)
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    np.save(index_dir / "embeddings.npy", matrix)
    with open(index_dir / "chunk_ids.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump([c["chunk_id"] for c in chunks], f, ensure_ascii=False, indent=0)
    return len(chunks), n_new


def bge_encoder():
    """Encoder of the local embedding model; also returns a running token count.

    The model is loaded on the first call, so a fully cached run never loads it.
    """
    loaded = {}
    usage = {"texts": 0, "tokens": 0}

    def encode(texts):
        if "model" not in loaded:
            from sentence_transformers import SentenceTransformer
            loaded["model"] = SentenceTransformer(MODEL_NAME, device="cpu")
        model = loaded["model"]
        usage["texts"] += len(texts)
        usage["tokens"] += sum(len(model.tokenizer(t)["input_ids"]) for t in texts)
        # Normalised vectors make the dot product equal to cosine similarity.
        return model.encode(texts, batch_size=BATCH_SIZE, normalize_embeddings=True,
                            convert_to_numpy=True, show_progress_bar=False)

    return encode, usage


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    chunks_path, index_dir, cache_path = argv[1:]
    encode, usage = bge_encoder()
    rows, n_new = build_index(chunks_path, index_dir, cache_path, encode)
    # Reused rows are cache hits or repeats of a text embedded in this same run.
    print(f"rows: {rows}  embedded now: {n_new}  reused: {rows - n_new}  "
          f"tokens sent to the model: {usage['tokens']}")


if __name__ == "__main__":
    main(sys.argv)
