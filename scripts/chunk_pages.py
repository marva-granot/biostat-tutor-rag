"""Split page transcriptions into chunks ready for embedding.

Usage:  python -I scripts/chunk_pages.py RAW_DIR TRANSCRIPTS_DIR OUT_JSONL

RAW_DIR holds the PDFs (searched recursively; the folder a PDF sits in gives its
`kind`). TRANSCRIPTS_DIR holds one `<pdf stem>_p<NN>.md` file per page. One JSON
record per chunk is written to OUT_JSONL. Only counts and page ids are printed,
never course text.

Rules:
- one chunk per page; a page whose body is over MAX_BODY_TOKENS is split between
  paragraphs, never inside a `$$...$$` block;
- no overlap: later pieces of a split page repeat the page heading instead;
- every chunk starts with "<Kind>: <pdf stem>" so it names its lecture;
- a page with nothing left once the omission markers are removed gets no chunk.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_MAX_TOKENS = 512
# Below the model limit so the prefix and the repeated heading still fit.
MAX_BODY_TOKENS = 400

KINDS = {"Lectures": "lecture", "Recitations": "recitation"}
PAGE_FILE = re.compile(r"^(?P<stem>.+)_p(?P<page>\d+)\.md$")
MARKERS = re.compile(r"\[(Hebrew|contact details) omitted\]")
PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def paragraphs(text):
    """Blank-line separated blocks, re-joined so a `$$...$$` block is never split."""
    out, open_block = [], False
    for part in PARAGRAPH_BREAK.split(text.strip()):
        if open_block:
            out[-1] += "\n\n" + part
        else:
            out.append(part)
        # An odd number of `$$` leaves a display formula open across the break.
        if part.count("$$") % 2:
            open_block = not open_block
    return [p for p in out if p.strip()]


def pack(units, count_tokens, limit, sep):
    """Greedily join units into groups whose joined text stays within `limit` tokens.

    A unit that alone exceeds the limit becomes its own group; the caller
    decides whether to split it further.
    """
    groups, current = [], []
    for unit in units:
        if current and count_tokens(sep.join(current + [unit])) > limit:
            groups.append(current)
            current = []
        current.append(unit)
    if current:
        groups.append(current)
    return [sep.join(g) for g in groups]


def split_body(body, count_tokens, limit=MAX_BODY_TOKENS):
    """Pieces of at most `limit` tokens, cut between paragraphs.

    A single paragraph over the limit is cut between lines, unless it is a
    formula block; an over-limit line or formula is kept whole and shows up as
    an over-limit chunk in the summary.
    """
    pieces = []
    for piece in pack(paragraphs(body), count_tokens, limit, "\n\n"):
        if count_tokens(piece) > limit and "$$" not in piece and "\n" in piece:
            pieces.extend(pack(piece.split("\n"), count_tokens, limit, "\n"))
        else:
            pieces.append(piece)
    return pieces


def page_heading(body):
    """The first Markdown heading line of a page, or None."""
    for line in body.splitlines():
        if line.startswith("#"):
            return line.strip()
    return None


def chunk_page(body, stem, page, kind, count_tokens, limit=MAX_BODY_TOKENS):
    """Chunk records for one transcribed page (an empty list if it has no content)."""
    if not MARKERS.sub("", body).strip():
        return []
    prefix = f"{kind.capitalize()}: {stem}"
    heading = page_heading(body)
    records = []
    for i, piece in enumerate(split_body(body, count_tokens, limit)):
        parts = [prefix]
        if i > 0 and heading and not piece.startswith(heading):
            parts.append(heading)
        parts.append(piece)
        text = "\n\n".join(parts)
        records.append({
            "chunk_id": f"{stem}_p{page:02d}_c{i}",
            "source_file": f"{stem}.pdf",
            "kind": kind,
            "page": page,
            "piece": i,
            "text": text,
            "n_tokens": count_tokens(text),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
    return records


def kinds_by_stem(raw_dir):
    """Map each PDF stem to its kind, taken from the folder the PDF sits in."""
    return {
        pdf.stem: KINDS.get(pdf.parent.name, "document")
        for pdf in Path(raw_dir).rglob("*.pdf")
    }


def chunk_folder(raw_dir, transcripts_dir, count_tokens, limit=MAX_BODY_TOKENS):
    """All chunk records of a folder, in a fixed order, plus the page ids left empty."""
    kinds = kinds_by_stem(raw_dir)
    records, empty = [], []
    pages = []
    for path in Path(transcripts_dir).glob("*.md"):
        m = PAGE_FILE.match(path.name)
        if m and m["stem"] in kinds:
            pages.append((m["stem"], int(m["page"]), path))
    # Sorted by (stem, page number) so the output never depends on directory order.
    for stem, page, path in sorted(pages):
        body = path.read_text(encoding="utf-8")
        found = chunk_page(body, stem, page, kinds[stem], count_tokens, limit)
        if not found:
            empty.append(f"{stem} p{page}")
        records.extend(found)
    return records, empty


def bge_token_counter():
    """Token counter of the embedding model, including its [CLS] and [SEP] tokens."""
    from sentence_transformers import SentenceTransformer

    tokenizer = SentenceTransformer(MODEL_NAME, device="cpu").tokenizer
    return lambda text: len(tokenizer(text)["input_ids"])


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    raw_dir, transcripts_dir, out = argv[1:]
    records, empty = chunk_folder(raw_dir, transcripts_dir, bge_token_counter())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    split = sorted({(r["source_file"], r["page"]) for r in records if r["piece"] > 0})
    over = [r["chunk_id"] for r in records if r["n_tokens"] > MODEL_MAX_TOKENS]
    print(f"chunks: {len(records)}  pages split: {len(split)}  pages without a chunk: {len(empty)}")
    for page_id in empty:
        print(f"NO CHUNK  {page_id}")
    for chunk_id in over:
        print(f"OVER {MODEL_MAX_TOKENS} TOKENS  {chunk_id}")


if __name__ == "__main__":
    main(sys.argv)
