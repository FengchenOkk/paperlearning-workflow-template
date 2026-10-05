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
