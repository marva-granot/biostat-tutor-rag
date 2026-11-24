# Source of the sample material

`Lane - Degrees of Freedom.pdf` is an extract of pages 330–332 (section "Degrees of Freedom", chapter 10 "Estimation") of:

> Online Statistics Education: A Multimedia Course of Study (http://onlinestatbook.com/). Project Leader: David M. Lane, Rice University.

- Book site: https://onlinestatbook.com/
- Full PDF: https://onlinestatbook.com/Online_Statistics_Education.pdf

**License:** the book site states "This work is in the public domain. Therefore, it can be copied and reproduced without limitation," and asks for the citation above.

## Files

| file | book page |
|---|---|
| `Lane - Degrees of Freedom_p01.md` | 330 |
| `Lane - Degrees of Freedom_p02.md` | 331 |
| `Lane - Degrees of Freedom_p03.md` | 332 |

Each `.md` file is the transcription of one page of the extract, named `<pdf stem>_p<NN>.md` like the course pages. The pages are transcribed with the same rules: text copied exactly (typos kept; for example, the source prints `(8-6.5)2` without a superscript on page 2), formulas written as LaTeX, page numbers left out.

Page 3's text layer also contains invisible leftover text ("Degrees of Freedom", "Characteristics of estimators", "Confidence Interval for the Mean") that is not shown on the page, so `scripts/check_transcripts.py` flags it with low recall even though the transcription is complete.

The material is used for unit tests and public examples only. It is not part of the tutor's knowledge.
