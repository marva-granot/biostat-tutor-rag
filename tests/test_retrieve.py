import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from embed_chunks import build_index  # noqa: E402
from retrieve import (  # noqa: E402
    QUERY_PREFIX,
    StaleIndexError,
    is_expected,
    load_index,
    search,
)

VOCAB = ["mean", "variance", "bootstrap", "anova", "slide"]


class KeywordEncoder:
    """Fake model: a vector of keyword counts, so the best match is known in advance."""

    def __init__(self):
        self.seen = []

    def __call__(self, texts):
        self.seen.extend(texts)
        out = []
        for t in texts:
            words = t.lower().split()
            v = np.array([words.count(w) for w in VOCAB], dtype=np.float32) + 0.01
            out.append(v / np.linalg.norm(v))
        return np.stack(out)


def record(i, text, page=None):
    return {
        "chunk_id": f"N_p{page or i:02d}_c0",
        "source_file": "N.pdf",
        "page": page or i,
        "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


TEXTS = [
    "mean mean of a sample",
    "variance variance variance estimator",
    "bootstrap bootstrap resampling with mean",
    "anova anova compares groups",
    "variance and mean together",
]


def tiny_index(texts=TEXTS):
    records = [record(i + 1, t) for i, t in enumerate(texts)]
    enc = KeywordEncoder()
    matrix = enc([r["text"] for r in records])
    return records, matrix


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.records, self.matrix = tiny_index()

    def test_known_best_chunk_comes_first(self):
        hits = search("what is a bootstrap", self.records, self.matrix, KeywordEncoder())
        self.assertEqual(hits[0]["page"], 3)
        hits = search("anova", self.records, self.matrix, KeywordEncoder())
        self.assertEqual(hits[0]["page"], 4)

    def test_k_is_respected(self):
        for k in (1, 3, 5):
            hits = search("variance", self.records, self.matrix, KeywordEncoder(), k=k)
            self.assertEqual(len(hits), k)

    def test_results_are_sorted_by_score(self):
        hits = search("variance mean", self.records, self.matrix, KeywordEncoder())
        scores = [h["score"] for h in hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_results_carry_file_page_and_text(self):
        hit = search("mean", self.records, self.matrix, KeywordEncoder(), k=1)[0]
        self.assertEqual(set(hit) - {"also", "pieces"},
                         {"chunk_id", "source_file", "page", "score", "text"})

    def test_pieces_of_one_page_are_merged_into_one_result(self):
        records = [record(1, t) for t in TEXTS]
        for i, r in enumerate(records):
            r["chunk_id"] = f"N_p01_c{i}"
        records.append(record(2, "anova groups"))
        matrix = KeywordEncoder()([r["text"] for r in records])
        hits = search("variance anova", records, matrix, KeywordEncoder(), k=2)
        # Five pieces of page 1 take one slot, so page 2 still fits in k=2.
        self.assertEqual(sorted(h["page"] for h in hits), [1, 2])
        page1 = next(h for h in hits if h["page"] == 1)
        self.assertEqual(len(page1["pieces"]), len(TEXTS) - 1)
        self.assertNotIn(page1["chunk_id"], page1["pieces"])

    def test_question_gets_the_prefix(self):
        enc = KeywordEncoder()
        search("anova", self.records, self.matrix, enc)
        self.assertEqual(enc.seen, [QUERY_PREFIX + "anova"])

    def test_repeated_slides_are_merged_into_one_result(self):
        texts = ["slide slide repeated"] * 3 + TEXTS
        records = [record(i + 1, t) for i, t in enumerate(texts)]
        matrix = KeywordEncoder()([r["text"] for r in records])
        hits = search("slide", records, matrix, KeywordEncoder(), k=3)
        self.assertEqual(len(hits), 3)
        self.assertEqual(hits[0]["page"], 1)
        self.assertEqual([a["page"] for a in hits[0]["also"]], [2, 3])
        self.assertEqual(len({h["text"] for h in hits}), 3)


class LoadIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.chunks, self.index = d / "chunks.jsonl", d / "index"
        self.write(TEXTS)
        build_index(self.chunks, self.index, d / "cache.npz", KeywordEncoder())

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, texts):
        with open(self.chunks, "w", encoding="utf-8") as f:
            for i, t in enumerate(texts):
                f.write(json.dumps(record(i + 1, t)) + "\n")

    def test_index_loads_and_searches(self):
        records, matrix = load_index(self.chunks, self.index)
        self.assertEqual(matrix.shape, (len(TEXTS), len(VOCAB)))
        self.assertEqual(search("anova", records, matrix, KeywordEncoder())[0]["page"], 4)

    def test_stale_index_is_refused(self):
        self.write(TEXTS + ["a new chunk added after embedding"])
        with self.assertRaises(StaleIndexError):
            load_index(self.chunks, self.index)


class ExpectedTest(unittest.TestCase):
    def test_expected_page_matches_main_or_merged_page(self):
        hit = {"source_file": "N.pdf", "page": 16, "also": [{"source_file": "N.pdf", "page": 18}]}
        self.assertTrue(is_expected(hit, [{"file": "N.pdf", "pages": [18]}]))
        self.assertFalse(is_expected(hit, [{"file": "N.pdf", "pages": [17]}]))
        self.assertFalse(is_expected(hit, [{"file": "M.pdf", "pages": [16]}]))


if __name__ == "__main__":
    unittest.main()
