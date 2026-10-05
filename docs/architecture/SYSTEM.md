# System

PaperGraph is a local-first modular monolith for navigating scientific knowledge with original evidence. The first release delivers PDF → persisted source structure → candidate scientific entities → graph → evidence → page/bounding-box navigation. It does not claim full scientific understanding.

`backend/papergraph` owns domain contracts, SQLAlchemy persistence, document parsing, extraction, graph queries and HTTP routes. A separate worker consumes durable database jobs; uploads never run analysis inside the HTTP request. `frontend` is a strict TypeScript React workspace using Cytoscape. All projections read the same canonical database graph. PDF page images are generated locally; private document content is never sent to an external service.

PostgreSQL is the deployment database; SQLite is a local development/test option. Alembic manages both. Object storage initially uses a private filesystem volume addressed by SHA-256, independent of original filenames. The API and worker share that volume. Frontend assets are bundled locally, with no runtime CDN.

The V0 tools and projects remain a separate historical workspace. New architecture supersedes their constraints for the application; no changes are made to legacy research truth sources.

Security scope: single-user loopback deployment. Authentication, tenancy and authorization are not implemented; do not expose this development service on the public internet. Uploaded PDFs are untrusted, limited in size/page count and parsed in the worker process. A hardened parser sandbox is a later deployment prerequisite.
