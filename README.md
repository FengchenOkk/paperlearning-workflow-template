# PaperGraph

An evidence-grounded workspace for understanding scientific papers through typed knowledge graphs and original source locations.

Open a PDF, inspect its scientific candidates, follow a node to exact source text, and jump to the corresponding page and bounding box. The database owns the source model, graph, evidence and review history. Markdown and JSON are exports, not application state.

**Current release:** the first PDF → graph → evidence vertical slice works locally. Extraction uses conservative rules and produces **candidates**, not scientifically verified explanations. First-principles reasoning, argument evaluation, equation derivation and innovation analysis are future milestones. This is not yet the complete research-grade product described by the master prompt.

## Start locally

No AI key is needed. No document is sent to a remote model. Python 3.11+ and Node 22+ are required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
cd frontend
npm ci --ignore-scripts
cd ..
.\infra\start-local.ps1
```

Open [PaperGraph](http://127.0.0.1:8000). Select **Open PDF** to upload a paper. The worker parses it in the background; select a graph node or a source text block to inspect evidence. The node navigator also provides keyboard access to canvas nodes. Use **Review scientific status** only after checking the original evidence; each review records the reviewer, reason, source hash and object version.

If this machine's npm wrapper fails, use the installed CLI directly:

```powershell
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" ci --ignore-scripts --prefix frontend
```

The startup script recognizes that installation. It stops its worker when the server stops. Data stays in `backend/data/`, which is ignored by Git. Existing `.env`, local model configurations and legacy research projects are neither loaded nor migrated.

For macOS/Linux or separate terminals:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
(cd frontend && npm ci --ignore-scripts && npm run build)
cd backend
mkdir -p data
python -m alembic upgrade head
python -m papergraph.worker
# In another activated terminal, from backend:
python -m uvicorn papergraph.api:app --host 127.0.0.1 --port 8000 --no-access-log
```

## Docker / PostgreSQL

```sh
docker compose up --build
```

This builds the frontend, migrates PostgreSQL, and starts the API and worker with persistent volumes. The API binds to loopback on port 8000. The included database password is for local development only; `PAPERGRAPH_DB_PASSWORD` can override it. Compose configuration has been checked; a container deployment has not been tested on this host because its Docker daemon is unavailable.

## Architecture

- **Backend:** FastAPI, strict Pydantic contracts, SQLAlchemy and Alembic.
- **Canonical graph:** database nodes/edges with typed relations, evidence and audited verification.
- **Source:** local PyMuPDF adapter, exact text blocks, page geometry, reading order and source hashes.
- **Worker:** persistent jobs, atomic leases, failure recovery and real stage updates.
- **Frontend:** React/TypeScript, Vite and Cytoscape; bounded graph views, search, evidence inspector and original page rendering.
- **Storage:** content-addressed PDFs in a private local directory. SQLite for local development, PostgreSQL for deployment.

Read the [system design](docs/architecture/SYSTEM.md), [data model](docs/architecture/DATA-MODEL.md), [provenance rules](docs/architecture/PROVENANCE.md), [ontology](docs/ontology/SCIENTIFIC-ONTOLOGY.md), [legacy audit](docs/legacy-audit.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md). API contracts are available at [local OpenAPI docs](http://127.0.0.1:8000/docs).

## Development and validation

From an activated Python environment:

```sh
python evals/download_fixture.py
cd backend
ruff check .
ruff format --check .
mypy papergraph
pytest -q
python -m scripts.export_contracts
python -m playwright install chromium
python scripts/run_e2e.py
cd ../frontend
node scripts/generate-contracts.mjs
npm run lint
npm run typecheck
npm test
npm run build
cd ..
python -m unittest discover -s tests
```

The public [JMLR Dropout paper](https://jmlr.org/papers/v15/srivastava14a.html) provides a real golden fixture. Its PDF is downloaded into an ignored folder; tracked metadata records the URL, expected hash and a small manually checked gold set. Synthetic PDFs are limited to explicitly labeled parser/negative tests. Browser tests use fresh storage and test the actual upload/worker/UI journey. The checked validation results and limits are in [VALIDATION.md](docs/VALIDATION.md).

Type contracts originate in Pydantic. `packages/schemas/domain.schema.json` and `frontend/src/contracts.ts` are generated views; regenerate both after schema changes. Frontend dependencies have a lockfile. CI runs backend lint/type checks/tests, frontend lint/type checks/tests/build, original regression tests and the browser journey without secrets.

## Scientific integrity and current limits

Source wording, author assertions, interpretations and verification are separate fields. Every extracted scientific candidate has exact source attribution. Containment only says that a paper contains a candidate; it does not imply support, causality, derivation or prerequisite dependence. Automatic extraction never marks scientific nodes VERIFIED. A human review is explicit and cannot be silently overwritten by duplicate uploads. Stale hashes/versions and invalid evidence ranges are rejected.

This release has one parser and a rule-based English candidate extractor. Heading detection and title assembly are heuristic; reading order may be inaccurate for complex columns. Equation nodes preserve source text rather than validated LaTeX or derivations. Figure/table nodes represent caption candidates, not visual analysis or reconstructed cells. OCR is not configured; empty/scanned pages produce PARTIAL and explicit warnings. Argument/innovation controls show filtered candidates with a pending-analysis label. Learning views remain empty until real prerequisite data exists.

External scholarly retrieval, structured AI extraction, translation, grounded chat, entity resolution, multi-paper connections and a first-principles engine are not implemented. No claim of extraction recall or scientific correctness follows from successful tests. PyMuPDF's AGPL/commercial license requires a release decision for proprietary distribution. This is a single-user local development service; authentication, tenancy and a hardened parser sandbox remain deployment work.

## V0 research workspace

The original `projects/`, `workflow/`, `config/`, `tools/` and tests remain available separately. They do not constrain or supply the new application's graph. User research and manual notes have not been overwritten. The former command reference is preserved in [legacy-cli.md](docs/legacy-cli.md).
