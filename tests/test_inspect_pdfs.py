import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_pdfs import measure_text, summarise  # noqa: E402


class MeasureTextTest(unittest.TestCase):
    def test_plain_text_has_no_math_or_garbling(self):
        m = measure_text("The mean of the sample")
        self.assertEqual((m["words"], m["math_chars"], m["doubled_math_chars"], m["garbled_chars"]), (5, 0, 0, 0))

    def test_doubled_math_glyphs_are_counted_in_characters(self):
        # 𝜑𝜑 is one symbol extracted twice; 𝑝 alone is a single, undoubled symbol.
        m = measure_text("\U0001D711\U0001D711 = \U0001D45D")
        self.assertEqual((m["math_chars"], m["doubled_math_chars"]), (3, 2))

    def test_replacement_and_private_use_chars_are_garbled(self):
        self.assertEqual(measure_text("a�bc(cid:12)")["garbled_chars"], 3)

    def test_hebrew_is_counted(self):
        self.assertEqual(measure_text("abc אב")["hebrew_chars"], 2)


class SummariseTest(unittest.TestCase):
    def test_doubled_share_and_near_empty(self):
        pages = [
            dict(measure_text("\U0001D711\U0001D711 x"), images=0, near_empty=False),
            dict(measure_text(""), images=1, near_empty=True),
        ]
        s = summarise(pages)
        self.assertEqual((s["pages"], s["doubled_share"], s["near_empty_pages"], s["image_count"]), (2, 1.0, 1, 1))


if __name__ == "__main__":
    unittest.main()
