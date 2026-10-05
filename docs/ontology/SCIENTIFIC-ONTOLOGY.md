# Scientific ontology

The typed node and relation vocabulary is defined in `backend/papergraph/ontology.py` and exposed by OpenAPI. It includes source structure, scientific concepts/laws/theories, methods, experiments, claims, evidence, results, contributions and limitations. Relations include structural containment and semantic dependency, derivation, use, support, contradiction, comparison and citation.

Each graph object belongs to SOURCE, SEMANTIC, ARGUMENT, LEARNING or CONTEXT. All four graph views are filtered projections of one graph; empty projections explicitly indicate absent analysis. No generic `related_to` edge is used. Initial extraction emits only containment for source candidates. Semantic scientific relations require evidence and intentional submission; keyword overlap creates no dependency.

Epistemic statuses distinguish PAPER_EXPLICIT, PAPER_IMPLICIT, AUTHOR_CLAIM, OBSERVED_DATA, REFERENCE_DERIVED, BACKGROUND_KNOWLEDGE, AI_INTERPRETATION, AI_DERIVATION, AI_HYPOTHESIS, UNVERIFIED, CONFLICTING, UNKNOWN and NOT_SPECIFIED_IN_PAPER. Verification states: CANDIDATE, SUPPORTED, VERIFIED, DISPUTED, REJECTED, STALE.

Extension procedure: add a vocabulary member, document its semantics/layer, update validation and API schema, migrate affected data if required, regenerate frontend types and add focused evidence tests. Discipline-specific taxonomies may extend the versioned vocabulary; the initial vocabulary is deliberately discipline-neutral.

Audit correction: source types require SOURCE; argument types require ARGUMENT; FIRST_PRINCIPLE permits LEARNING/SEMANTIC and PRIOR_WORK uses CONTEXT. Assumptions/approximations may occur in SEMANTIC or ARGUMENT. Remaining types are semantic. ASSUMES targets an assumption/approximation; EVIDENCE_FOR targets an argument claim; CONTAINS is source structure. APPROXIMATES and PART_OF remain general scientific relations rather than being incorrectly limited to approximation/source nodes. Relationship validity is not proved by endpoint typing.

Claim, Equation and Figure are now persisted canonical-node subtypes. Both nodes and edges carry real epistemic metadata. Source/scientific review scopes differ; current scientific paths require current scope/fingerprint checks. PREREQUISITE_OF and inverse DEPENDS_ON normalize to prerequisite → dependent for cycle checks. Full relation-specific scientific criteria, external-source contracts and entity resolution remain incomplete.
