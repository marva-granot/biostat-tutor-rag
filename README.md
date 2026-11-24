# biostat-tutor-rag

A private biostatistics tutor chatbot built with retrieval-augmented generation (RAG): it retrieves passages from course PDFs, answers from them, and cites file and page.

> **Course material is private.** The PDFs this tool was built and evaluated on are not mine to share and are not in this repository. Anything under `data/`, `index/` and `eval/private/` is git-ignored. The repository can be run end to end on the open-licensed documents in `sample_docs/`.

## Status

Work in progress. Sections marked _TBD_ are filled in as each part is built.

## How it works

_TBD: architecture diagram and one paragraph per stage (ingestion, retrieval, answering)._

## Setup

_TBD: Python version, pinned dependencies, `.env` variables._

Enable the repository's privacy checks once per clone:

```sh
git config core.hooksPath .githooks
```

They block commits and pushes that include PDFs, `.pptx` files, `data/`, `index/`, `eval/private/` or `.env`.

## Run on the sample documents

Ingestion turns page transcriptions into chunks, embeds them, and stores the vector index. Run from the repository root with the virtual environment active and `requirements.txt` installed. The first embedding run downloads `BAAI/bge-small-en-v1.5` from Hugging Face (about 130 MB); after that it runs offline on the CPU.

```sh
# 1. Chunks: one per page, long pages split; writes one JSON record per chunk.
python -I scripts/chunk_pages.py sample_docs sample_docs data/sample/chunks.jsonl

# 2. Embeddings and index: writes index/sample/embeddings.npy and chunk_ids.json.
#    Vectors are cached, so running it again makes no embedding calls.
python -I scripts/embed_chunks.py data/sample/chunks.jsonl index/sample data/sample/embed_cache.npz

# Optional: compare transcriptions with the PDF text layer and list pages to spot-check.
python -I scripts/check_transcripts.py sample_docs sample_docs
```

Expected output: 5 chunks from 3 pages; the first embedding run embeds 5 texts, a second run embeds 0.

Arguments are `RAW_DIR TRANSCRIPTS_DIR OUT` for `chunk_pages.py` and `CHUNKS INDEX_DIR CACHE` for `embed_chunks.py`. For other documents, `RAW_DIR` holds the PDFs (a PDF in a `Lectures/` or `Recitations/` folder gets that kind), and `TRANSCRIPTS_DIR` holds one `<pdf stem>_p<NN>.md` file per page, written by transcribing each page image (see Known limitations).

Search the index: prints the 5 best pages with file, page, cosine score and text. Pieces of one page, and slides repeated word for word, count as one result.

```sh
python -I scripts/retrieve.py ask "Why is the denominator of the sample variance N - 1?" --chunks data/sample/chunks.jsonl --index index/sample
```

`retrieve.py check QUESTIONS_JSON` prints the top 5 for a list of questions for a hand check. The search refuses an index that was built from different chunks; re-run `embed_chunks.py` after re-chunking.

_TBD: answering a question._

## Evaluation

_TBD: retrieval hit@k, citation correctness and out-of-scope behaviour, with the question format in `eval/template.json`. The real questions are private._

## Experiments

_TBD: see `EXPERIMENTS.md`._

## Known limitations

- Pages are transcribed from page images into Markdown with LaTeX formulas, not read from the PDF text layer, because the text layer flattens fractions, drops roots and accents, and misses formulas pasted as pictures. Transcription is a manual step in a Claude Code session, so new course pages are not picked up automatically. `scripts/check_transcripts.py` flags pages whose words disagree with the text layer for a spot check.
- Hebrew text is omitted and replaced by `[Hebrew omitted]`; only English content is indexed and answered. No page is skipped as a whole.
- Pictures and plots are not transcribed, except tables of numbers or formulas and English course content shown as a picture (such as screenshots of exam questions). Information that appears only inside a plot cannot be retrieved.

## Lessons learned

_TBD._
