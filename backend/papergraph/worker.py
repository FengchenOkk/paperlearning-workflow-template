import argparse
import logging
import time
import unicodedata
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select, update

from .config import Settings
from .database import Database
from .extraction import extract
from .integrity import report
from .models import (
    AnchorRow,
    EdgeRow,
    EvidenceRow,
    JobRow,
    NodeRow,
    PageRow,
    PaperRow,
    SpanRow,
    identifier,
    timestamp,
)
from .parser import DocumentParser, MuPDFParser, ParsedBlock
from .scientific_objects import ensure_scientific_object
from .storage import DocumentStorage

logger = logging.getLogger("papergraph.worker")
TERMINAL = ["READY", "PARTIAL", "FAILED"]


def stable(paper_id: str, key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"papergraph:{paper_id}:source-graph-v1:{key}"))


def title_blocks(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    candidates = [block for block in blocks if block.kind == "heading" and len(block.text) > 20]
    if not candidates:
        return []
    first = max(candidates, key=lambda block: block.font_size)
    result = [first]
    for block in blocks[blocks.index(first) + 1 :]:
        if (
            block.kind != "heading"
            or abs(block.font_size - first.font_size) > 0.5
            or not 0 <= block.bbox[1] - result[-1].bbox[3] <= 35
        ):
            break
        result.append(block)
    return result


def run_once(
    db: Database, storage: DocumentStorage, settings: Settings, parser: DocumentParser | None = None
) -> bool:
    parser = parser or MuPDFParser()
    now = time.time()
    token = identifier()
    with db.session() as session:
        next_job = (
            select(JobRow.id)
            .where(JobRow.status.not_in(TERMINAL), JobRow.lease_until <= now)
            .order_by(JobRow.updated_at)
            .limit(1)
            .scalar_subquery()
        )
        claimed = session.execute(
            update(JobRow)
            .where(JobRow.id == next_job, JobRow.status.not_in(TERMINAL), JobRow.lease_until <= now)
            .values(
                lease_token=token,
                lease_until=now + settings.lease_seconds,
                status="PARSING",
                progress=10,
                attempt=JobRow.attempt + 1,
                updated_at=timestamp(),
            )
            .returning(JobRow.id, JobRow.paper_id, JobRow.input_hash)
        ).first()
        if claimed is None:
            return False
        job_id, paper_id, digest = claimed
    try:
        content = storage.read(digest)
        parsed = []
        for page in parser.pages(content, settings.max_pages):
            parsed.append(page)
            with db.session() as session:
                heartbeat = session.execute(
                    update(JobRow)
                    .where(JobRow.id == job_id, JobRow.lease_token == token)
                    .values(
                        lease_until=time.time() + settings.lease_seconds, updated_at=timestamp()
                    )
                )
                if heartbeat.rowcount != 1:  # type: ignore[attr-defined]
                    raise ValueError("LEASE_LOST")
        with db.session() as session:
            session.execute(
                update(JobRow)
                .where(JobRow.id == job_id, JobRow.lease_token == token)
                .values(status="PARSED", progress=45, updated_at=timestamp())
            )
        with db.session() as session:
            session.execute(
                update(JobRow)
                .where(JobRow.id == job_id, JobRow.lease_token == token)
                .values(status="ENTITY_EXTRACTION", progress=55, updated_at=timestamp())
            )
        entities = {
            (page.number, block.order): extract(block.text, block.kind == "heading")
            for page in parsed
            for block in page.blocks
        }
        with db.session() as session:
            session.execute(
                update(JobRow)
                .where(JobRow.id == job_id, JobRow.lease_token == token)
                .values(status="GRAPH_BUILDING", progress=75, updated_at=timestamp())
            )
        with db.session() as session:
            job = session.scalar(select(JobRow).where(JobRow.id == job_id).with_for_update())
            paper = session.get(PaperRow, paper_id)
            if job is None or paper is None or job.lease_token != token:
                raise ValueError("LEASE_LOST")
            job.status, job.progress = "GRAPH_BUILDING", 75
            paper.page_count = len(parsed)
            paper.parser, paper.parser_version = parser.name, parser.version
            warnings = []
            selected_title = title_blocks(parsed[0].blocks) if parsed else []
            if selected_title:
                paper.title = unicodedata.normalize(
                    "NFKC", " ".join(" ".join(block.text.split()) for block in selected_title)
                )[:500]
            title_orders = {block.order for block in selected_title}
            title_anchors = []
            root = NodeRow(
                id=paper_id,
                paper_id=paper_id,
                type="PAPER",
                layer="SOURCE",
                label=paper.title,
                text="\n".join(block.text for block in selected_title)
                if selected_title
                else paper.title,
                confidence=1,
                verification_status="SUPPORTED",
                epistemic_status="PAPER_EXPLICIT" if selected_title else "UNKNOWN",
                uncertainty_reason="Title extracted using font and adjacency heuristics; not a scientific assertion."
                if selected_title
                else "Title unknown; original filename displayed as a label.",
                provenance=[],
                created_by="document-parser",
            )
            session.add(root)
            session.flush()
            for page in parsed:
                page_id = stable(paper_id, f"page:{page.number}")
                session.add(
                    PageRow(
                        id=page_id,
                        paper_id=paper_id,
                        number=page.number,
                        width=page.width,
                        height=page.height,
                        rotation=page.rotation,
                    )
                )
                session.flush()
                if not page.blocks:
                    warnings.append(
                        f"Page {page.number}: no extractable text. OCR is not configured."
                    )
                for block in page.blocks:
                    span_id = stable(paper_id, f"span:{page.number}:{block.order}")
                    session.add(
                        SpanRow(
                            id=span_id,
                            paper_id=paper_id,
                            page_id=page_id,
                            page_number=page.number,
                            reading_order=block.order,
                            text=block.text,
                            bbox=list(block.bbox),
                            kind=block.kind,
                        )
                    )
                    session.flush()
                    anchor_id = stable(paper_id, f"anchor:{span_id}")
                    session.add(
                        AnchorRow(
                            id=anchor_id,
                            paper_id=paper_id,
                            span_id=span_id,
                            page_number=page.number,
                            start_char=0,
                            end_char=len(block.text),
                            bbox=list(block.bbox),
                            text=block.text,
                            source_hash=digest,
                        )
                    )
                    session.flush()
                    if page.number == 1 and block.order in title_orders:
                        title_anchors.append(anchor_id)
                    for number, candidate in enumerate(entities[page.number, block.order]):
                        node_id = stable(paper_id, f"node:{span_id}:{number}")
                        label = " ".join(candidate.text.split())
                        session.add(
                            NodeRow(
                                id=node_id,
                                paper_id=paper_id,
                                type=candidate.type,
                                layer=candidate.layer,
                                label=label[:110] + ("…" if len(label) > 110 else ""),
                                text=candidate.text,
                                confidence=0.6,
                                verification_status="CANDIDATE",
                                epistemic_status=candidate.epistemic_status,
                                uncertainty_reason=candidate.reason,
                                provenance=[anchor_id],
                                created_by="local-rule-extractor-v2",
                            )
                        )
                        session.flush()
                        candidate_node = session.get(NodeRow, node_id)
                        if candidate_node is None:
                            raise ValueError("MISSING_CANDIDATE")
                        ensure_scientific_object(session, candidate_node)
                        session.add(
                            EvidenceRow(
                                id=stable(paper_id, f"evidence:{node_id}"),
                                supports_object_id=node_id,
                                anchor_id=anchor_id,
                            )
                        )
                        session.add(
                            EdgeRow(
                                id=stable(paper_id, f"edge:{node_id}"),
                                paper_id=paper_id,
                                source_node_id=paper_id,
                                target_node_id=node_id,
                                relation_type="CONTAINS",
                                confidence=1,
                                verification_status="SUPPORTED",
                                provenance=[anchor_id],
                                created_by="document-parser",
                                epistemic_status="PAPER_EXPLICIT",
                            )
                        )
            root.provenance = title_anchors
            for anchor_id in title_anchors:
                session.add(EvidenceRow(supports_object_id=root.id, anchor_id=anchor_id))
            paper.warnings = warnings
            session.flush()
            if not report(session, paper_id).structurally_valid:
                raise ValueError("GRAPH_INTEGRITY_FAILED")
            job.status = "PARTIAL" if warnings else "READY"
            job.progress, job.error, job.lease_until, job.lease_token = 100, None, 0, None
            job.updated_at = timestamp()
        logger.info(
            "job_complete job_id=%s paper_id=%s status=%s",
            job_id,
            paper_id,
            "PARTIAL" if warnings else "READY",
        )
    except Exception as error:
        category = (
            str(error)
            if isinstance(error, ValueError)
            and str(error) in {"ENCRYPTED_PDF", "PAGE_LIMIT_EXCEEDED", "EMPTY_PDF", "LEASE_LOST"}
            else "DOCUMENT_PROCESSING_FAILED"
        )
        with db.session() as session:
            session.execute(
                update(JobRow)
                .where(JobRow.id == job_id, JobRow.lease_token == token)
                .values(
                    status="FAILED",
                    error=category,
                    lease_until=0,
                    lease_token=None,
                    updated_at=timestamp(),
                )
            )
        logger.warning("job_failed job_id=%s category=%s", job_id, category)
    return True


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--once", action="store_true")
    options = args.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    db = Database(settings.database_url)
    storage = DocumentStorage(settings.storage_dir)
    while True:
        processed = run_once(db, storage, settings)
        if options.once:
            break
        if not processed:
            time.sleep(1)


if __name__ == "__main__":
    main()
