# PLAN

Private biostatistics tutor chatbot built with RAG. The goal is that the owner understands every part.

## How to read this plan

- **Time box:** active working time for the owner and Claude together, in minutes, not counting waiting for each other's OK. Step 0 took about 1 h; Steps 1–8 are budgeted at 3 h, so the whole project is about 4 h. The owner agreed to these time boxes; changing them needs the owner's OK.
- **Over-run rule:** if a step passes 150% of its time box, stop and cut scope using the "Cut" line of that step. Do not extend the box silently.
- **Done when:** measurable conditions. A step is not done without evidence from a command that can be re-run.
- **Status values:** `todo`, `in progress`, `awaiting OK`, `done`.
- After every step: tests, a ~10-line report, PLAN.md status update, a line in `AI_notes.md`, a commit and push after approval, then stop.

| Step | Time box | Status |
|------|----------|--------|
| 0. Rules, plan, scaffolding | about 60 min (spent) | done |
| 1. Understand the input | 15 min | done |
| 2. Choose the stack | 10 min | done |
| 3. Ingestion | 40 min + 40 min page transcription (approved extension) | in progress |
| 4. Retrieval | 20 min | todo |
| 5. Answering | 20 min | todo |
| 6. Evaluation | 30 min | todo |
| 7. Improve | 25 min | todo |
| 8. Interface, README, AI_USAGE.md | 20 min | todo |
| **Steps 1–8** | **180 min (3 h)** | |
| **Whole project** | **about 4 h** | |

---

## Step 0 — Rules, plan, scaffolding

- **Goal:** working rules and a plan agreed before any code; a repo that cannot leak course material.
- **We do together:** the rules and the plan (done); you run the git commands.
- **How we test:** privacy hooks block a forced `git add` of a PDF, `.pptx`, `data/`, `index/`, `eval/private/` and `.env` (8 scripted checks passed in a scratch repo; one real check in this repo after the first commit).
- **Done when:** `CLAUDE.md` and `PLAN.md` approved; `.gitignore` (the five listed patterns plus `~$*`, `*.docx`, `.venv/`, `__pycache__/`, `.pytest_cache/`), `README.md` skeleton, `.githooks/`, `scripts/check_no_private_data.sh` and `AI_notes.md` pushed to `marva-granot/biostat-tutor-rag`; the real hook check printed `BLOCKED`.
- **Cut:** none; this step is small.

## Step 1 — Understand the input

- **Goal:** know exactly what is in the 14 PDFs and which pages will cause trouble, before choosing tools.
- **We do together:** the inspection script and a list of the 3–5 topics you expect to ask about most, so we can check coverage by eye. The unzip goes to `data/raw/` only.
- **How we test:** a script prints one table per file: pages, words, characters per page, share of characters that are doubled math glyphs, and the pages with almost no text. The claims in the project brief (text layer present, "01 Introduction.pdf" nearly empty, Tirgul 4 mostly images, 316 pages, ~17k words) are checked against the script output, not assumed.
- **Done when:** the table covers all 14 files; every claim from the brief is marked confirmed or corrected with the number; at least 5 sample pages (including 2 formula-heavy and 1 near-empty) were shown to you; a list of problem pages with a cause for each exists in `data/` (local only).
- **Cut:** report on a subset of 6 files, then extend only if the numbers surprise us.

## Step 2 — Choose the stack together

- **Goal:** a decision on embeddings, vector database, PDF library and LLM API, with costs, made by you.
- **We do together:** the comparison and the decision, with a one-paragraph reason for each choice, for the README. You choose.
- **How we test:** each option is checked against current official docs (linked), installs cleanly in a fresh virtual environment, and a 3-line smoke script runs (embed two sentences, compare them). Cost estimates use the real token and page counts from Step 1 and current published prices (linked).
- **Done when:** 2–3 options per component are presented in one comparison table with a cost estimate and a source link per number; you chose one option per component; the choice and the dependency list (versions pinned) are written down; each chosen dependency passed the smoke script.
- **Cut:** fix the vector DB and PDF library to the simplest option and compare only embeddings and the LLM.

## Step 3 — Ingestion

- **Goal:** turn the PDFs into chunks with file name and page, embeddings, and a stored vector index, with the formula problem handled.
- **We do together:** the chunking function and the metadata schema. Before writing, Claude explains the split rule, size and overlap, and the PDF reader, embedding and storage calls; you approve those choices.
- **How we test:** unit tests on a small open-licensed PDF in `sample_docs/` (source and license linked): every chunk has file name and page, no chunk is empty, chunk ids are stable between runs, the embedding cache is hit on a second run (no re-embedding). On the course PDFs, a local-only check prints page coverage. For formulas: at least two approaches are compared on about 5 formula-heavy pages with before/after text shown to you.
- **Done when:** the formula approach is chosen by you; all pages except an explicit exclusion list are covered by at least one chunk (the exclusion list starts with the exam-image pages Tirgul 4 p14–22 and any Hebrew-only content, which are skipped and documented as a known limitation in the README); the unit tests pass; running ingestion twice gives identical chunk ids and the second run makes 0 embedding calls; index files exist only under `index/` and `data/` (ignored by git); a git status check shows nothing derived staged.
- **Cut:** skip the second formula approach if the first already gives readable text on 4 of the 5 pages, and note the remainder as a known limitation.
- **Deviation (approved):** every page is transcribed from its image (316 pages), which does not fit the 40-minute box; a pilot on one 24-page file took about 3 minutes, and the box was extended by 40 minutes for transcription.

## Step 4 — Retrieval

- **Goal:** a function that takes a question and returns the top 3–5 chunks, verified by hand before any LLM is added.
- **We do together:** the retrieval function (embed the question, search, return chunks with file, page and score) and the ~10 test questions.
- **How we test:** unit tests with a tiny fixed index (known best chunk for a given query; `k` is respected; results are sorted by score). Hand check: for each of ~10 questions, the top 5 chunks are printed with file, page and score, and you judge each as relevant or not.
- **Done when:** unit tests pass; the hand-check table (question, top-5 pages, relevant yes/no) is complete; and a threshold you agree on is met — proposal: at least 7 of 10 questions have a relevant chunk in the top 5. If not, we list the failures and their likely causes, and stop for your decision.
- **Cut:** use 6 questions instead of 10.

## Step 5 — Answering

- **Goal:** a teacher-style answer built only from the retrieved chunks, with file and page citations, and a fixed refusal when the answer is not there.
- **We do together:** the system prompt and the rule for what counts as "not in the course material". Claude explains how the prompt, chunks and question are put together first.
- **How we test:** tests with a stubbed LLM check prompt assembly (chunks and question present, sources labelled). Live checks with a small set of in-scope and out-of-scope questions check three things: citations point to chunks that were actually retrieved; the out-of-scope answer starts with "This isn't in the course material"; any general-knowledge part is labelled as not from the material. The estimated API cost is shown before the first paid call and token use is logged.
- **Done when:** stubbed tests pass; on the live check set, 100% of cited file/page pairs exist in the retrieved chunks, and every out-of-scope question triggers the exact phrase; cost estimate and actual token use are in the report.
- **Cut:** drop the "general knowledge, labelled" branch and only refuse.

## Step 6 — Evaluation

- **Goal:** numbers that say how good retrieval and answering are, on questions you wrote.
- **We do together:** the 15–20 tuning questions with the correct file and page, and the 3–4 out-of-scope questions, kept in `eval/private/`. **You write alone:** a held-out set of 4–5 more questions (including 1 out-of-scope) in `eval/private/heldout/`; Claude does not see them. Claude builds the runner and the format template.
- **How we test:** the runner prints only aggregate numbers for the held-out set. It computes hit@k (k = 1, 3, 5), citation correctness (cited file and page match the expected page or a page that contains the answer) and out-of-scope behaviour (exact refusal phrase). The runner is itself tested on a 3-question fake set with known expected scores.
- **Done when:** runner tests pass; the metrics for all three measures are computed on the tuning set and saved as the baseline (with date, parameters and seed) in `EXPERIMENTS.md`; `eval/template.json` (format only, no real questions) is committed; no real question is in git; the held-out set exists and is not used for any tuning.
- **Cut:** 12 tuning questions instead of 15–20, 2 out-of-scope instead of 3–4, and 3 held-out questions instead of 4–5.

## Step 7 — Improve

- **Goal:** find out which changes help, one at a time, with evidence.
- **We do together:** the hypothesis for each experiment, written before it is run, and the conclusion afterwards.
- **How we test:** each experiment changes exactly one parameter (for example chunk size, k, hybrid search, reranking) with the seed fixed, re-runs the same evaluation and records before/after numbers. Nothing is tuned on hidden test data.
- **Done when:** the held-out set is run once, on the final configuration only, and its numbers are logged next to the tuning-set numbers; at least 2 experiments are logged in `EXPERIMENTS.md` with parameter, hypothesis, before/after for each metric and a keep-or-revert decision; the final configuration reproduces its logged numbers on a re-run.
- **Cut:** stop at 1 experiment, the one with the largest expected effect (for example k or chunk size).

## Step 8 — Interface, README, AI_USAGE.md

- **Goal:** something a recruiter can run on open material, and an honest write-up.
- **We do together:** the README's "lessons learned" and the final text of `AI_USAGE.md`. The `AI_USAGE.md` part starts only after you give clear instructions, and is built from `AI_notes.md`.
- **How we test:** a CLI or Streamlit app (your choice) is run from a fresh clone and a fresh virtual environment on `sample_docs/` following only the README. A scripted check scans the repository for PDFs, derived data and course-specific text.
- **Done when:** the README has architecture, how to run on `sample_docs/`, results and lessons learned, and a note that the course material is private; the fresh-clone run works with the commands in the README; the leak scan finds nothing; `AI_USAGE.md` is written from `AI_notes.md` after your instructions. Optional: a baseline that puts the whole corpus into one prompt, if the time box allows.
- **Cut:** CLI instead of Streamlit; skip the optional baseline.

---

## Open decisions

- Where `sample_docs/` material comes from (an open-licensed biostatistics text with a linked license), needed for the tests in Step 3 and the demo in Step 8. Claude proposes options with license links in Step 3.
