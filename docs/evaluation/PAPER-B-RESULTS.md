# Paper B source-quality results

## Current technical reconciliation — 2026-10-11

Reviewed Gate A **FAIL**, current source review/binding PENDING, scientific validity NOT_ASSESSED; Gate B NOT_STARTED. See [current report](../../evals/reports/dual-paper/reconciliation-20261011-r4/README.md), [candidate delta](../../evals/reports/dual-paper/reconciliation-20261011-r4/CANDIDATE-DELTA.md) and [targeted review](../../evals/reports/dual-paper/reconciliation-20261011-r4/TARGETED-REVIEW.md). All original gold/thresholds and human decisions are unchanged. Technical equivalence proposals are not human decisions.

B: all18 window scientific statements/types/localizations map to old objects, including SIMULATION after literal DFT heading separation. The two prior notation REVISEs still need current correction confirmation; V_th was originally a model-added check. Original pixels/browser confirm third-digit1 bar and on/th subscripts. Equation1 mathematical reconstruction remains uncertain. Frozen model precision17/18, recall16/16. Fresh graph76/75 provenance100%.

## Production correction update — 2026-10-11

**Paper B reviewed Gate A: FAIL.** Model comparison passes its numeric thresholds, while corrected production lacks current attributable source review/binding. [Audit](../../evals/reports/dual-paper/production-corrections-20261011-r2/paper-b.json) · [Manifest](../../evals/reports/dual-paper/production-corrections-20261011-r2/manifest.json).

| Frozen model comparison / fresh production | A | B |
| --- | --- | --- |
| Prediction precision | 16/21 (76.19%) | 17/18 (94.44%) |
| Same-type recall | 16/17 (94.12%) | 16/16 (100%) |
| Matched type accuracy / anchors / pages | 16/16 each | 16/16 each |
| Selected captions / quantities | 3/3; 10/10 | 3/3; 11/11 |
| Numbered equation localization | N/A | 1/1 |
| All-node / all-edge provenance | 55/55; 54/54 | 74/74; 73/73 |
| Integrity ERRORs / duplicate warnings | 0 / 0 | 0 / 0 |
| Fresh real-PDF browser journey | PASS | PASS |

Rendered original-PDF inspection confirms `Sb(0 1 −1 2)`: the overbar is on the third digit 1, not the fourth digit 2. Generic drawing/glyph geometry yields `(011̅2)` in a separate notation view. Baseline/size observations yield I_on and V_th; the latter remains attributed to model source checking. Raw strings, anchors, signs and quantities are preserved. All eight reviewed template-header instances remain header spans, without SECTION candidates or duplicate warnings. Title and body outline exclude template text.

The DFT statement's text key changed when its subsection heading was separated; it remains unreviewed in the frozen model adjudication. Seventeen other prediction source snapshots have changed typography/heading evidence and require current review. Equation 1 remains localized, with uncertain fraction/root/short-rule layout rather than invented normalization. Its accepted visual review transcription remains historical. Model metrics do not establish current human precision or scientific validity.

Completed checks: 38 backend tests; 8 frontend tests; Ruff lint/format; strict mypy (20 modules); frontend lint/format/types/build; both contract drift checks; isolated Alembic upgrade/check. The real public-PDF Chromium journey and both supplied-PDF source/evidence journeys passed, including original pixels, highlights, reverse selection, refresh, search and B's notation views. These are fresh browser results. Windows sandbox restrictions required elevated local checks; existing workspace Chromium was used without installation or paper transmission.

The canonical DB was consistently backed up, then additively migrated to `35c8d2ea0003`. Every prior row/field and all 77 human-reviewed node/anchor snapshots were preserved. Existing application A/B graphs and v3 jobs were not regenerated. New results describe fresh isolated ordinary uploads; duplicate upload of an existing PDF does not re-extract it. PostgreSQL/container runtime, full-document quality and research-grade understanding remain unassessed.

## Historical state before these corrections

2026-10-11. **Reviewed Gate A: FAIL — human source review COMPLETE; production notation corrections remain unapplied.** The unchanged production evaluator was rerun locally against the frozen PDF, gold and model adjudication. Its sampled comparison metrics still pass; they do not certify the source-fidelity defects identified by the human review. Scientific validity remains NOT_ASSESSED.

Supplied Li et al. semiconductor-contact article: 19 pages including extended data; SHA-256 `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`. Frozen gold: 16 selected statements/source objects, 11 quantity occurrences, figures 1–3 and real equation 1.

| Measure | Baseline | Production rerun / frozen model comparison | Fixed threshold |
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
| Real browser journey | Not previously tested with this PDF | Historical PASS, reported 2026-10-05; not rerun for this review/document update | All required steps |

## Completed human source review

All 16 frozen gold items and all 18 window predictions were reviewed: ACCEPT 16, REVISE 2, REJECT 0. All 11 quantity occurrences, three selected captions and equation 1 have separate ACCEPT records. The 16/18 figure describes explicit production acceptance coverage, not a newly inferred type-accuracy or precision score.

The two explicit production revisions remain unresolved in the extracted objects:

- `b-contact-method`: restore `(011̅2)`, with an overbar on the third digit, instead of `(0112)`. The user's description of its direction is retained as an attributed user note, not scientific-validity acceptance.
- `b-stability`: preserve symbol subscripts, including the user's explicit example I_on (`on` is a subscript). The companion V_th transcription was checked in the PDF and remains labeled model source review.

The frozen protocol states that unresolved numeric/glyph ambiguity fails that gold item. These known source-notation defects therefore prevent reviewed Gate A PASS despite the model's 100% text/number comparison. Original text, explicit corrections and all gold items are preserved; no production parser or application DB fix was applied.

The final parser anomaly received REVISE: the large “Article” label at the upper left is a paper-template header, unrelated to body section structure. Sections must be identified from explicit markers in the article body. Eight SECTION instances on pages 3, 5, 9, 11, 13, 15, 17 and 19 produce seven duplicate warnings. This anomaly is outside the frozen scientific scoring sample and does not change its denominators.

The equation's visual/plain-text review transcription was accepted; automatic algebra/LaTeX reconstruction is still absent. The earlier formula-display feedback is recorded separately from scientific-object decisions. At the user's request, the complete Methods section has a separate [30-step source-anchored inventory](../../evals/reviews/dual-paper/PAPER-B-METHODS-SUMMARY.md). That model-origin draft is not additional frozen gold, a completed production extraction or a human acceptance of all methods.

The baseline fragmented equation 1 into three overlapping blocks and omitted right-column caption continuations. Generic spatial grouping now retains the observed fragments in one TEXT_BLOCK anchor, with correct equation number and original-PDF location. It does not reconstruct the square-root/fraction layout: automatic LaTeX, mathematical meaning and derivation remain null. Gold's visual transcription is a model review aid, not production graph input.

A later full-graph inspection caught three false EQUATION candidates in extended-data captions: a leading-zero crystal index at a line end had been mistaken for an equation label. Shared caption/number syntax now recognizes extended/supplementary figure labels and rejects those indices. The final graph contains 15 Figure candidates and exactly one Equation candidate. This defect was fixed before the reported final gate; the earlier local runtime is preserved as a diagnostic backup, not an accepted result.

Superscripts now preserve the distinction between `10⁸` and `108`, and signs/exponents in computational parameters. Both an explicitly stated ballistic assumption and the caption's TLM assumption/uncertainty have separate candidates. Selected numerical contexts include contact resistance/stability, transistor performance, average contact comparison and computational convergence; no scientific acceptance is recorded.

Seven duplicate warnings concern repeated source SECTION text “Article”, not merged scientific statements. The human review explicitly identifies this text as a template header; it should not determine body sections. The title still includes the frontmatter “Article”; heading/title parsing remains heuristic. Figure text extraction does not faithfully reconstruct crystallographic overbars/subscript typography. Read the actual PDF for those symbols; no contact-plane interpretation is verified.

The previously reported Chromium journey checked the page-1 result and equation plus all three selected captions, actual original page pixels/highlights, visible type/status, reverse selection, refresh and multi-term source search. It was not rerun on 2026-10-11; the current work changes evaluation records and documentation only. No semantic edges, accepted similarity edges, fabricated source quotations, unanchored scientific nodes or VERIFIED objects were produced. Incorrect merges: zero; automatic merging is absent. Scientific truth, full-document and extended-data extraction quality, all formula glyphs and figure-image claims are unassessed.

Evidence: [baseline](../../evals/reports/dual-paper/baseline-b.json), [original frozen measurements](../../evals/reports/dual-paper/current-b.json), [fresh production measurements](../../evals/reports/dual-paper/human-reviewed-20261011-r2/production-b.json), [human-reviewed reevaluation](../../evals/reports/dual-paper/human-reviewed-20261011-r2/paper-b.json), [attributable human audit ledger](../../evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json), [historical browser assertions](../../evals/reports/dual-paper/browser.json). The original [prepared review bundle](../../evals/gold/paper-b/REVIEW.md) is frozen model review material; its original PENDING labels are not the current human review status.
