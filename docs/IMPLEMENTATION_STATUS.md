# Implementation status

Updated: 2026-10-05, after the dual-paper source gate. Branch: `main`; baseline: `dc20102`. Current milestone: reviewed PAPER → GRAPH → EVIDENCE. **Gate A: FAIL (human review pending); Gate B: FAIL / NOT STARTED.** Model-reviewed sample measurements and browser checks pass; scientific validity remains NOT_ASSESSED. The full research-grade product is **not complete**. [Dual-paper results](evaluation/CROSS-DOMAIN-GENERALIZATION.md) · [Audit](CURRENT-IMPLEMENTATION-AUDIT.md) · [Gaps](ARCHITECTURE-GAP-REPORT.md).

## Actual vertical-slice coverage

| Stage | Status | Practical boundary |
| --- | --- | --- |
| Real PDF upload/storage | IMPLEMENTED | Local, bounded, hash-addressed, deduplicated. |
| PDF parser | PARTIAL | Real text/page/block geometry; headings/order heuristic, OCR and verified sections/references absent. |
| Persisted source model | IMPLEMENTED | Pages/spans/anchors; precision is TEXT_BLOCK. |
| Scientific entity extraction | PARTIAL | Generic English rules, candidate-only; measured on 33 frozen source items in two PDFs by the implementing model; human and full-document evaluation pending. |
| Claim / Equation / Figure objects | IMPLEMENTED | Actual DB subtypes/contracts; storage capability is not scientific analysis. |
| Canonical graph persistence/views | IMPLEMENTED | One DB graph, four projections, bounded queries. |
| Scientific graph understanding | PARTIAL | Manual semantic candidates require provenance/review; automatic edges are structural only. |
| Interactive frontend / inspector | IMPLEMENTED | Real Cytoscape, typed objects and actual backend statuses. |
| Evidence / source-anchor navigation | IMPLEMENTED | Shared validation, graph ↔ source links and search. |
| Real PDF location | IMPLEMENTED | Actual page pixels and rotated text-block highlights; exact formula/image regions absent. |
| Scientific integrity checks | IMPLEMENTED | Foundational structural checks; scientific validity stays NOT_ASSESSED. |
| Scientific reasoning / support assessment | NOT IMPLEMENTED | Text matching and confidence cannot establish truth. |
| First-principles learning engine | NOT IMPLEMENTED | PLANNED; no verified recursive expansion/stopping criteria. |

## Implemented

- V0 module audit and documented domain architecture, ontology, provenance, pipeline, UI and evaluation.
- Pydantic domain contracts and generated JSON Schema/TypeScript views.
- Canonical SQLAlchemy persistence and additive Alembic migrations for source/graph/evidence/jobs, scoped reviews and first-class claim/equation/figure subtypes. Populated v1 upgrades preserve original rows/decisions; unscoped old reviews are flagged, not re-signed.
- Content-addressed source storage; bounded PDF uploads, deduplication and source-hash validation.
- Real local PDF parsing with text blocks, pages, bounding boxes, reading order, heuristic headings and multiline title assembly. Observed numeric superscript typography is retained; spatially aligned caption columns/display-equation fragments have union TEXT_BLOCK anchors. Formula algebra and overbars/subscripts are not reconstructed. Small chart labels/footer blocks are excluded from heading heuristics.
- Persistent background jobs with atomic leases, real stage updates, expired-lease recovery and safe failure/retry categories.
- Source-attributed candidate methods, simulations, devices, research problems, assumptions, limitations, definitions, results, claims, numbered equations and figure/table captions. Caption definitions/assumptions/limitations retain separate wording. Automatic relations are structural containment only; confidence is uncalibrated.
- Directed candidate paths and bounded neighborhoods; local node/source search with all-term matching, phrase-first ordering and PDF line-wrap/ligature/superscript normalization; shared ownership/range/geometry/hash checks. Search returns original evidence and does not imply scientific relationships. Normalized PREREQUISITE_OF / inverse DEPENDS_ON cycle rejection includes reactivating disputed edges. Scientific paths require current scientific reviews for every node/edge.
- Separate SOURCE_ATTRIBUTION / SCIENTIFIC_VALIDITY reviews, substantive scientific evidence assessment, optimistic versions, content/anchor/subtype fingerprints and computed current-review state. Stale/unscoped decisions do not appear as current acceptance.
- Read-only integrity report for invalid references/provenance/ontology/subtypes, duplicate/orphan candidates, cycles and inconsistent reviews; ingestion is structurally gated. No automatic scientific referee.
- Single-compilation contract generation and drift checks; distinct subtype/source-span fields cannot be merged by name.
- React/Cytoscape workspace: pan/zoom/fit, selection, neighborhood focus, four database projections, depth limits, keyboard-accessible node navigator, history, search, dark/light themes and responsive/resizable panels.
- Node → evidence → original page/text-block bbox and source → associated entity. Reverse navigation preserves the clicked block; search selects its matched entity. Real pixels are rendered locally with bounded dimensions. Refresh restores selection; restart preserves the graph.
- Windows launcher, Docker/Compose configuration, secret-free CI definitions, public JMLR gold manifest, backend/frontend tests and browser journey.

## Partially implemented

- Scientific extraction is conservative English rules, candidate-only; no validated semantic AI model.
- Source hierarchy has pages/spans and heading candidates; no verified section/reference parser.
- Claim/equation/figure objects have typed storage/read contracts; support strength, symbols/meanings and visual analysis remain unassessed. Unknowns stay empty/null/NOT_ASSESSED. Text blocks cannot become visual-region evidence. Tables remain caption candidates without cells.
- Argument/innovation controls show filtered candidates labeled pending analysis, not reconstructed reasoning/novelty.
- Human review has node/edge audit APIs and node review UI; editing/merge/split and edge review UI remain pending.
- PostgreSQL schema/configuration exists; runtime validation used SQLite. Docker daemon is unavailable on this host.

## Not implemented

Structured AI providers/prompt registry, scholarly retrieval, recursive first-principles expansion, verified learning paths, argument evaluation, innovation lineage, equation derivation, figure intelligence, translation alignment, embeddings/grounded chat, entity resolution, minimap/pinning/viewport virtualization, cross-paper workspace and reproduction automation.

## Validation

- Original workflow: **208 tests passed in the prior implementation pass**; unchanged legacy code was not rerun during this audit.
- Backend: **32 tests passed in the dual-paper pass**, adding real source typography/evidence, scientific search/exponent distinctions, caption/equation grouping, extended-caption versus equation-number safeguards, sentence boundaries and chart/footer classification to the existing typed object, scoped review/path, integrity and populated-v1 migration checks.
- Frontend: **6 tests passed**, including suppression of stale page pixels/highlights while the target page loads; lint/format, strict TypeScript, contract consistency and production build passed.
- Backend Ruff lint/format, strict mypy (19 modules), JSON Schema consistency and Alembic model/schema drift check passed.
- Real Chromium journey passed: upload, worker parsing, persisted candidate graph, inspector, real bbox visible in the PDF viewport, reverse source selection, page navigation, refresh, search, empty learning view, themes and mobile overflow check.
- Desktop dark/light and mobile screenshots inspected. Visual QA corrected title splitting, selected-node zoom and source-panel scrolling. The final desktop image uses a viewport capture.
- Supplied real PDFs both ran the same production pipeline: A model source precision 19/19, recall 17/17, selected quantities 10/10; B precision 18/18, recall 16/16, quantities 11/11. Six selected captions and one numbered equation were localized. Current provenance: 93 nodes and 91 structural edges, zero integrity ERRORs, seven repeated-header warnings in B. Both real-PDF browser journeys passed graph/type/status → evidence/page/highlight → reverse → refresh/search. All human gold reviews remain PENDING; none of these runs generated VERIFIED objects or scientific acceptance.

Reproducible checks and scientific limits: [VALIDATION.md](VALIDATION.md). No paid AI call, private document transmission, research migration, delivered scientific acceptance record or public deployment occurred. Review mutations exist only in isolated tests. The empty local application DB was backed up before additive upgrade.

## Known issues

Rule confidence is uncalibrated. The implementing model authored source gold and adjudication, and tuned using both supplied papers; the measured sample is not blind or independently human-reviewed. Full-document precision/recall and semantic scientific structure remain unassessed. Equation fractions/roots, crystallographic overbars, complete figure-image provenance, all caption continuations and supplement remain unresolved. B's frontmatter “Article” is still included in its heuristic title and repeated section candidates. Search scans one bounded document locally; no scholarly/external search provider exists. Complex column order and non-English extraction need further parsers/fixtures. Authentication, tenancy and hardened parser isolation are pending. PyMuPDF deployment licensing is unresolved. This host's broken npm wrapper and restricted Anaconda DLL access required local environment workarounds.

## Architecture decisions

[ADR-001](adr/001-foundation.md): relational PostgreSQL/SQLite graph, Alembic, parser boundary, React/Vite/Cytoscape, original image reader and durable DB queue. No runtime dependency on V0 tasks/graphs or external AI keys.

## Next milestone

Complete attributable human source review of the frozen dual-paper bundle (33 gold items, 37 window predictions, 21 quantity occurrences, six captions and one numbered equation), with explicit decisions/reasons against current hashes. Fix rejected items generically and rerun the unchanged thresholds. Gate B remains conditional on both reviewed gates passing. The twelve full-product gates remain open until evidenced.
