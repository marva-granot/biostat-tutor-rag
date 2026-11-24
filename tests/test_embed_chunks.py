import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from embed_chunks import build_index, cache_key, embed_texts, load_cache  # noqa: E402

SAMPLE = ROOT / "sample_docs"


class FakeEncoder:
    """Deterministic stand-in for the model that records every text it is given."""

    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        out = []
        for t in texts:
            v = np.array([len(t), t.count("e") + 1, sum(map(ord, t)) % 97 + 1], dtype=np.float32)
            out.append(v / np.linalg.norm(v))
        return np.stack(out)

    @property
    def n_texts(self):
        return sum(len(c) for c in self.calls)


def write_chunks(path, texts):
    with open(path, "w", encoding="utf-8") as f:
        for i, t in enumerate(texts):
            f.write(json.dumps({"chunk_id": f"N_p{i + 1:02d}_c0", "text": t}) + "\n")


class EmbedTextsTest(unittest.TestCase):
    def test_cached_texts_are_not_sent_again(self):
        enc, cache = FakeEncoder(), {}
        first, n1 = embed_texts(["a b", "c d"], enc, cache)
        second, n2 = embed_texts(["a b", "c d"], enc, cache)
        self.assertEqual((n1, n2), (2, 0))
        self.assertEqual(enc.n_texts, 2)
        np.testing.assert_array_equal(first, second)

    def test_duplicate_texts_are_embedded_once(self):
        enc = FakeEncoder()
        matrix, n = embed_texts(["same", "same"], enc, {})
        self.assertEqual(n, 1)
        np.testing.assert_array_equal(matrix[0], matrix[1])

    def test_key_depends_on_model_name(self):
        self.assertNotEqual(cache_key("x", "model-a"), cache_key("x", "model-b"))


class BuildIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.chunks, self.index, self.cache = d / "chunks.jsonl", d / "index", d / "cache.npz"

    def tearDown(self):
        self.tmp.cleanup()

    def test_second_run_makes_no_embedding_calls(self):
        write_chunks(self.chunks, ["one text", "two text", "three text"])
        enc = FakeEncoder()
        self.assertEqual(build_index(self.chunks, self.index, self.cache, enc), (3, 3))
        first = np.load(self.index / "embeddings.npy")
        self.assertEqual(build_index(self.chunks, self.index, self.cache, enc), (3, 0))
        self.assertEqual(len(enc.calls), 1)
        np.testing.assert_array_equal(first, np.load(self.index / "embeddings.npy"))

    def test_changing_one_chunk_embeds_only_that_chunk(self):
        write_chunks(self.chunks, ["one text", "two text", "three text"])
        enc = FakeEncoder()
        build_index(self.chunks, self.index, self.cache, enc)
        write_chunks(self.chunks, ["one text", "two text, corrected", "three text"])
        self.assertEqual(build_index(self.chunks, self.index, self.cache, enc), (3, 1))
        self.assertEqual(enc.calls[-1], ["two text, corrected"])

    def test_rows_follow_chunk_order_and_ids_are_saved(self):
        texts = ["zeta", "alpha", "mid"]
        write_chunks(self.chunks, texts)
        enc = FakeEncoder()
        build_index(self.chunks, self.index, self.cache, enc)
        matrix = np.load(self.index / "embeddings.npy")
        self.assertEqual(matrix.dtype, np.float32)
        np.testing.assert_allclose(matrix, enc(texts), rtol=1e-6)
        ids = json.loads((self.index / "chunk_ids.json").read_text(encoding="utf-8"))
        self.assertEqual(ids, ["N_p01_c0", "N_p02_c0", "N_p03_c0"])

    def test_cache_survives_on_disk(self):
        write_chunks(self.chunks, ["kept"])
        build_index(self.chunks, self.index, self.cache, FakeEncoder())
        self.assertIn(cache_key("kept"), load_cache(self.cache))


class RealModelTest(unittest.TestCase):
    def test_sample_vectors_have_model_shape_and_unit_length(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        try:
            from chunk_pages import bge_token_counter, chunk_folder
            from embed_chunks import bge_encoder
            count = bge_token_counter()
        except Exception:
            self.skipTest("bge-small-en-v1.5 is not in the local cache")
        records, _ = chunk_folder(SAMPLE, SAMPLE, count)
        encode, usage = bge_encoder()
        matrix, n = embed_texts([r["text"] for r in records], encode, {})
        self.assertEqual(matrix.shape, (len(records), 384))
        np.testing.assert_allclose(np.linalg.norm(matrix, axis=1), 1.0, atol=1e-5)
        self.assertEqual(usage["texts"], n)
        self.assertGreater(usage["tokens"], 0)


if __name__ == "__main__":
    unittest.main()
