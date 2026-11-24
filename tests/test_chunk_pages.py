import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from chunk_pages import (  # noqa: E402
    MODEL_MAX_TOKENS,
    chunk_folder,
    chunk_page,
    paragraphs,
)

SAMPLE = ROOT / "sample_docs"
STEM = "Lane - Degrees of Freedom"


def words(text):
    """Stand-in token counter: fast, exact, and needs no model."""
    return len(text.split())


def make_folder(tmp, pages, stem="Notes", folder="Lectures"):
    """A raw dir with one (empty) PDF and a transcripts dir with the given pages."""
    raw = Path(tmp) / "raw" / folder
    raw.mkdir(parents=True)
    (raw / f"{stem}.pdf").write_bytes(b"")
    tr = Path(tmp) / "tr"
    tr.mkdir()
    for page, body in pages.items():
        (tr / f"{stem}_p{page:02d}.md").write_text(body, encoding="utf-8")
    return Path(tmp) / "raw", tr


class SampleFolderTest(unittest.TestCase):
    def setUp(self):
        self.records, self.empty = chunk_folder(SAMPLE, SAMPLE, words, limit=150)

    def test_every_chunk_has_file_page_and_text(self):
        self.assertTrue(self.records)
        for r in self.records:
            self.assertEqual(r["source_file"], f"{STEM}.pdf")
            self.assertIn(r["page"], (1, 2, 3))
            self.assertTrue(r["text"].strip())
        self.assertEqual(self.empty, [])

    def test_every_page_is_covered(self):
        self.assertEqual({r["page"] for r in self.records}, {1, 2, 3})

    def test_ids_are_unique_and_stable_between_runs(self):
        again, _ = chunk_folder(SAMPLE, SAMPLE, words, limit=150)
        ids = [r["chunk_id"] for r in self.records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [r["chunk_id"] for r in again])
        self.assertEqual([r["text_sha256"] for r in self.records],
                         [r["text_sha256"] for r in again])

    def test_every_chunk_starts_with_its_lecture_name(self):
        # The sample PDF sits directly in sample_docs/, not in Lectures/ or Recitations/.
        for r in self.records:
            self.assertEqual(r["kind"], "document")
            self.assertTrue(r["text"].startswith(f"Document: {STEM}\n\n"))

    def test_long_page_is_split_and_later_pieces_repeat_the_heading(self):
        page1 = [r for r in self.records if r["page"] == 1]
        self.assertGreater(len(page1), 1)
        self.assertEqual([r["piece"] for r in page1], list(range(len(page1))))
        for r in page1[1:]:
            self.assertIn("\n\n# Degrees of Freedom\n\n", r["text"])

    def test_short_page_stays_one_chunk(self):
        page3 = [r for r in self.records if r["page"] == 3]
        self.assertEqual(len(page3), 1)
        self.assertEqual(page3[0]["chunk_id"], f"{STEM}_p03_c0")


class ChunkPageTest(unittest.TestCase):
    def test_formula_block_is_never_cut(self):
        body = "Intro words here.\n\n$$a = b\n\nc = d$$\n\nOutro words here."
        self.assertEqual(paragraphs(body),
                         ["Intro words here.", "$$a = b\n\nc = d$$", "Outro words here."])
        records = chunk_page(body, "N", 1, "lecture", words, limit=4)
        self.assertTrue(any("$$a = b\n\nc = d$$" in r["text"] for r in records))

    def test_marker_only_page_gives_no_chunk(self):
        self.assertEqual(chunk_page("[Hebrew omitted]\n\n[contact details omitted]",
                                    "N", 1, "lecture", words), [])

    def test_page_with_content_and_marker_keeps_the_marker(self):
        records = chunk_page("# Title\n\n[Hebrew omitted]\n\nSome text.", "N", 1, "lecture", words)
        self.assertEqual(len(records), 1)
        self.assertIn("[Hebrew omitted]", records[0]["text"])

    def test_kind_comes_from_the_pdf_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, tr = make_folder(tmp, {1: "Text."}, folder="Recitations")
            records, _ = chunk_folder(raw, tr, words)
        self.assertEqual(records[0]["kind"], "recitation")
        self.assertTrue(records[0]["text"].startswith("Recitation: Notes\n\n"))

    def test_pages_are_ordered_by_number_and_empty_pages_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, tr = make_folder(tmp, {10: "Ten.", 2: "Two.", 3: "[Hebrew omitted]"})
            records, empty = chunk_folder(raw, tr, words)
        self.assertEqual([r["page"] for r in records], [2, 10])
        self.assertEqual(empty, ["Notes p3"])

    def test_transcripts_without_a_pdf_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, tr = make_folder(tmp, {1: "Text."})
            (tr / "Other_p01.md").write_text("Stray page.", encoding="utf-8")
            records, _ = chunk_folder(raw, tr, words)
        self.assertEqual({r["source_file"] for r in records}, {"Notes.pdf"})


def load_bge_counter():
    """The real token counter from the locally cached model, or None if unavailable."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        from chunk_pages import bge_token_counter
        return bge_token_counter()
    except Exception:
        return None


class RealTokenizerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        count = load_bge_counter()
        if count is None:
            raise unittest.SkipTest("bge-small-en-v1.5 is not in the local cache")
        # staticmethod: a plain function stored on the class would receive `self`.
        cls.count = staticmethod(count)

    def test_every_sample_chunk_fits_the_model(self):
        records, _ = chunk_folder(SAMPLE, SAMPLE, self.count)
        for r in records:
            self.assertLessEqual(r["n_tokens"], MODEL_MAX_TOKENS, r["chunk_id"])
        # Page 2 is 546 tokens on its own, so it must have been split.
        self.assertGreater(sum(r["page"] == 2 for r in records), 1)


if __name__ == "__main__":
    unittest.main()
