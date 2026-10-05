# Dual-paper generalization and gate decisions

2026-10-05. **Gate A: FAIL. Gate B: FAIL / NOT STARTED because reviewed Gate A has not passed.** All human source-review decisions are pending; the model has not generated a human or scientific acceptance record. No reviewed pilot knowledge paths exist for either paper. None are supplied as if reviewed.

One identical production upload → PyMuPDF → generic candidate extraction → persisted typed objects/canonical graph → validated evidence pipeline processed both supplied PDFs. Runtime code receives no paper titles, domain lists, gold, expected mechanisms or manually prepared graph nodes. The application does not import evaluation scripts/data. Ontology, database model and provenance contract are shared; automatic relations are CONTAINS only. Core architecture was preserved.

Concrete generic repairs: caption formats with spaces or vertical bars; spatially aligned two-column captions; overlapping numbered display-math fragments; source superscript typography; sentence boundaries before caption panel labels; additional explicit scientific statement cues; chart-label/footer heading filtering; local multi-term evidence search with line-wrap/ligature/exponent normalization. Stored source text is not rewritten by search. Phrase matches rank ahead of unordered all-term matches; every hit resolves to validated source evidence. Search makes no semantic-dependence claim and performs no external retrieval.

The model-reviewed sample has A recall 17/17, precision 19/19; B recall 16/16, precision 18/18, selected values/units/context representation 10/10 and 11/11. Six selected captions and one real numbered equation resolve correctly. Both browser journeys and the prior public-PDF regression pass. The frozen thresholds were not reduced and no difficult gold item was removed. Source gold hashes remain unchanged.

Browser visual QA also exposed a page-image transition defect: new-page highlights could briefly overlay the previous page's pixels. Page-keyed images now hide the highlight until the requested original image loads; errors keep evidence overlays hidden. A delayed-load/stale-element frontend regression and the actual refreshed/search journeys validate that boundary. The local preview contains both supplied documents; paper IDs and original content-addressed bytes were preserved. Task-generated unreviewed graphs were rebuilt after the caption fix only after checking that no manual objects or verification records existed, and their diagnostic database was backed up.

These measurements show that the same implementation can handle the chosen source windows in two related subdomains. They do **not** prove general scientific understanding or broad generalization: both papers were used for local diagnosis/tuning, the source gold and judgments were prepared by the implementing model, no blind held-out scientific corpus was adjudicated, and no semantic explanation graph was accepted. A structural star graph cannot establish a mechanism or a first-principles path. Full-document precision/recall and scientific validity are NOT_ASSESSED.

Safety/integrity observations: all 93 current nodes and 91 structural edges have validated source provenance; zero integrity ERRORs; A has zero duplicate warnings, B seven repeated-header warnings with no automatic merge. Zero semantic/accepted-similarity edges, zero unanchored scientific objects and zero VERIFIED objects. Fabricated source statements were not found in the checked source quotes; authors' factual correctness remains unassessed. Equation layout, crystallographic overbars, precise figure-image regions, support assessment and supplementary evidence remain unresolved.

| Graph property | Paper A | Paper B |
| --- | --- | --- |
| Source nodes | PAPER 1; SECTION 2; FIGURE 5; EQUATION 0 | PAPER 1; SECTION 20; FIGURE 15; EQUATION 1 |
| Scientific candidate types | DEFINITION 1; DEVICE 2; LIMITATION 1; METHOD 6; RESEARCH_PROBLEM 2; RESULT 11; SIMULATION 2 | ASSUMPTION 4; DEFINITION 2; LIMITATION 4; METHOD 7; RESEARCH_PROBLEM 1; RESULT 4; SIMULATION 1 |
| Automatic edges | CONTAINS 32 | CONTAINS 59 |
| Parser/job failures; invalid anchors; orphans | 0; 0; 0 | 0; 0; 0 |
| Unresolved duplicates | 0 | Seven repeated source-header warnings |
| Unsupported accepted relations / scientific domain assumptions added | 0 / 0 | 0 / 0 |

[Actual type counts](../../evals/reports/dual-paper/type-counts.json) are projections of the same canonical database schema. Neither paper required a photonics/device-specific parser or a mechanism encoded in the ontology. English sentence and typography heuristics remain generic implementation assumptions; unusual prose, layout and non-English papers can fail. B's extended caption indices initially triggered false equation candidates; the final shared label grammar fixes that case without matching a material, title, author or conclusion.

## Required review and next bounded milestone

Complete attributable **human source review of this frozen dual-paper bundle**: 33 gold items, 37 predictions in the selected windows, 21 quantity occurrences, six captions and one numbered equation. Record actual ACCEPT / REVISE / REJECT decisions against current hashes, with reasons, in the [A](../../evals/gold/paper-a/REVIEW.md) and [B](../../evals/gold/paper-b/REVIEW.md) bundles. Review the original pixels, not only model text. Correct any rejected source/type/glyph item through the generic pipeline and rerun the same fixed gate. This is the single next milestone.

Until both reviewed gates pass, do not start external scientific retrieval, recursive prerequisite expansion or either first-principles pilot. No candidate chains were preloaded to bypass that condition. Once eligible, the two target concepts must still be individually source-grounded and reviewed; scientific-validity acceptance remains separate from this source-quality gate.
