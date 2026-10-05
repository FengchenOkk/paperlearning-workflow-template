from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def identifier() -> str:
    return str(uuid4())


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


class Base(DeclarativeBase):
    pass


class PaperRow(Base):
    __tablename__ = "papers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    title: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64), unique=True)
    page_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(default=timestamp)
    parser: Mapped[str] = mapped_column(default="")
    parser_version: Mapped[str] = mapped_column(default="")
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)


class PageRow(Base):
    __tablename__ = "paper_pages"
    __table_args__ = (UniqueConstraint("paper_id", "number"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    number: Mapped[int]
    width: Mapped[float]
    height: Mapped[float]
    rotation: Mapped[int]


class SpanRow(Base):
    __tablename__ = "source_spans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    page_id: Mapped[str] = mapped_column(ForeignKey("paper_pages.id"))
    page_number: Mapped[int]
    reading_order: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    bbox: Mapped[list[float]] = mapped_column(JSON)
    kind: Mapped[str]


class AnchorRow(Base):
    __tablename__ = "source_anchors"
    __table_args__ = (CheckConstraint("start_char >= 0 AND end_char > start_char"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    span_id: Mapped[str] = mapped_column(ForeignKey("source_spans.id"), index=True)
    page_number: Mapped[int]
    start_char: Mapped[int]
    end_char: Mapped[int]
    bbox: Mapped[list[float]] = mapped_column(JSON)
    text: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64))
    localization_precision: Mapped[str] = mapped_column(
        default="TEXT_BLOCK", server_default="TEXT_BLOCK"
    )


class GraphFields:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    confidence: Mapped[float]
    verification_status: Mapped[str]
    provenance: Mapped[list[str]] = mapped_column(JSON)
    created_by: Mapped[str]
    model: Mapped[str] = mapped_column(default="none")
    prompt_version: Mapped[str] = mapped_column(default="none")
    created_at: Mapped[str] = mapped_column(default=timestamp)
    updated_at: Mapped[str] = mapped_column(default=timestamp)
    version: Mapped[int] = mapped_column(default=1)
    verification_scope: Mapped[str | None] = mapped_column(nullable=True)


class NodeRow(GraphFields, Base):
    __tablename__ = "knowledge_nodes"
    __table_args__ = (CheckConstraint("confidence >= 0 AND confidence <= 1"),)
    type: Mapped[str]
    layer: Mapped[str]
    label: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    epistemic_status: Mapped[str]
    uncertainty_reason: Mapped[str] = mapped_column(Text)


class EdgeRow(GraphFields, Base):
    __tablename__ = "knowledge_edges"
    __table_args__ = (CheckConstraint("confidence >= 0 AND confidence <= 1"),)
    source_node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), index=True)
    target_node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), index=True)
    relation_type: Mapped[str]
    epistemic_status: Mapped[str] = mapped_column(
        default="AI_INTERPRETATION", server_default="UNVERIFIED"
    )


class EvidenceRow(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    supports_object_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), index=True)
    anchor_id: Mapped[str] = mapped_column(ForeignKey("source_anchors.id"))
    evidence_type: Mapped[str] = mapped_column(default="SOURCE_TEXT")
    support_type: Mapped[str] = mapped_column(default="SOURCE_ATTRIBUTION")
    confidence: Mapped[float] = mapped_column(default=1.0)
    verification_status: Mapped[str] = mapped_column(default="SUPPORTED")
    note: Mapped[str] = mapped_column(
        default="Exact source location; does not establish scientific validity."
    )


class JobRow(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("jobs_queue", "status", "lease_until"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), unique=True)
    status: Mapped[str] = mapped_column(default="UPLOADED")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_hash: Mapped[str]
    pipeline_version: Mapped[str] = mapped_column(default="source-graph-v2")
    attempt: Mapped[int] = mapped_column(default=0)
    lease_until: Mapped[float] = mapped_column(default=0.0)
    lease_token: Mapped[str | None] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column(default=timestamp)


class VerificationRow(Base):
    __tablename__ = "verification_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"))
    object_id: Mapped[str]
    object_kind: Mapped[str]
    reviewer: Mapped[str]
    decision: Mapped[str]
    reason: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str]
    object_version: Mapped[int]
    created_at: Mapped[str] = mapped_column(default=timestamp)
    scope: Mapped[str] = mapped_column(
        default="SOURCE_ATTRIBUTION", server_default="SOURCE_ATTRIBUTION"
    )
    scientific_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ClaimRow(Base):
    """Subtype of a canonical node. Status/text/relationships stay on that node/graph."""

    __tablename__ = "claims"
    node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), primary_key=True)
    source_anchor_id: Mapped[str] = mapped_column(ForeignKey("source_anchors.id"))
    claim_type: Mapped[str] = mapped_column(default="UNCLASSIFIED")
    qualifiers: Mapped[list[str]] = mapped_column(JSON, default=list)
    support_strength: Mapped[str] = mapped_column(default="NOT_ASSESSED")


class EquationRow(Base):
    __tablename__ = "equations"
    node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), primary_key=True)
    source_anchor_id: Mapped[str] = mapped_column(ForeignKey("source_anchors.id"))
    equation_number: Mapped[str | None] = mapped_column(nullable=True)
    normalized_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    latex: Mapped[str | None] = mapped_column(Text, nullable=True)
    symbols: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    mathematical_meaning: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    physical_meaning: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)


class FigureRow(Base):
    __tablename__ = "figures"
    node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), primary_key=True)
    source_anchor_id: Mapped[str] = mapped_column(ForeignKey("source_anchors.id"))
    figure_number: Mapped[str | None] = mapped_column(nullable=True)
    # Caption block is localized; image-region localization is unknown.
    visual_anchor_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_anchors.id"), nullable=True
    )
    surrounding_text: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    visual_observations: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    interpretations: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
