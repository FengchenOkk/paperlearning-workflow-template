# Processing pipeline

Upload validation → content-addressed PDF storage → UPLOADED job → worker lease → PARSING → PARSED → ENTITY_EXTRACTION → GRAPH_BUILDING → READY/PARTIAL. Failures record a safe error category without logging private source text. Jobs survive API restarts. Expired leases permit recovery after worker failure. Writes for source and graph construction are one transaction, so retry does not expose half a graph.

DocumentParser is a protocol; PyMuPDF is the initial implementation. It extracts page dimensions, real text blocks, bounding boxes and font-derived heading candidates. Reading order is a parser heuristic, especially for columns. Scanned/empty pages yield warnings and PARTIAL, never invented OCR. OCR, GROBID and Docling are future adapters.

Conservative local extraction recognizes numbered equation candidates, figure/table captions and explicit author method/result/claim sentences. Source fidelity is exact; scientific classification is CANDIDATE with an uncertainty reason. Equations are source text, not guaranteed LaTeX. Figure captions do not stand in for visual analysis. No keyword co-occurrence or automatic scientific dependency is emitted.

Graph construction persists claim/equation/figure subtypes under the existing node IDs and runs structural integrity validation before publication. Source/caption fields are real; analyses remain unknown. Caption recognition precedes heading heuristics. Scientific review scope/fingerprint is separate from parsing status.

PLANNED pipeline: validated structured extraction → argument graph → bounded prerequisite decomposition → scholarly evidence retrieval → independent verification → innovation/learning projections. These stages are not implemented. Future first-principles stopping rules should consider reader assumptions, useful depth and user limits; unresolved dependencies must remain unknown. Next gate is independent source-quality assessment of the corrected PAPER → GRAPH → EVIDENCE foundation.
