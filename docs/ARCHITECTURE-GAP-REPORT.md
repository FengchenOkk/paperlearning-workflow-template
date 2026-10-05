# Architecture gap report

2026-10-05. This report separates the first-draft risks from corrections and remaining scientific work. See [audit](CURRENT-IMPLEMENTATION-AUDIT.md), [status](IMPLEMENTATION_STATUS.md) and [validation](VALIDATION.md).

## What is correct and retained?

The local API/worker/relational database architecture, source hashing, real PDF pages/text blocks, durable parsing, candidate extraction, canonical directed graph and graph ↔ original source navigation are useful foundations. All views use the same persisted graph. No second graph, automatic similarity-derived science relation or fixture-specific runtime ontology was found. Legacy research stays separate and intact.

## What was scientifically unsafe?

1. A text-attribution review could be mistaken for validation of a scientific claim or relation. Corrected with SOURCE_ATTRIBUTION / SCIENTIFIC_VALIDITY scopes, a required scientific evidence assessment and reviewed-path constraints.
2. Node labels alone stood in for Claim/Equation/Figure objects. Corrected with first-class persisted subtypes, shared canonical identity and explicit unknown analyses. Caption attribution no longer implies figure interpretation.
3. Source integrity checks were inconsistent between evidence, search and reverse navigation. Corrected with shared anchor and byte-hash validation, genuine block precision and page/bbox checks.
4. PREREQUISITE_OF cycle checking ignored inverse DEPENDS_ON edges and inconsistent review states. Corrected with normalized cycles, current-review fingerprints and endpoint checks.
5. The TypeScript generator could merge incompatible field aliases. Replaced with one compilation and generation-drift checks; strict types now discriminate subtype responses.

No correction establishes scientific validity automatically. A named local human review remains a recorded judgment, not a replicated experiment or independent expert endorsement.

## What remains architecturally weak?

| Gap | Consequence | Next bounded correction |
| --- | --- | --- |
| Provenance arrays are JSON anchor IDs | SQL foreign keys do not cover these associations | Normalize associations when editing/import is added; retain domain/integrity checks now. |
| Ontology/status strings lack full SQL enum checks | Direct SQL can bypass domain contracts | Integrity report detects invalid values; harden migrations before adding other writers. |
| Relation rules cover only basic structural/support/assumption endpoints | A valid shape can still express wrong science | Define relation-specific review criteria and expert gold cases; do not infer truth from shape. |
| Parser heuristics for columns, captions and headings | Misclassification, layout order and missed equations | Compare independently checked sections/captions/equations across varied PDFs. |
| No normalized entity resolution | Repeated source wording may create duplicate candidates | Warn, do not merge; add reviewed identity/alias workflow only with clear evidence. |
| Source anchors have block coordinates only | Formula, glyph and figure image regions may be unavailable | Preserve TEXT_BLOCK precision; add separate validated region anchors through a parser adapter. |
| Scalar equation normalization is nullable without an authoring/review workflow | Representation fidelity is not established | Require normalization-specific provenance/version review before accepting non-null reconstruction. |
| Source interpretation fields exist but no analysis editor/provider writes them | Storage capability is not intelligence | Add one grounded extraction task only after evaluation contracts are ready. |
| API mixes some query composition with routing | Harder to audit all read invariants as the app grows | Continue extracting source/graph queries into domain services when extending those routes. |
| Review identity is local and unauthenticated | Reviewer name is an assertion, unsuitable for shared service | Keep loopback scope; authenticated provenance is a deployment prerequisite. |
| Integrity checks are synchronous and query-heavy | Large graphs may need batched validation | Profile meaningful workloads; no distributed stack is justified yet. |
| SQLite is the only tested database | PostgreSQL/concurrency behavior is not proven | Run migrations and lease/review concurrency checks on PostgreSQL before deployment. |

## What is only a demonstration?

The public-paper browser journey demonstrates real source navigation, not comprehensive understanding. Its small gold set proves selected source statements and locations only. Dropout remains a legitimate golden input; an unrelated gravitational-wave PDF now passes the same pipeline. Neither fixture preloads handcrafted scientific nodes or accepted causal/prerequisite relationships. Test-only synthetic reviews never enter the delivered workspace.

## What is missing?

First-principles reverse prerequisite analysis, verified recursive decomposition and task-relative stopping criteria are **PLANNED**. Argument support strength, causal assessment, innovation lineage, equation derivation, symbol/dimension checking, figure visual inference, reference retrieval and expert evaluation remain missing. Table cell reconstruction, robust scanned-PDF OCR and precise image/formula localization remain missing. Chat, translation, Zotero, reproduction and multi-paper features were deliberately not added during this correction.

## What was removed?

The contract generator's unsafe name-only deduplication, unscoped verified-path eligibility and the navigation jump to an unrelated first anchor. No research originals, user prompt documents, legacy mock/test tooling or current implementation files were discarded wholesale.

## Next smallest meaningful milestone

Complete a **reviewed PAPER → GRAPH → EVIDENCE foundation gate** before starting FIRST PRINCIPLE → PAPER CONTRIBUTION: select a small independent gold set of claims, numbered equations and figure captions from both real PDFs; check actual wording, numbers, units and source precision; assess extraction omissions/misclassification; record source attribution separately from scientific support; and pass integrity inspection with no unresolved errors. No forced VERIFIED scientific result is required to close a source-location gate.

Only then add one evidence-backed prerequisite candidate for one core concept, independently review it and define a task-relative stopping rule. A hand-written chain or source-only review is insufficient to claim a first-principles engine.
