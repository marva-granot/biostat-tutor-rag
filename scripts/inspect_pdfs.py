"""Report how well the text layer of each PDF can be read.

Usage:  python -I scripts/inspect_pdfs.py INPUT_DIR OUTPUT_DIR

Prints one table (one row per PDF) and writes `inspection.json`, with per-page
numbers, into OUTPUT_DIR. OUTPUT_DIR must be git-ignored (e.g. data/), because the
per-page JSON is derived from course material.

The measurements are about the text layer only. A page that is an image has no
text layer, so it shows up as "near-empty" even if it is full of content.
"""
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

# Pages with fewer words than this are flagged: usually a title slide or an image.
NEAR_EMPTY_WORDS = 20

# Mathematical Alphanumeric Symbols block (U+1D400-U+1D7FF), e.g. 𝜑 𝑝 𝑥.
MATH_CHAR = re.compile(r"[\U0001D400-\U0001D7FF]")
# The same math character twice in a row, e.g. 𝜑𝜑: how the doubled glyphs look.
DOUBLED_MATH = re.compile(r"([\U0001D400-\U0001D7FF])\1")
# Characters that signal a broken font mapping (private use area, replacement char).
HEBREW = re.compile(r"[\u0590-\u05FF]")
GARBLED = re.compile(r"[-�]|\(cid:\d+\)")


def measure_text(text):
    """Numbers describing one page of extracted text (pure function, easy to test)."""
    return {
        "words": len(text.split()),
        "chars": len(text),
        "math_chars": len(MATH_CHAR.findall(text)),
        "doubled_math_chars": 2 * len(DOUBLED_MATH.findall(text)),
        "garbled_chars": len(GARBLED.findall(text)),
        "hebrew_chars": len(HEBREW.findall(text)),
    }


def inspect_page(page):
    return {**measure_text(page.extract_text() or ""), "images": len(page.images)}


def inspect_pdf(path):
    reader = PdfReader(str(path))
    pages = [dict(page=i, **inspect_page(p)) for i, p in enumerate(reader.pages, start=1)]
    for p in pages:
        p["near_empty"] = p["words"] < NEAR_EMPTY_WORDS
    return pages


def summarise(pages):
    math = sum(p["math_chars"] for p in pages)
    return {
        "pages": len(pages),
        "words": sum(p["words"] for p in pages),
        "chars_per_page": round(sum(p["chars"] for p in pages) / max(len(pages), 1)),
        "math_chars": math,
        "doubled_share": round(sum(p["doubled_math_chars"] for p in pages) / math, 2) if math else 0.0,
        "garbled_chars": sum(p["garbled_chars"] for p in pages),
        "hebrew_chars": sum(p["hebrew_chars"] for p in pages),
        "near_empty_pages": sum(p["near_empty"] for p in pages),
        "image_count": sum(p["images"] for p in pages),
    }


def main(input_dir, output_dir):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    for path in sorted(input_dir.rglob("*.pdf")):
        report[str(path.relative_to(input_dir))] = inspect_pdf(path)

    header = ("file", "pages", "words", "chars/pg", "math", "doubled", "garbled", "hebrew", "empty", "images")
    print(" | ".join(header))
    totals = {"pages": 0, "words": 0}
    for name, pages in report.items():
        s = summarise(pages)
        totals["pages"] += s["pages"]
        totals["words"] += s["words"]
        print(" | ".join(str(x) for x in (
            name, s["pages"], s["words"], s["chars_per_page"], s["math_chars"],
            s["doubled_share"], s["garbled_chars"], s["hebrew_chars"], s["near_empty_pages"], s["image_count"])))
    print(f"TOTAL pages={totals['pages']} words={totals['words']}")

    (output_dir / "inspection.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
