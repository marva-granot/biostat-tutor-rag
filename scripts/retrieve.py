"""Find the chunks that best match a question.

Usage:
  python -I scripts/retrieve.py ask "QUESTION" [-k 5] [--chunks PATH] [--index DIR]
  python -I scripts/retrieve.py check QUESTIONS_JSON [-k 5] [--chunks PATH] [--index DIR]

`ask` prints the top-k chunks for one question. `check` prints the top-k for
every question in a JSON list of {"id", "question", "expected": [{"file",
"pages"}]} records and marks results on an expected page, for a hand check.
Both print course text, so their output stays on this machine.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_chunks import bge_encoder, read_chunks  # noqa: E402

# bge v1.5 model card: for short queries searching longer passages, prefix the
# query (never the passages) with this instruction.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
DEFAULT_K = 5


class StaleIndexError(RuntimeError):
    pass


def load_index(chunks_path, index_dir):
    """Chunk records and their embedding matrix, refusing an index built from other chunks."""
    records = read_chunks(chunks_path)
    index_dir = Path(index_dir)
    ids = json.loads((index_dir / "chunk_ids.json").read_text(encoding="utf-8"))
    matrix = np.load(index_dir / "embeddings.npy")
    if ids != [r["chunk_id"] for r in records] or len(matrix) != len(records):
        raise StaleIndexError(
            f"{index_dir} does not match {chunks_path}; re-run scripts/embed_chunks.py")
    return records, matrix


def search(question, records, matrix, encode, k=DEFAULT_K):
    """The k best pages for `question`, best first.

    Each result is one page, carrying the text of its best-scoring chunk; the
    ids of that page's other chunks are listed under "pieces". Chunks with
    identical text on other pages (a slide repeated in a deck) are merged into
    the first result too, and those pages are listed under "also".
    """
    query = np.asarray(encode([QUERY_PREFIX + question])[0], dtype=np.float32)
    # Rows and query are unit vectors, so the dot product is the cosine similarity.
    scores = matrix @ query
    # A stable sort keeps chunk order on ties, so results never change between runs.
    order = np.argsort(-scores, kind="stable")
    results, by_text, by_page = [], {}, {}
    for i in order:
        r = records[i]
        page = (r["source_file"], r["page"])
        if page in by_page:
            # Another piece of a page that is already a result: no new slot.
            by_page[page]["pieces"].append(r["chunk_id"])
            continue
        if r["text_sha256"] in by_text:
            hit = by_text[r["text_sha256"]]
            hit["also"].append({"source_file": r["source_file"], "page": r["page"]})
            by_page[page] = hit
            continue
        if len(results) == k:
            continue
        hit = {
            "chunk_id": r["chunk_id"],
            "source_file": r["source_file"],
            "page": r["page"],
            "score": float(scores[i]),
            "text": r["text"],
            "pieces": [],
            "also": [],
        }
        by_text[r["text_sha256"]] = hit
        by_page[page] = hit
        results.append(hit)
    return results


def first_line(text):
    """First line after the "<Kind>: <file>" prefix, for compact listings."""
    lines = [line for line in text.split("\n") if line.strip()]
    return (lines[1] if len(lines) > 1 else lines[0])[:70]


def where(hit):
    pages = [hit["page"]] + [a["page"] for a in hit["also"]]
    return f"{Path(hit['source_file']).stem} p{', '.join(map(str, pages))}"


def is_expected(hit, expected):
    places = [(hit["source_file"], hit["page"])] + [(a["source_file"], a["page"]) for a in hit["also"]]
    return any((e["file"], p) in places for e in expected for p in e["pages"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search the chunk index.")
    parser.add_argument("command", choices=["ask", "check"])
    parser.add_argument("target", help="a question (ask) or a questions JSON file (check)")
    parser.add_argument("-k", type=int, default=DEFAULT_K)
    parser.add_argument("--chunks", default="data/chunks.jsonl")
    parser.add_argument("--index", default="index")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    records, matrix = load_index(args.chunks, args.index)
    encode, _ = bge_encoder()

    if args.command == "ask":
        for rank, hit in enumerate(search(args.target, records, matrix, encode, args.k), 1):
            print(f"{rank}. {hit['score']:.3f}  {where(hit)}\n{hit['text']}\n")
        return

    questions = json.loads(Path(args.target).read_text(encoding="utf-8"))
    with_expected = 0
    for q in questions:
        hits = search(q["question"], records, matrix, encode, args.k)
        found = [is_expected(h, q["expected"]) for h in hits]
        with_expected += any(found)
        print(f"\n[{q['id']}] {q['question']}")
        for rank, (hit, ok) in enumerate(zip(hits, found), 1):
            mark = "EXPECTED" if ok else "        "
            print(f"  {rank}. {hit['score']:.3f} {mark} {where(hit)} | {first_line(hit['text'])}")
    print(f"\nquestions with an expected page in the top {args.k}: {with_expected} of {len(questions)}")


if __name__ == "__main__":
    main()
