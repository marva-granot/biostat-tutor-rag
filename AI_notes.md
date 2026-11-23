# AI notes

One line per step: what I asked, what came back, any mistake caught.
This file is the raw log; it becomes AI_USAGE.md at the end of the project.

| Step | What I asked | What came back | Mistake caught |
|------|--------------|----------------|----------------|
| 0 | Create CLAUDE.md from my behavior rules, then PLAN.md and the repo scaffolding. | CLAUDE.md drafted from the rules I pasted. | My first message said the rules were "below" but they were missing; the assistant asked instead of inventing them. The rules named both AI_notes.md and AI_usage.md; I decided on AI_notes.md now and AI_USAGE.md only at the end. The assistant also first wrote the privacy hooks without line-ending rules; I caught that Windows Git would convert them to CRLF and break them, and `.gitattributes` fixed it. PLAN.md drafted with time boxes from my extra instructions. |
| 1 | Inspect the 14 PDFs and verify the claims in my brief. | Page, word, doubled-glyph and near-empty-page table, cross-checked with a second tool; local problem-page list. | Word total differs by tool (19,832 vs 16,988); doubled glyphs are file-specific, not general; Tirgul 4 pages 14–22 are exam images. |
