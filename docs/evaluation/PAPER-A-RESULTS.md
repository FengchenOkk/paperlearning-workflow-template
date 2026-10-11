# Paper A source-quality results

## Current technical reconciliation — 2026-10-11

Reviewed Gate A **FAIL**, current source review/binding PENDING, scientific validity NOT_ASSESSED; Gate B NOT_STARTED. See [current report](../../evals/reports/dual-paper/reconciliation-20261011-r4/README.md), [candidate delta](../../evals/reports/dual-paper/reconciliation-20261011-r4/CANDIDATE-DELTA.md) and [targeted review](../../evals/reports/dual-paper/reconciliation-20261011-r4/TARGETED-REVIEW.md). All original gold/thresholds and human decisions are unchanged. Technical equivalence proposals are not human decisions.

A: 17 of 21 window candidates are source/type-equivalent old objects; one type change and three new candidates require current adjudication. A problem heading removal is a key mismatch; rejected background remains a gold miss. Generic v5 PROCESS excerpts exclude unrelated characterization, retain exact continuation and are AI_INTERPRETATION. Frozen model precision16/21, recall16/17. Fresh graph56/55 provenance100%.

## Production correction update — 2026-10-11

**Paper A reviewed Gate A: FAIL.** Current production corrections are implemented; current human source review/binding is required. [Audit](../../evals/reports/dual-paper/production-corrections-20261011-r2/paper-a.json) · [Manifest](../../evals/reports/dual-paper/production-corrections-20261011-r2/manifest.json).

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

A's background limitation was omitted as an independent research object, retaining its raw source and frozen gold miss. Relationship exploration is RELATIONSHIP_ANALYSIS, without a claimed relationship result or semantic edge. Fabrication/transfer coverage now includes passive Methods statements and a four-anchor PROCESS excerpt compilation labeled AI_INTERPRETATION, alongside source-backed DEVICE/Figure objects. The accepted expanded review view was not copied into production. Figure 3 c/d/e remain panel-label source spans; explanation-only decisions are unchanged.

Five A prediction keys and one B key are unreviewed under the unchanged frozen model adjudication and count incorrect. These model comparison metrics do not establish current human precision. A's rejected background target stays a frozen recall miss. Current audit records A 14 stale source comparisons, three comparisons requiring current binding, four new keys; B 17 stale comparisons and one new key. These counts are reconciliation statuses, not an all-ACCEPT requirement. Old decisions remain intact.

A retains two uncertain shifted-glyph blocks on page 7, outside matched frozen gold. B equation 1 is localized but short mathematical rules/fraction/root layout remain uncertain: automatic algebra/LaTeX reconstruction is not claimed. Current source review/binding is missing; A also fails the frozen model precision threshold. Report the unknowns rather than fabricating notation or acceptance. Stop before Gate B.

Completed checks: 38 backend tests; 8 frontend tests; Ruff lint/format; strict mypy (20 modules); frontend lint/format/types/build; both contract drift checks; isolated Alembic upgrade/check. The real public-PDF Chromium journey and both supplied-PDF source/evidence journeys passed, including original pixels, highlights, reverse selection, refresh, search and B's notation views. These are fresh browser results. Windows sandbox restrictions required elevated local checks; existing workspace Chromium was used without installation or paper transmission.

The canonical DB was consistently backed up, then additively migrated to `35c8d2ea0003`. Every prior row/field and all 77 human-reviewed node/anchor snapshots were preserved. Existing application A/B graphs and v3 jobs were not regenerated. New results describe fresh isolated ordinary uploads; duplicate upload of an existing PDF does not re-extract it. PostgreSQL/container runtime, full-document quality and research-grade understanding remain unassessed.

## Historical state before these corrections

2026-10-11. **Reviewed Gate A: FAIL — human source review COMPLETE; production corrections remain unapplied.** The unchanged production evaluator was rerun locally against the frozen PDF, gold and model adjudication. Its sampled comparison metrics still pass; those model judgments remain separate from the completed human audit. Scientific validity is NOT_ASSESSED.

Supplied Guo et al. integrated-photonics main article: 10 pages; SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`. Gold frozen before tuning: 17 statements/source objects in preselected text windows; 10 quantity occurrences, three figure captions. No numbered display equation found in this supplied main article; supplementary material is not assessed.

| Measure | Baseline | Production rerun / frozen model comparison | Fixed threshold |
| --- | --- | --- | --- |
| Scientific prediction precision in windows | 1/2 (50%) | 19/19 (100%, model source adjudication) | ≥90% |
| Same-type gold recall | 1/17 (5.9%) | 17/17 (100%) | ≥80% |
| Matched type accuracy | 1/1 | 17/17 | ≥90% |
| Matched anchor/page correctness | 1/1 | 17/17 | 100% |
| Selected figure-caption association | 0/3 | 3/3: figures 1, 3, 4 on pages 3, 5, 6 | 100% |
| Numbered equation localization | N/A | N/A; no equation invented | 100% or actual N/A |
| Selected numerical integrity | 2/10 | 10/10 | 100% |
| All-node provenance | 42/42 | 33/33 | 100% |
| All-edge provenance | Structural source edges only | 32/32 | 100% |
| Integrity ERRORs / duplicate warnings | No ERRORs | 0 / 0 | Zero ERRORs |
| Real browser journey | Not previously tested with this PDF | Historical PASS, reported 2026-10-05; not rerun for this review/document update | All required steps |

## Completed human source review

All 17 frozen gold items and all 19 window predictions were reviewed. Current review-view outcomes are ACCEPT 15, REVISE 3, REJECT 1. The original production candidates have 14 explicit ACCEPTs, four REVISEs and one REJECT: two REVISEs concern only the Chinese review explanation and are resolved without changing source/type. They are neither invented ACCEPT records nor extraction failures.

Three production corrections remain:

- `a-limitation`: explicit REJECT. The ionic-liquid passage is introductory background, not an independent research object of this paper. The rejected gold item remains in the frozen set and denominator.
- `a-prediction-c935580f9be3`: explicit REVISE. The user identifies relationship analysis exploring Δn, Δk versus carrier density; the original METHOD classification remains in production. Mapping this source role to application ontology is pending.
- `a-fabrication`: the user accepted an expanded, source-anchored device/fabrication **review draft**. That acceptance does not repair the original oxidation-only production output; its REVISE and the accepted draft are both retained.

Even granting correctness to every other prediction, the explicit independent-object rejection and type objection limit source identity/type precision to at most 17/19 (89.47%), below the frozen 90% threshold. No exact human precision or revised type/recall score is manufactured from the review-view counts.

Separate records contain ACCEPT for all 10 quantities and all three selected captions. The numbered-equation channel is explicitly N/A. The Figure 3 `c d e` anomaly received REVISE: these are panel labels, not section headings. It remains outside the frozen scientific scoring windows and does not change their denominators. Only the requested Chinese explanations were corrected for `a-absorption-method` and `a-index-measurement`; Δn_eff and Δk_eff denote changes, with `eff` a subscript.

The original extractor missed captions written as “Fig. 1 [title]” and most passive/procedural sentences, and mislabeled a motivating challenge as RESULT. Corrections recognize generic statement cues and caption syntax, preserve observed superscripts (`4 × 10¹² cm⁻²`), retain individual caption definition sentences, and suppress small chart labels as section headings. All extracted scientific entities remain CANDIDATE, with attribution separated from scientific support.

Heading recognition remains imperfect: one large panel-label block “c d e” still appears as a SECTION candidate. The human review confirms it belongs to Figure 3. It has source provenance but is not a real section. The sampled scientific metrics exclude SECTION/PAPER identity, so this error is reported rather than hidden in a full-document accuracy claim. No extractor or application DB correction was applied during human review.

The previously reported Chromium journey exercised the central result on page 1 and selected figures on pages 3, 5, 6: canonical graph → visible type/status → evidence → original pixels and block highlight → reverse source selection → refresh; multi-term search selected its actual matching result/page. Source localization is TEXT_BLOCK, including union blocks where applicable. This browser journey was not rerun on 2026-10-11; the current work changes evaluation records and documentation only.

No semantic edges, accepted similarity edges, fabricated source quotations, unanchored scientific nodes or VERIFIED objects were produced. Incorrect merges: zero; no merging operation occurs. These counts do not establish whether authors' claims are scientifically correct. Only selected source statements and quantities were adjudicated. Full-document precision/recall, all figure caption completeness (including figure 5), image interpretation, equation algebra, overbars/subscripts, supplement and independent scientific validity remain unassessed.

Evidence: [baseline](../../evals/reports/dual-paper/baseline-a.json), [original frozen measurements](../../evals/reports/dual-paper/current-a.json), [fresh production measurements](../../evals/reports/dual-paper/human-reviewed-20261011-r2/production-a.json), [human-reviewed reevaluation](../../evals/reports/dual-paper/human-reviewed-20261011-r2/paper-a.json), [attributable human audit ledger](../../evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json), [historical browser assertions](../../evals/reports/dual-paper/browser.json). The original [prepared review bundle](../../evals/gold/paper-a/REVIEW.md) is frozen model review material; its original PENDING labels are not the current human review status.
