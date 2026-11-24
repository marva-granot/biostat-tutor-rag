"""Compare page transcriptions with the PDF text layer and flag pages to spot-check.

Usage:  python -I scripts/check_transcripts.py RAW_DIR TRANSCRIPTS_DIR [THRESHOLD]

Transcriptions are files named `<pdf stem>_p<NN>.md`. For each one, the plain
English words of the transcription are compared with those of the same page's
text layer (pypdf):

- recall:    share of text-layer words found in the transcription (low = text skipped)
- precision: share of transcription prose words found in the text layer (low = text added)

Only page ids and scores are printed, never course text.
"""
import re
import sys
from pathlib import Path

from pypdf import PdfReader

THRESHOLD = 0.9
# Below this many words on either side a ratio is too noisy to judge.
MIN_WORDS = 5

# ASCII words of 3+ letters. pypdf emits math letters from the Unicode
# Mathematical Alphanumeric block, so they never match and drop out by themselves.
WORD = re.compile(r"[a-z]{3,}")
MATH = re.compile(r"\$\$.*?\$\$|\$.*?\$", re.DOTALL)
# Operator names pypdf prints as ordinary letters, so they must survive stripping.
OPERATOR = re.compile(r"\\(log|ln|max|min|arg|exp|Pr|sin|cos)\b")
COMMAND = re.compile(r"\\[A-Za-z]+")
# Placeholders written instead of skipped content; their words are not slide text.
MARKERS = ("[Hebrew omitted]", "[contact details omitted]")
NAME = re.compile(r"^(?P<stem>.+)_p(?P<page>\d+)\.md$")


def words(text):
    return set(WORD.findall(text.lower()))


def transcript_words(md):
    """(all words incl. math with LaTeX commands removed, prose words outside math)."""
    for marker in MARKERS:
        md = md.replace(marker, " ")
    everything = COMMAND.sub(" ", OPERATOR.sub(r" \1 ", md))
    prose = MATH.sub(" ", md)
    return words(everything), words(prose)


def score(layer_text, md):
    """Recall and precision for one page; None where too few words to judge."""
    layer = words(layer_text)
    full, prose = transcript_words(md)
    recall = len(layer & full) / len(layer) if len(layer) >= MIN_WORDS else None
    precision = len(prose & layer) / len(prose) if len(prose) >= MIN_WORDS else None
    return recall, precision


def main(raw_dir, transcripts_dir, threshold=THRESHOLD):
    pdfs = {p.stem: p for p in Path(raw_dir).rglob("*.pdf")}
    readers = {}
    flagged, unchecked, checked = [], [], 0
    for md_path in sorted(Path(transcripts_dir).glob("*.md")):
        m = NAME.match(md_path.name)
        if not m or m["stem"] not in pdfs:
            print(f"skipped (no matching PDF): {md_path.name}")
            continue
        stem, page = m["stem"], int(m["page"])
        reader = readers.setdefault(stem, PdfReader(str(pdfs[stem])))
        layer = reader.pages[page - 1].extract_text() or ""
        recall, precision = score(layer, md_path.read_text(encoding="utf-8"))
        checked += 1
        page_id = f"{stem} p{page}"
        if recall is None and precision is None:
            unchecked.append(page_id)
        elif (recall is not None and recall < threshold) or (precision is not None and precision < threshold):
            flagged.append((page_id, recall, precision))

    fmt = lambda x: "  -  " if x is None else f"{x:.2f}"
    print(f"pages checked: {checked}, flagged: {len(flagged)}, unchecked: {len(unchecked)} (threshold {threshold})")
    for page_id, r, p in flagged:
        print(f"FLAG  recall {fmt(r)}  precision {fmt(p)}  {page_id}")
    for page_id in unchecked:
        print(f"UNCHECKED (too few words)  {page_id}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) == 4 else THRESHOLD)
