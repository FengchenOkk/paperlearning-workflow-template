# Paper A source-quality results

2026-10-05. **Reviewed Gate A: FAIL — human source review pending.** Automated checks and model-reviewed sampled measurements satisfy the frozen thresholds. This is not scientific-validity acceptance.

Supplied Guo et al. integrated-photonics main article: 10 pages; SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`. Gold frozen before tuning: 17 statements/source objects in preselected text windows; 10 quantity occurrences, three figure captions. No numbered display equation found in this supplied main article; supplementary material is not assessed.

| Measure | Baseline | Current | Fixed threshold |
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
| Real browser journey | Not previously tested with this PDF | PASS | All required steps |

The original extractor missed captions written as “Fig. 1 [title]” and most passive/procedural sentences, and mislabeled a motivating challenge as RESULT. Corrections recognize generic statement cues and caption syntax, preserve observed superscripts (`4 × 10¹² cm⁻²`), retain individual caption definition sentences, and suppress small chart labels as section headings. All extracted scientific entities remain CANDIDATE, with attribution separated from scientific support.

Heading recognition remains imperfect: one large panel-label block “c d e” still appears as a SECTION candidate. It has source provenance but is not a real section. The sampled scientific metrics exclude SECTION/PAPER identity, so this error is reported rather than hidden in a full-document accuracy claim.

Chromium exercised the central result on page 1 and selected figures on pages 3, 5, 6: canonical graph → visible type/status → evidence → original pixels and block highlight → reverse source selection → refresh; multi-term search selected its actual matching result/page. Source localization is TEXT_BLOCK, including union blocks where applicable.

No semantic edges, accepted similarity edges, fabricated source quotations, unanchored scientific nodes or VERIFIED objects were produced. Incorrect merges: zero; no merging operation occurs. These counts do not establish whether authors' claims are scientifically correct. Only selected source statements and quantities were adjudicated. Full-document precision/recall, all figure caption completeness (including figure 5), image interpretation, equation algebra, overbars/subscripts, supplement and independent scientific validity remain unassessed.

Evidence: [baseline](../../evals/reports/dual-paper/baseline-a.json), [current measurements](../../evals/reports/dual-paper/current-a.json), [browser assertions](../../evals/reports/dual-paper/browser.json), [human review bundle](../../evals/gold/paper-a/REVIEW.md).
