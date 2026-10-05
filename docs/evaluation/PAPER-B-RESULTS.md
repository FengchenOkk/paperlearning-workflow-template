# Paper B source-quality results

2026-10-05. **Reviewed Gate A: FAIL — human source review pending.** Automated checks and model-reviewed sampled measurements satisfy the frozen thresholds. Scientific validity remains NOT_ASSESSED.

Supplied Li et al. semiconductor-contact article: 19 pages including extended data; SHA-256 `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`. Frozen gold: 16 selected statements/source objects, 11 quantity occurrences, figures 1–3 and real equation 1.

| Measure | Baseline | Current | Fixed threshold |
| --- | --- | --- | --- |
| Scientific prediction precision in windows | N/A: zero predictions | 18/18 (100%, model source adjudication) | ≥90% |
| Same-type gold recall | 0/16 (0%) | 16/16 (100%) | ≥80% |
| Matched type accuracy | N/A: no matches | 16/16 | ≥90% |
| Matched anchor/page correctness | N/A: no matches | 16/16 | 100% |
| Selected figure-caption association | 0/3 | 3/3: figures 1, 2 on page 2; figure 3 on page 3 | 100% |
| Equation localization/number | 0/1 | 1/1: equation 1, page 1 | 100% |
| Selected numerical integrity | 0/11 | 11/11 | 100% |
| All-node provenance | 41/41 | 60/60 | 100% |
| All-edge provenance | Structural source edges only | 59/59 | 100% |
| Integrity ERRORs / duplicate warnings | No ERRORs | 0 / 7 | Zero ERRORs |
| Real browser journey | Not previously tested with this PDF | PASS | All required steps |

The baseline fragmented equation 1 into three overlapping blocks and omitted right-column caption continuations. Generic spatial grouping now retains the observed fragments in one TEXT_BLOCK anchor, with correct equation number and original-PDF location. It does not reconstruct the square-root/fraction layout: automatic LaTeX, mathematical meaning and derivation remain null. Gold's visual transcription is a model review aid, not production graph input.

A later full-graph inspection caught three false EQUATION candidates in extended-data captions: a leading-zero crystal index at a line end had been mistaken for an equation label. Shared caption/number syntax now recognizes extended/supplementary figure labels and rejects those indices. The final graph contains 15 Figure candidates and exactly one Equation candidate. This defect was fixed before the reported final gate; the earlier local runtime is preserved as a diagnostic backup, not an accepted result.

Superscripts now preserve the distinction between `10⁸` and `108`, and signs/exponents in computational parameters. Both an explicitly stated ballistic assumption and the caption's TLM assumption/uncertainty have separate candidates. Selected numerical contexts include contact resistance/stability, transistor performance, average contact comparison and computational convergence; no scientific acceptance is recorded.

Seven duplicate warnings concern repeated source SECTION text “Article”, not merged scientific statements. The title still includes the frontmatter “Article”; heading/title parsing remains heuristic. Figure text extraction does not faithfully reconstruct crystallographic overbars/subscript typography. Read the actual PDF for those symbols; no contact-plane interpretation is verified.

Chromium checked the page-1 result and equation plus all three selected captions, actual original page pixels/highlights, visible type/status, reverse selection, refresh and multi-term source search. No semantic edges, accepted similarity edges, fabricated source quotations, unanchored scientific nodes or VERIFIED objects were produced. Incorrect merges: zero; automatic merging is absent. Scientific truth, full-document and extended-data extraction quality, all formula glyphs and figure-image claims are unassessed.

Evidence: [baseline](../../evals/reports/dual-paper/baseline-b.json), [current measurements](../../evals/reports/dual-paper/current-b.json), [browser assertions](../../evals/reports/dual-paper/browser.json), [human review bundle](../../evals/gold/paper-b/REVIEW.md).
