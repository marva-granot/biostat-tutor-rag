# Stack

## Choices

| Part | Choice | Why |
|------|--------|-----|
| Embeddings | `BAAI/bge-small-en-v1.5`, run locally on CPU | Built for retrieval; 384-dimension vectors; 512-token input limit fits chunk sizes of a few hundred words. MIT license. [Model card](https://huggingface.co/BAAI/bge-small-en-v1.5) |
| Vector store | NumPy: one array of normalised vectors plus a JSON file of metadata | Nothing extra to install and nothing hidden: search is a dot product. A few hundred chunks need no index. |
| Page text and formulas | Claude reads an image of each page inside the Claude Code session (no API; pages rendered by me, transcriptions saved as one file per page in `data/`) and returns text with formulas as LaTeX; Hebrew content is excluded | The PDF text layer loses fractions, roots and accents. Pages are rendered with `pypdfium2`. `pypdf` is kept to check the transcription against the text layer. |
| Answer LLM | Open: Gemini free tier or Claude Haiku 5.5 | Decided when the answering step is built. |

## Dependencies (pinned in `requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | 2.5.5 | vector search |
| sentence-transformers | 6.3.0 | embeddings (installs PyTorch) |
| google-genai | 3.6.1 | Gemini API client |
| pypdfium2 | 5.15.2 | render PDF pages to images |
| pillow | 13.0.0 | save rendered pages as PNG |
| pypdf | 7.1.1 | read the PDF text layer |

Extraction output differs slightly between `pypdf` versions (about 0.03% of words on the inspected corpus), so the version is pinned.

## Data handling

Course text never enters the repository (`data/`, `index/` and `eval/private/` are git-ignored). Page images are read by Claude inside the Claude Code session, so the Claude account's "Help improve our AI models" setting (Settings, Privacy) governs them. Retrieved excerpts are sent to the answer LLM in Step 5; if that is Gemini on its free tier, Google uses submitted content to improve its products and may have it reviewed under the unpaid terms. [Gemini API terms](https://ai.google.dev/terms)

The API key is read from the `GEMINI_API_KEY` environment variable (see `.env.example`). The SDK also reads `GOOGLE_API_KEY` and prefers it when both are set.

## Costs (estimates, to be replaced by logged token usage)

- Embeddings and search: local, no cost.
- Claude Haiku 5.5: $0.10 per million input tokens and $0.50 per million output tokens for prompts up to 100,000 tokens. [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Gemini 2.5 Flash-Lite: $0.10 input and $0.40 output per million tokens; a free tier exists. [Pricing](https://aistudio.google.com/docs/pricing)
- Image input to Claude costs one token per 28x28-pixel patch. [Vision docs](https://platform.claude.com/docs/en/vision)

## Known limitations

- Pages that are only images (for example exam screenshots) and Hebrew text are not indexed.
- Formula transcription by a vision model can contain errors; it is checked automatically against the text layer and by spot checks.
