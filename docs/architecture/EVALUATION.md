# Evaluation and acceptance

Golden public paper: Srivastava et al., *Dropout: A Simple Way to Prevent Neural Networks from Overfitting*, JMLR 15 (2014). Download URL and document hash live under evals; the PDF remains ignored. Manually checked first-page title, abstract wording and method statement are gold assertions, not model-generated truth.

First slice checks: upload a real PDF; worker persists pages/spans/anchors; scientific candidates are drawn from exact text; graph node inspection resolves evidence; real page pixels and anchor coordinates are served; refresh/restart retains identity and graph; duplicate upload does not destroy reviews. API, database and browser tests exercise the same endpoints used by the workspace.

Negative cases: invalid/encrypted/oversized PDFs, empty/scanned pages, missing references, foreign-paper anchors, fabricated text ranges, unsupported VERIFIED assertions, stale version/hash, graph path cycles and recovery from expired jobs. Count valid evidence coverage for scientific candidates separately from extraction precision. Valid provenance does not prove a scientific claim.

Full product gates still outstanding: equation semantics/localization across papers, visual figure interpretation, argument support judgments, verified prerequisites, innovation lineage, translation fidelity, first-principles path usefulness and expert review. No JSON-valid output or successful build can substitute for these gates.
