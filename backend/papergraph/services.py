from pathlib import PurePath

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import Database
from .models import JobRow, PaperRow
from .repository import paper_contract
from .schemas import Job, UploadResult
from .storage import DocumentStorage


def upload(db: Database, storage: DocumentStorage, content: bytes, filename: str) -> UploadResult:
    if not content.startswith(b"%PDF-"):
        raise ValueError("Expected a PDF document")
    digest = storage.put(content)
    try:
        with db.session() as session:
            paper = session.scalar(select(PaperRow).where(PaperRow.source_hash == digest))
            deduplicated = paper is not None
            if paper is None:
                paper = PaperRow(
                    title=PurePath(filename.replace("\\", "/")).stem[:500] or "Untitled paper",
                    source_hash=digest,
                )
                session.add(paper)
                session.flush()
                session.add(JobRow(paper_id=paper.id, input_hash=digest))
                session.flush()
            job = session.scalar(select(JobRow).where(JobRow.paper_id == paper.id))
            if job is None:
                raise ValueError("Missing job")
            return UploadResult(
                paper=paper_contract(session, paper),
                job=Job.model_validate(job),
                deduplicated=deduplicated,
            )
    except IntegrityError:
        # Concurrent identical uploads resolve to the already-created immutable document.
        with db.session() as session:
            paper = session.scalar(select(PaperRow).where(PaperRow.source_hash == digest))
            if paper is None:
                raise
            job = session.scalar(select(JobRow).where(JobRow.paper_id == paper.id))
            if job is None:
                raise
            return UploadResult(
                paper=paper_contract(session, paper), job=Job.model_validate(job), deduplicated=True
            )
