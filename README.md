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

## Lessons learned

_TBD._
