import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_transcripts import score, transcript_words  # noqa: E402

# Text layer as pypdf gives it: plain words, math letters in the Unicode math block (𝜆𝜆).
LAYER = "Given the measurements we compute log \U0001D706\U0001D706 for every sample window"
MD = "Given the measurements we compute $\\log\\lambda$ for every sample window"


class TranscriptWordsTest(unittest.TestCase):
    def test_latex_commands_dropped_but_operators_kept(self):
        full, prose = transcript_words("Then $\\frac{a}{b} + \\log x$ holds")
        self.assertIn("log", full)
        self.assertNotIn("frac", full)
        self.assertEqual(prose, {"then", "holds"})

    def test_markers_are_not_counted(self):
        full, prose = transcript_words("[Hebrew omitted] sample [contact details omitted]")
        self.assertEqual(prose, {"sample"})


class ScoreTest(unittest.TestCase):
    def test_faithful_transcription_scores_one(self):
        self.assertEqual(score(LAYER, MD), (1.0, 1.0))

    def test_skipped_text_lowers_recall(self):
        recall, _ = score(LAYER + " variance estimator", MD)
        self.assertLess(recall, 1.0)

    def test_added_text_lowers_precision(self):
        _, precision = score(LAYER, MD + " invented extra words here")
        self.assertLess(precision, 1.0)

    def test_too_few_words_is_unjudged(self):
        self.assertEqual(score("Title", "# Title"), (None, None))


if __name__ == "__main__":
    unittest.main()
