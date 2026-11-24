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

_TBD: commands for ingesting `sample_docs/` and asking a question._

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
