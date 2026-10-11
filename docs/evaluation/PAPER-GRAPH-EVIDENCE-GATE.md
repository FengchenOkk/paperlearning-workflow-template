# Dual-paper source quality gate — protocol v1

Frozen 2026-10-05 before extracting gold or tuning the two-paper pipeline. Corpus: supplied integrated-photonics paper (A) and semiconductor-contact paper (B). Both run identical production parser, extractor, storage, contracts and graph. No titles, authors, domain concept lists or gold are inputs to extraction. Originals remain at user-selected local paths; no evaluation-fixture copies or Git PDF commits.

## Measurement and fixed acceptance criteria

Each paper must pass separately. Small independently source-checked gold items cover problem, methods, claims/results, explicit definitions/assumptions where present, caption/text channels and selected quantities; numbered equations are included only where actually present. Freeze annotations before running extraction scoring. Report missing statements/types rather than substituting general background. Scores apply only to this stated sample.

| Metric | Measurement | Pass | Failure |
| --- | --- | --- | --- |
| Entity precision | Independently adjudicated predictions in preselected source windows; correct identity/type divided by all scientific predictions in those windows | ≥90% | Unreviewed predictions are not counted correct |
| Entity recall | Gold scientific statements with a same-type, source-faithful production node divided by all extraction-target gold statements | ≥80% | Missing or wrong-type statements count as misses |
| Type accuracy | Correct type for matched gold statements / all matched statements, including wrong-type matches | ≥90% | Source-span-only search does not count as entity extraction |
| Anchor correctness | Matched anchor has correct source hash, page, block, exact offsets/text and bbox | 100% | Guessed/coincident locations fail |
| Page correctness | Matched gold objects resolve to visually checked PDF page | 100% | Any wrong page fails |
| Figure-caption association | Selected caption gold has correctly numbered first-class Figure and exact caption block | 100% | Caption and nearby body text cannot be conflated |
| Equation localization | All selected real numbered-equation gold resolves to first-class Equation, correct number and source block | 100%, or explicitly N/A | Missing/split equation, invented normalization or number fails |
| Quantitative integrity | Selected value, sign/exponent/prefix, unit and semantic context agree with rendered PDF | 100% | A matching bare numeric token is insufficient |
| Provenance coverage | Every paper-derived scientific node/edge passes source validation | 100% | Missing/hash-invalid evidence fails |
| Graph integrity | Production integrity report, subtype/source agreement and reviewed prediction audit | Zero unresolved ERRORs | Warnings counted/described; no silent merging |
| Browser journey | Both papers: graph, inspector/type/status, evidence/page/highlight, reverse link, refresh | All steps pass | API success alone is insufficient |

## Zero tolerance

Fabricated paper statements/equations/values/locations, visual inference presented as paper fact, similarity-only accepted semantic edges, invalid VERIFIED objects, gold leakage or paper-specific runtime branches automatically fail. Count unsupported semantic edges, fabricated facts, unanchored statements, duplicate candidates and incorrect merges separately. An empty semantic edge set passes provenance safety, not scientific reasoning.

## Reviews and limitations

Source attribution is distinct from scientific validity. Gold drafted and visually checked by the current Codex model is labeled MODEL_SOURCE_REVIEW, not human verification or independent scientific acceptance. A real human must explicitly review the prepared source/quantity bundle before the reviewed Gate A is PASS. No human names, acceptances or scientific judgments are generated on their behalf. Without that review, the overall reviewed gate is FAIL even if measured engineering criteria pass; report the automatic results separately.

This human-review condition was chosen in this frozen protocol to establish review independence. PaperTest §33 explicitly requires distinguishing machine and human review; it does not itself state that every source gate must wait for a human. We retain the stronger condition selected before tuning, and describe it as this protocol's criterion rather than as a permission restriction imposed by the document. Model source measurements can be reported without human acceptance; no additional operation permission is needed for local implementation/testing.

Gold stores document hash, type, exact wording/normalized representation, page/block/bbox, section if resolvable, equation/figure number, numbers/units/context, expected epistemic status and review origin. Exact formula glyph transcription cannot be established from extracted text alone. Unresolved numeric/glyph ambiguity fails that gold item. Text-block localization does not claim figure-image or glyph-level precision.

Keep baseline and corrected measurements. Do not change thresholds or remove difficult items to obtain PASS. Full-document precision/recall, independent scientific validity, table structure and supplementary materials are outside this small-source-sample gate. Gate B may begin only after both reviewed Gate A results pass.

## Human source review and reevaluation — 2026-10-11

The frozen v1 definitions, thresholds and gold sets above are unchanged. Both human source reviews are now COMPLETE: A 17/17 gold items and 19/19 predictions; B 16/16 gold items and 18/18 predictions, with 21 quantities, six selected captions, one real numbered equation and two separately documented parser anomalies. Decisions are attributable user responses, stored in the [human source audit ledger](../../evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json), not written into frozen model adjudication or application scientific-verification records.

The unchanged production evaluator was rerun locally for both PDFs in isolated databases. The [reevaluation manifest](../../evals/reports/dual-paper/human-reviewed-20261011-r2/manifest.json) records input/report hashes, unchanged thresholds and separate production-model measurements versus the human source audit. Current source hash/version snapshots were checked read-only. Browser results retain their historical 2026-10-05 PASS status and were not rerun for these evaluation/documentation changes.

**A: FAIL. B: FAIL.** A's independent-object REJECT and METHOD-type objection cap identity/type precision at 17/19 (89.47%), below 90%; its accepted expanded fabrication review draft is not a production fix. B's overbar/subscript revisions remain unapplied, so the existing unresolved-glyph clause prevents source-fidelity acceptance. Automatic/model comparison percentages remain separate and do not override human corrections. Explanation-only revisions do not become extraction errors or fabricated ACCEPTs. Parser anomalies outside scientific windows do not alter scoring denominators.

All original gold items, model reports and superseded human events are retained. Scientific validity remains NOT_ASSESSED, all application scientific objects remain CANDIDATE, and Gate B / First-Principles work is NOT_STARTED. Generic pipeline corrections require a subsequent user instruction under the active human-review scope.

## Corrected-production reevaluation — 2026-10-11

The frozen v1 metric definitions, thresholds, windows and gold files above are unchanged. The generic v4 production pipeline ran both original PDFs through fresh isolated ordinary upload/worker ingestion. [Current manifest](../../evals/reports/dual-paper/production-corrections-20261011-r2/manifest.json) records separate unchanged model-key comparisons and current snapshot reconciliation.

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

Five A prediction keys and one B key are unreviewed under the unchanged frozen model adjudication and count incorrect. These model comparison metrics do not establish current human precision. A's rejected background target stays a frozen recall miss. Current audit records A 14 stale source comparisons, three comparisons requiring current binding, four new keys; B 17 stale comparisons and one new key. These counts are reconciliation statuses, not an all-ACCEPT requirement. Old decisions remain intact.

A retains two uncertain shifted-glyph blocks on page 7, outside matched frozen gold. B equation 1 is localized but short mathematical rules/fraction/root layout remain uncertain: automatic algebra/LaTeX reconstruction is not claimed. Current source review/binding is missing; A also fails the frozen model precision threshold. Report the unknowns rather than fabricating notation or acceptance. Stop before Gate B.

The original human ledger was not modified. New audit snapshots bind current IDs, versions, source hashes and the application's evidence fingerprints; no ACCEPT or scientific VERIFIED record is created. The real public-PDF browser journey and both supplied-PDF journeys passed. Input/source hashes, old decisions and thresholds remain preserved. Gate B stays NOT_STARTED.

## Technical equivalence proposals — 2026-10-11 (not yet adopted)

The frozen v1 metric definitions, thresholds, windows, gold and independent-human condition remain unchanged. [Current proposals](../../evals/reports/dual-paper/reconciliation-20261011-r4/README.md) prove old/new source identity and literal wording, type, values/units/qualifiers and exact localization. Whole-block added typography is no longer treated as a scientific content change by default. Thirty-five current prediction statements are metadata-equivalent, one changes scientific type and three are new. All original REVISE/REJECT and limited draft/view acceptances retain their original scope.

No existing rule silently authorizes transferring ACCEPT to new IDs/fingerprints. E0 is a finite auditable binding proposal requiring explicit user confirmation; it is not an adopted policy or an application verification record. Seven unresolved objects are presented in six localized review cards. Source-equivalence proof alone does not accept a new display, scientific type, compilation, mathematical reconstruction or scientific validity. Current human decisions remain null until received.

Frozen model-key comparisons remain A16/21 and B17/18 precision, while current human precision is uncomputed. A rejected background stays a frozen recall miss. Future source adjudication may bind the current keys under the same definition using real human decisions; immutable old model/human records are not rewritten. Equation1 root/fraction interpretation stays uncertain, and no invented normalization or scientific VERIFIED may be used to pass the gate. Current reviewed Gate A A/B FAIL; Gate B NOT_STARTED.
