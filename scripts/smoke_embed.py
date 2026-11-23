"""Check that a local embedding model loads, embeds, and ranks a relevant sentence first.

Usage:  python scripts/smoke_embed.py [MODEL_NAME]
Default model: BAAI/bge-small-en-v1.5. The first run downloads the model.
"""
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

model_name = sys.argv[1] if len(sys.argv) > 1 else "BAAI/bge-small-en-v1.5"
model = SentenceTransformer(model_name, device="cpu")

docs = [
    "The maximum likelihood estimator maximises the likelihood of the observed data.",
    "Bootstrapping resamples the data with replacement.",
    "ANOVA compares the means of several groups.",
]
query = "How do I estimate a parameter by maximum likelihood?"

# Normalised vectors make the dot product equal to cosine similarity.
doc_vecs = model.encode(docs, normalize_embeddings=True)
query_vec = model.encode([query], normalize_embeddings=True)
scores = (doc_vecs @ query_vec.T).ravel()

print(f"model={model_name} dim={doc_vecs.shape[1]} scores={np.round(scores, 3).tolist()}")
assert int(np.argmax(scores)) == 0, "the maximum-likelihood sentence should rank first"
print("OK")
