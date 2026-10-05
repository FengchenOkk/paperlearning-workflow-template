# ADR-001: foundation choices

Accepted for the first vertical slice on 2026-10-05.

1. SQLAlchemy nodes/edges over PostgreSQL; SQLite enables private offline development. No Neo4j or embedding service until evidence-backed retrieval needs them.
2. Alembic is the only schema deployment path. Domain contracts are Pydantic, frontend types generated from their JSON Schema.
3. PyMuPDF behind DocumentParser; page images plus exact bbox navigation initially. OCR and specialized equation/table parsers deferred. AGPL/commercial licensing remains a release decision.
4. React/Vite/Cytoscape for a client workspace. Next.js and PDF.js are optional later adapters, not prerequisites for the evidence model.
5. Durable database job queue with transactional leases for the local monolith. One worker initially; no Redis dependency for offline startup. A mature distributed queue should replace it if scheduling/concurrency requirements expand.
6. Source-only deterministic candidate extraction initially. Scientific interpretation and verification remain explicit future stages. Existing user research and profiles are isolated, never automatically migrated.
