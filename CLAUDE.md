# CLAUDE.md — working rules for this repo

Project: a private biostatistics tutor chatbot built with RAG. The owner is a student whose goal is to **understand every part**, not just to end up with working code. The repo is public; the course material is not the owner's and must never be published.

## Ground truth
- Never invent facts, library APIs, model names, prices or results.
- For every source you bring, include a link to it.
- Check current docs. Run things to verify.
- If you don't know, say "I don't know".

## Teach mode
- Before writing code for a step, explain what it does and why, in plain words.

## Decisions
- Ask me whenever a decision is ambiguous or has trade-offs. Don't silently choose.
- Explain any idea that isn't in the plan, with its cost, before applying it.
- Report any deviation from the plan.

## Workflow: one step at a time
After each step:
1. Run the tests.
2. Post a short report (about 10 lines): commands run, pass/fail counts, failures with cause and proposed fix, metric change, files added or changed (one line of purpose each), and a verdict.
3. Update the status in PLAN.md.
4. Stop and wait for my OK before the next step.

## Testing
- Every step has a runnable check. No step is "done" without evidence.
- Never tune on hidden test data.

## Git
- Commit after each verified step, using conventional commits.
- Before every commit run `git status` and confirm that no course material or derived data is staged: PDFs, extracted text, chunks, vector index, eval questions.
- Push after each approved step.

## Privacy
- Course content stays local.
- Public docs, screenshots and examples use only open-licensed sample material in `sample_docs/`.
- Secrets live only in `.env`.

## Cost
- Show the estimated API cost before any run that calls a paid API.
- Cache embeddings.
- Log token usage.

## Reproducibility
- Pin dependencies, fix random seeds (fixed seed for determinism), document how to run.
- Keep dependencies minimal; ask before adding one.

## Code and docs style
- Code and docs describe the code, not the chat.
- Comments explain why.
- No "Step 3", "user asked" or other process history in code or the README.

## AI usage log
- Append one line per step to `AI_notes.md`: what I asked, what came back, any mistake caught. The owner turns it into `AI_USAGE.md` at the end.
