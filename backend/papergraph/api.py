import logging
import time
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import integrity, repository, services
from .config import Settings
from .database import Database
from .models import AnchorRow, EvidenceRow, JobRow, NodeRow, PageRow, PaperRow, SpanRow, timestamp
from .ontology import Relation
from .parser import page_image
from .schemas import (
    Anchor,
    CandidateEdge,
    CandidateNode,
    Document,
    Edge,
    EvidenceBundle,
    Graph,
    IntegrityReport,
    Job,
    Node,
    Page,
    Paper,
    PathResult,
    SearchHit,
    Span,
    UploadResult,
    Verification,
)
from .storage import DocumentStorage

logger = logging.getLogger("papergraph.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.storage_dir.parent.mkdir(parents=True, exist_ok=True)
    database = Database(settings.database_url)
    storage = DocumentStorage(settings.storage_dir)

    def source_paper(session: Session, paper_id: str) -> PaperRow:
        paper = repository.required(session, PaperRow, paper_id)
        try:
            storage.read(paper.source_hash)
        except (ValueError, OSError):
            raise repository.Conflict("Original source missing or hash mismatch") from None
        return paper

    app = FastAPI(
        title="PaperGraph",
        version="0.1.0",
        description="Evidence-grounded source exploration. Scientific extraction is candidate-only.",
    )
    app.state.database = database
    app.state.storage = storage
    app.state.settings = settings
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.middleware("http")
    async def trace(request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            allowed_origins = {
                f"http://{request.url.netloc}",
                f"https://{request.url.netloc}",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            }
            parsed_origin = urlparse(origin)
            if origin not in allowed_origins or parsed_origin.username or parsed_origin.password:
                return JSONResponse(
                    status_code=403, content={"detail": "Cross-origin mutation is not allowed"}
                )
        request_id = str(uuid4())
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request_id=%s method=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
        return response

    @app.exception_handler(repository.NotFound)
    async def missing(_: Request, error: repository.NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(repository.Conflict)
    async def conflict(_: Request, error: repository.Conflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(ValidationError)
    async def invalid_stored_contract(_: Request, error: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Stored scientific object violates its domain contract; run integrity inspection"
            },
        )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-only", "scientific_extraction": "candidate"}

    @app.post("/api/papers", response_model=UploadResult, status_code=202)
    async def upload_paper(file: UploadFile) -> UploadResult:
        content = bytearray()
        while chunk := await file.read(1024 * 1024):
            content.extend(chunk)
            if len(content) > settings.max_upload_bytes:
                raise HTTPException(413, "PDF exceeds upload limit")
        try:
            return services.upload(database, storage, bytes(content), file.filename or "paper.pdf")
        except ValueError:
            raise HTTPException(422, "Invalid PDF or unavailable document storage") from None

    @app.get("/api/papers", response_model=list[Paper])
    def papers() -> list[Paper]:
        with database.session() as session:
            return [
                repository.paper_contract(session, row)
                for row in session.scalars(select(PaperRow).order_by(PaperRow.created_at.desc()))
            ]

    @app.get("/api/papers/{paper_id}", response_model=Paper)
    def paper_detail(paper_id: str) -> Paper:
        with database.session() as session:
            row = session.get(PaperRow, paper_id)
            if row is None:
                raise repository.NotFound("Paper not found")
            return repository.paper_contract(session, row)

    @app.get("/api/jobs/{job_id}", response_model=Job)
    def job_detail(job_id: str) -> Job:
        with database.session() as session:
            return Job.model_validate(repository.required(session, JobRow, job_id))

    @app.post("/api/jobs/{job_id}/retry", response_model=Job)
    def retry_job(job_id: str) -> Job:
        with database.session() as session:
            job = session.get(JobRow, job_id)
            if job is None:
                raise repository.NotFound("Job not found")
            result = session.execute(
                update(JobRow)
                .where(JobRow.id == job_id, JobRow.status == "FAILED")
                .values(
                    status="UPLOADED",
                    error=None,
                    progress=0,
                    lease_until=0,
                    lease_token=None,
                    updated_at=timestamp(),
                )
            )
            if result.rowcount != 1:  # type: ignore[attr-defined]
                raise repository.Conflict("Only failed jobs can be retried")
            session.refresh(job)
            return Job.model_validate(job)

    @app.get("/api/papers/{paper_id}/document", response_model=Document)
    def document(paper_id: str) -> Document:
        with database.session() as session:
            row = source_paper(session, paper_id)
            pages = []
            for page in session.scalars(
                select(PageRow).where(PageRow.paper_id == paper_id).order_by(PageRow.number)
            ):
                spans = []
                for span, anchor_id in session.execute(
                    select(SpanRow, AnchorRow.id)
                    .join(AnchorRow, AnchorRow.span_id == SpanRow.id)
                    .where(SpanRow.page_id == page.id)
                    .order_by(SpanRow.reading_order)
                ):
                    spans.append(
                        Span(
                            id=span.id,
                            anchor_id=anchor_id,
                            paper_id=span.paper_id,
                            page_number=span.page_number,
                            reading_order=span.reading_order,
                            text=span.text,
                            bbox=(span.bbox[0], span.bbox[1], span.bbox[2], span.bbox[3]),
                            kind="heading" if span.kind == "heading" else "paragraph",
                        )
                    )
                    repository.anchors_for(session, row, [anchor_id])
                pages.append(
                    Page(
                        number=page.number,
                        width=page.width,
                        height=page.height,
                        rotation=page.rotation,
                        spans=spans,
                    )
                )
            return Document(
                paper_id=paper_id,
                parser=row.parser,
                parser_version=row.parser_version,
                warnings=row.warnings,
                pages=pages,
            )

    @app.get("/api/papers/{paper_id}/pdf")
    def original(paper_id: str) -> Response:
        with database.session() as session:
            row = session.get(PaperRow, paper_id)
            if row is None:
                raise repository.NotFound("Paper not found")
            try:
                return Response(
                    storage.read(row.source_hash),
                    media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="paper.pdf"'},
                )
            except (ValueError, OSError):
                raise HTTPException(409, "Source missing or hash mismatch") from None

    @app.get("/api/papers/{paper_id}/pages/{number}/image")
    def image(paper_id: str, number: int) -> Response:
        with database.session() as session:
            row = session.get(PaperRow, paper_id)
            if row is None:
                raise repository.NotFound("Paper not found")
            if number < 1 or number > row.page_count:
                raise HTTPException(404, "Page not found")
            try:
                return Response(
                    page_image(storage.read(row.source_hash), number), media_type="image/png"
                )
            except (ValueError, OSError):
                raise HTTPException(409, "Source missing or hash mismatch") from None

    @app.get("/api/papers/{paper_id}/graph", response_model=Graph)
    def paper_graph(
        paper_id: str,
        view: Literal["knowledge", "argument", "innovation", "learning"] = "knowledge",
        limit: Annotated[int, Query(ge=1, le=500)] = 80,
    ) -> Graph:
        with database.session() as session:
            source_paper(session, paper_id)
            return repository.graph(session, paper_id, view, limit)

    @app.get("/api/nodes/{node_id}/neighborhood", response_model=Graph)
    def neighbors(
        node_id: str,
        depth: Annotated[int, Query(ge=0, le=4)] = 1,
        limit: Annotated[int, Query(ge=1, le=300)] = 80,
    ) -> Graph:
        with database.session() as session:
            source_paper(session, repository.required(session, NodeRow, node_id).paper_id)
            return repository.neighborhood(session, node_id, depth, limit)

    @app.get("/api/nodes/{node_id}", response_model=Node)
    def node_detail(node_id: str) -> Node:
        with database.session() as session:
            source_paper(session, repository.required(session, NodeRow, node_id).paper_id)
            return repository.node_contract(session, repository.required(session, NodeRow, node_id))

    @app.get("/api/nodes/{node_id}/evidence", response_model=EvidenceBundle)
    def node_evidence(node_id: str) -> EvidenceBundle:
        with database.session() as session:
            node = repository.required(session, NodeRow, node_id)
            source_paper(session, node.paper_id)
            return repository.evidence_bundle(session, node_id)

    @app.get("/api/anchors/{anchor_id}", response_model=Anchor)
    def anchor_detail(anchor_id: str) -> Anchor:
        with database.session() as session:
            anchor = repository.required(session, AnchorRow, anchor_id)
            paper = source_paper(session, anchor.paper_id)
            return Anchor.model_validate(repository.anchors_for(session, paper, [anchor_id])[0])

    @app.get("/api/anchors/{anchor_id}/nodes", response_model=list[Node])
    def anchor_nodes(anchor_id: str) -> list[Node]:
        with database.session() as session:
            anchor = repository.required(session, AnchorRow, anchor_id)
            paper = source_paper(session, anchor.paper_id)
            repository.anchors_for(session, paper, [anchor_id])
            nodes = list(
                session.scalars(
                    select(NodeRow)
                    .join(EvidenceRow, EvidenceRow.supports_object_id == NodeRow.id)
                    .where(EvidenceRow.anchor_id == anchor_id)
                    .distinct()
                )
            )
            for node in nodes:
                if node.paper_id != paper.id or anchor_id not in node.provenance:
                    raise repository.Conflict(
                        "Reverse source association conflicts with node provenance"
                    )
            return [repository.evidence_bundle(session, node.id).node for node in nodes]

    @app.get("/api/papers/{paper_id}/search", response_model=list[SearchHit])
    def search(
        paper_id: str, q: Annotated[str, Query(min_length=2, max_length=200)]
    ) -> list[SearchHit]:
        with database.session() as session:
            paper = source_paper(session, paper_id)
            hits = []
            query = (
                select(NodeRow)
                .where(
                    NodeRow.paper_id == paper_id,
                    (
                        NodeRow.text.icontains(q, autoescape=True)
                        | NodeRow.label.icontains(q, autoescape=True)
                    ),
                )
                .limit(30)
            )
            for node in session.scalars(query):
                if node.provenance:
                    anchor = session.get(AnchorRow, node.provenance[0])
                    if anchor:
                        repository.anchors_for(session, paper, [anchor.id])
                        hits.append(
                            SearchHit(
                                node_id=node.id,
                                anchor_id=anchor.id,
                                page_number=anchor.page_number,
                                text=node.text,
                                kind=node.type,
                            )
                        )
            used = {h.anchor_id for h in hits}
            for anchor in session.scalars(
                select(AnchorRow)
                .where(AnchorRow.paper_id == paper_id, AnchorRow.text.icontains(q, autoescape=True))
                .limit(30)
            ):
                if anchor.id not in used:
                    repository.anchors_for(session, paper, [anchor.id])
                    hits.append(
                        SearchHit(
                            node_id=None,
                            anchor_id=anchor.id,
                            page_number=anchor.page_number,
                            text=anchor.text,
                            kind="SOURCE_SPAN",
                        )
                    )
            return hits[:50]

    @app.get("/api/papers/{paper_id}/integrity", response_model=IntegrityReport)
    def integrity_report(paper_id: str) -> IntegrityReport:
        with database.session() as session:
            result = integrity.report(session, paper_id)
            paper = repository.required(session, PaperRow, paper_id)
            try:
                storage.read(paper.source_hash)
            except (ValueError, OSError):
                from .schemas import IntegrityIssue

                result.issues.append(
                    IntegrityIssue(
                        code="SOURCE_HASH_MISMATCH",
                        object_id=paper_id,
                        detail="Original PDF missing or bytes do not match stored hash",
                    )
                )
                result.structurally_valid = False
            return result

    @app.post("/api/papers/{paper_id}/nodes", response_model=Node, status_code=201)
    def candidate_node(paper_id: str, draft: CandidateNode) -> Node:
        with database.session() as session:
            source_paper(session, paper_id)
            return repository.add_candidate(session, paper_id, draft)

    @app.post("/api/papers/{paper_id}/edges", response_model=Edge, status_code=201)
    def candidate_edge(paper_id: str, draft: CandidateEdge) -> Edge:
        with database.session() as session:
            source_paper(session, paper_id)
            return repository.add_edge(session, paper_id, draft)

    @app.post("/api/nodes/{node_id}/verification", response_model=Node)
    def node_verification(node_id: str, review: Verification) -> Node | Edge:
        with database.session() as session:
            source_paper(session, repository.required(session, NodeRow, node_id).paper_id)
            return repository.verify(session, node_id, "node", review)

    @app.post("/api/edges/{edge_id}/verification", response_model=Edge)
    def edge_verification(edge_id: str, review: Verification) -> Node | Edge:
        with database.session() as session:
            from .models import EdgeRow

            source_paper(session, repository.required(session, EdgeRow, edge_id).paper_id)
            return repository.verify(session, edge_id, "edge", review)

    @app.get("/api/nodes/{node_id}/paths", response_model=PathResult)
    def path(
        node_id: str, target: str, relation: Relation | None = None, verified_only: bool = False
    ) -> PathResult:
        with database.session() as session:
            source_paper(session, repository.required(session, NodeRow, node_id).paper_id)
            return repository.semantic_path(session, node_id, target, relation, verified_only)

    web = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if web.exists():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(web / "index.html")

    return app


app = create_app()
