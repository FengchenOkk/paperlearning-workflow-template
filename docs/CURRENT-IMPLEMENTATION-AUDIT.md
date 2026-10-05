# Implementation audit and correction

2026-10-05 · branch retained · baseline `118a9d2`. Scope: the first PaperGraph implementation, including backend, frontend, generated contracts, docs, evals and launch/CI configuration. Pre-existing `prompt/` documents were inspected as historical requirements, not executed. Private research, original PDFs, credentials and legacy truth files were preserved.

## Conclusion

The first draft delivered real source navigation and durable candidate data. It did **not** deliver scientific understanding. Passing its 13 backend tests, two frontend tests and browser journey was insufficient evidence for the larger claim. The architecture is retained and corrected in place; no repository reset or research migration was performed.

## Subsystem decisions

| Subsystem | Decision | Reason and actual correction |
| --- | --- | --- |
| Local modular monolith / API + worker | KEEP | Appropriate for one paper; no distributed infrastructure is needed. |
| Content-addressed PDF storage | KEEP | Real SHA-256 validation, atomic writes and deduplication protect identity and reviews. |
| Database canonical graph | KEEP | All four views, paths and neighborhoods query `knowledge_nodes`/`knowledge_edges`. No parallel application graph store exists. |
| JSON Schema / TypeScript export | REPLACE | Independent compilation plus name-only deduplication confused distinct `kind` types. One compilation now resolves names consistently; regeneration checks detect drift. |
| Ontology vocabulary | KEEP | Scientific types and semantic relations are present in runtime enums and contracts, without a discipline-specific concept dictionary. |
| Ontology enforcement | REFACTOR | Added type/layer invariants and basic relation endpoint rules. Comprehensive scientific relation semantics remain incomplete. |
| Persisted source model | KEEP | Pages, exact extracted blocks, order, coordinates and source hashes are genuine parser output. Section/reference hierarchy is still partial. |
| SourceAnchor / provenance | REFACTOR | Checks page ownership, ranges, text, geometry, rotation and hash. Source navigation/search/reverse links now share checks. PDF bytes are checked before source access and reviews. Location precision is explicitly `TEXT_BLOCK`. |
| Parser / rendering | REFACTOR | Image payloads are excluded from text extraction and render dimensions are bounded. Caption recognition precedes heading heuristics. No fake OCR. |
| Entity extraction | REFACTOR | Generic English rules remain candidate generation, not scientific verification. Rules work on an unrelated physics paper through the same pipeline. Precision/recall is unmeasured. |
| Claim | REFACTOR | Added `claims` table keyed by canonical node ID, typed API projection, source anchor, qualifiers and support state. Assumptions/evidence reference canonical edges; `NOT_ASSESSED` does not imply support. Result/conclusion/hypothesis claims use the same subtype. |
| Equation | REFACTOR | Added source expression/number, nullable normalized/LaTeX fields, symbols and separately attributed meanings. Derivations, definitions, uses, assumptions and approximations are graph projections. No derivation engine was invented. |
| Figure | REFACTOR | Added caption anchor/number and separate surrounding-text, visual-observation and AI-interpretation channels. Caption bbox is not an image-region bbox; region remains unknown. |
| Human verification | REFACTOR | Source attribution and scientific validity have distinct scopes. Scientific acceptance requires a separate evidence assessment. Reviews bind source/object version and content fingerprint. Legacy reviews are preserved as unscoped and flagged for reconsideration. |
| Paths / prerequisite checks | REFACTOR | Both prerequisite directions are normalized for cycles. Disputed/rejected/stale endpoints are excluded. Verified paths require current scientific reviews on every node and edge; source attribution alone is insufficient. |
| Graph integrity inspection | REFACTOR | Added read-only integrity report, ingestion gate and negative tests for ownership, ontology, provenance, subtype absence, duplicates/orphans, cycles and inconsistent reviews. It explicitly reports scientific validity as NOT_ASSESSED. |
| Durable jobs / recovery | KEEP | Atomic lease ownership, staged status and transactional graph creation are retained. READY means parser/candidate pipeline success. |
| Central graph / inspector / source UI | REFACTOR | Retained real Cytoscape and original page reader; inspector reads typed objects and scoped status. Reverse navigation preserves the clicked source block; search selects the matched node; late responses are guarded. |
| Argument / innovation views | INCOMPLETE | Filtered views of the canonical graph, visibly pending analysis. They do not reconstruct arguments or establish novelty. |
| First-principles / Learning engine | INCOMPLETE | PLANNED. No reverse prerequisite expansion, stopping rule, verified decomposition or learning evaluation exists. Empty learning projection is intentional. |
| Equation / figure intelligence | INCOMPLETE | First-class storage is implemented; scientific interpretation and expert assessment are not. |
| PostgreSQL / containers | INCOMPLETE | Configuration exists; local runtime/migration verification uses SQLite. Docker daemon is unavailable. |
| Legacy workflows, user prompts and research | KEEP | Isolated, preserved and never imported as application graph state or executed as this task's instructions. |

## Removed behavior

Removed the unsafe generated-type deduplication and the interpretation that any VERIFIED status establishes scientific validity. Removed source-selection behavior that could jump to a node's first anchor instead of the clicked anchor. No user files or historical tooling were deleted. No fabricated scientific demo graph was found to remove.

## One canonical representation

`models.py` owns persistent nodes/edges and scientific subtypes. Subtype PKs are node FKs; status/text live once on the node. Relationship lists in subtype responses are queries over canonical edges, not independent writable lists. Evidence anchor IDs remain JSON references and are validated by the domain layer; this is a remaining storage limitation, not a second graph.

`packages/schemas/domain.schema.json` describes contracts, not scientific data. Frontend graph state comes from API responses. Local storage contains paper/selection IDs and theme only. Markdown architecture documents and gold manifests are documentation/test expectations. No AI responses are used at runtime. Legacy project JSON/Markdown graphs belong to an isolated historical workflow with no implicit synchronization into PaperGraph.

## Lexical content audit

Every matching occurrence in the inspected public/source surface is classified in [content-occurrences.json](audit/content-occurrences.json), with path, line, byte column and line hash. The reproducible scanner is `backend/scripts/audit_content.py`. It excludes credentials, ignored originals, private research, dependencies, runtime/build/cache output and its own inventory. These exclusions protect user data; no claim is made to have audited private research conclusions.

Application runtime matches were inspected directly: `demo` occurs inside the author-wording regex `demonstrate`; `placeholder` is a search input hint. Test fixtures and synthetic invalid assertions are explicitly confined to tests. Historical mock adapters, unfinished templates and vendor examples remain isolated. `prompt/` contains earlier instruction documents, including obsolete architecture constraints; their presence does not authorize actions or constitute runtime analysis. No runtime mock scientific result or hardcoded Dropout entity/relationship was found.

## Test audit

The original tests checked genuine PDF parsing, storage, restart/deduplication, source anchors and browser navigation. Weaknesses were missing typed objects, mixed dependency cycles, scoped review semantics, bad reference/geometry handling across all read endpoints, migration preservation and contract drift.

Added targeted tests cover these gaps, including first-class subtype persistence, original/AI separation, ontology rejection, evidence-channel rejection, source-vs-scientific reviews, current reviewed paths, corrupted anchors across navigation/search, absent subtype, duplicate/orphan candidates, invalid audit references and upgrading a populated v1 database without discarding its records. Two public PDFs pass the same parser/extractor/graph pipeline. The frontend now checks scientific object/status presentation, beyond HTTP success.

Actual results and limits: [VALIDATION.md](VALIDATION.md). Browser canvas rendering and keyboard node selection are exercised; automated coordinate hit testing on arbitrary graph nodes and broad extraction accuracy remain uncovered. Tests prove software invariants, not paper claims.
