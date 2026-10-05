from collections import deque
from typing import TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .errors import Conflict as Conflict
from .errors import NotFound as NotFound
from .integrity import INACTIVE, prerequisite_cycles, scientific_path_object, validate_edge
from .models import (
    Base,
    EdgeRow,
    EvidenceRow,
    JobRow,
    NodeRow,
    PaperRow,
    VerificationRow,
    identifier,
    timestamp,
)
from .ontology import EpistemicStatus, NodeType, Relation, ReviewScope, VerificationStatus
from .provenance import anchors_for as anchors_for
from .provenance import current_review, fingerprint
from .schemas import (
    Anchor,
    CandidateEdge,
    CandidateNode,
    Edge,
    EvidenceBundle,
    EvidenceItem,
    Graph,
    Node,
    Paper,
    PathResult,
    Verification,
)
from .scientific_objects import ensure_scientific_object, scientific_object

RowType = TypeVar("RowType", bound=Base)


def node_contract(session: Session, row: NodeRow) -> Node:
    paper = required(session, PaperRow, row.paper_id)
    if row.type != "PAPER" and not row.provenance:
        raise Conflict("Paper-derived node has no provenance")
    anchors = anchors_for(session, paper, row.provenance)
    if (
        row.type != "PAPER"
        and row.epistemic_status in {"PAPER_EXPLICIT", "AUTHOR_CLAIM"}
        and not any(row.text in a.text for a in anchors)
    ):
        raise Conflict("Attributed node text does not match its source")
    scientific_object(session, row)
    return Node.model_validate(row).model_copy(
        update={
            "review_current": current_review(session, row)
            if row.verification_status in {"VERIFIED", "REJECTED", "DISPUTED"}
            else None
        }
    )


def edge_contract(session: Session, row: EdgeRow) -> Edge:
    validate_edge(session, row)
    paper = required(session, PaperRow, row.paper_id)
    if not row.provenance:
        raise Conflict("Relationship has no source provenance")
    anchors_for(session, paper, row.provenance)
    return Edge.model_validate(row).model_copy(
        update={
            "review_current": current_review(session, row)
            if row.verification_status in {"VERIFIED", "REJECTED", "DISPUTED"}
            else None
        }
    )


def required(
    session: Session,
    model: type[RowType],
    key: str,
) -> RowType:
    row = session.get(model, key)
    if row is None:
        raise NotFound("Object not found")
    return row


def paper_contract(session: Session, paper: PaperRow) -> Paper:
    job = session.scalar(select(JobRow).where(JobRow.paper_id == paper.id))
    if job is None:
        raise NotFound("Paper job not found")
    return Paper(
        id=paper.id,
        title=paper.title,
        source_hash=paper.source_hash,
        page_count=paper.page_count,
        created_at=paper.created_at,
        job_id=job.id,
    )


def evidence_bundle(session: Session, node_id: str) -> EvidenceBundle:
    node = session.get(NodeRow, node_id)
    if node is None:
        raise NotFound("Node not found")
    items = []
    paper = required(session, PaperRow, node.paper_id)
    anchors_for(session, paper, node.provenance)
    for evidence in session.scalars(
        select(EvidenceRow).where(EvidenceRow.supports_object_id == node_id)
    ):
        if evidence.anchor_id not in node.provenance:
            raise Conflict("Evidence association conflicts with canonical node provenance")
        anchor = anchors_for(session, paper, [evidence.anchor_id])[0]
        items.append(
            EvidenceItem(
                id=evidence.id,
                supports_object_id=node_id,
                evidence_type=evidence.evidence_type,
                support_type=evidence.support_type,
                confidence=evidence.confidence,
                verification_status=VerificationStatus(evidence.verification_status),
                note=evidence.note,
                anchor=Anchor.model_validate(anchor),
            )
        )
    return EvidenceBundle(
        node=node_contract(session, node),
        evidence=items,
        scientific_object=scientific_object(session, node),
    )


def graph(session: Session, paper_id: str, view: str, limit: int) -> Graph:
    required(session, PaperRow, paper_id)
    query = select(NodeRow).where(NodeRow.paper_id == paper_id)
    if view == "argument":
        query = query.where(
            NodeRow.type.in_(
                [
                    "PAPER",
                    "CLAIM",
                    "EVIDENCE",
                    "OBSERVATION",
                    "RESULT",
                    "CONCLUSION",
                    "ASSUMPTION",
                    "LIMITATION",
                ]
            )
        )
    elif view == "innovation":
        query = query.where(
            NodeRow.type.in_(
                [
                    "PAPER",
                    "PRIOR_WORK",
                    "RESEARCH_GAP",
                    "METHOD",
                    "CONTRIBUTION",
                    "INNOVATION",
                    "RESULT",
                    "LIMITATION",
                ]
            )
        )
    elif view == "learning":
        query = query.where(NodeRow.layer == "LEARNING")
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # Keep paper root first, then bounded candidates. Stable pagination seed.
    rows = list(
        session.scalars(
            query.order_by((NodeRow.type != "PAPER"), NodeRow.created_at, NodeRow.id).limit(limit)
        )
    )
    ids = [node.id for node in rows]
    edges = (
        list(
            session.scalars(
                select(EdgeRow).where(
                    EdgeRow.paper_id == paper_id,
                    EdgeRow.source_node_id.in_(ids),
                    EdgeRow.target_node_id.in_(ids),
                )
            )
        )
        if ids
        else []
    )
    return Graph(
        nodes=[node_contract(session, n) for n in rows],
        edges=[edge_contract(session, e) for e in edges],
        total_nodes=total,
        truncated=total > limit,
    )


def neighborhood(session: Session, node_id: str, depth: int, limit: int) -> Graph:
    node = session.get(NodeRow, node_id)
    if node is None:
        raise NotFound("Node not found")
    ids = {node_id}
    frontier = {node_id}
    truncated = False
    for _ in range(depth):
        neighbors = list(
            session.scalars(
                select(EdgeRow)
                .where(
                    EdgeRow.paper_id == node.paper_id,
                    (EdgeRow.source_node_id.in_(frontier) | EdgeRow.target_node_id.in_(frontier)),
                )
                .limit(limit * 2 + 1)
            )
        )
        next_ids = {key for e in neighbors for key in [e.source_node_id, e.target_node_id]} - ids
        available = max(0, limit - len(ids))
        if len(next_ids) > available or len(neighbors) > limit * 2:
            truncated = True
        frontier = set(sorted(next_ids)[:available])
        ids.update(frontier)
        if not frontier:
            break
    rows = session.scalars(select(NodeRow).where(NodeRow.id.in_(ids)).order_by(NodeRow.id))
    edges = session.scalars(
        select(EdgeRow).where(EdgeRow.source_node_id.in_(ids), EdgeRow.target_node_id.in_(ids))
    )
    return Graph(
        nodes=[node_contract(session, n) for n in rows],
        edges=[edge_contract(session, e) for e in edges],
        total_nodes=len(ids),
        truncated=truncated,
    )


def add_candidate(session: Session, paper_id: str, draft: CandidateNode) -> Node:
    paper = session.get(PaperRow, paper_id)
    if paper is None:
        raise NotFound("Paper not found")
    if draft.type in {NodeType.PAPER, NodeType.SOURCE_SPAN, NodeType.PARAGRAPH, NodeType.SECTION}:
        raise Conflict("Source structure cannot be replaced by an annotation")
    anchors = anchors_for(session, paper, draft.anchor_ids)
    if (
        draft.type in {NodeType.EQUATION, NodeType.FIGURE, NodeType.TABLE}
        and draft.epistemic_status != EpistemicStatus.PAPER_EXPLICIT
    ):
        raise Conflict(
            "Source objects require explicit source wording; interpretations belong to separate annotations"
        )
    if draft.epistemic_status in {
        EpistemicStatus.PAPER_EXPLICIT,
        EpistemicStatus.AUTHOR_CLAIM,
    } and not any(draft.text in a.text for a in anchors):
        raise Conflict("Paper attribution must match exact source text")
    node = NodeRow(
        id=identifier(),
        paper_id=paper_id,
        type=draft.type,
        layer=draft.layer,
        label=draft.label,
        text=draft.text,
        confidence=draft.confidence,
        epistemic_status=draft.epistemic_status,
        verification_status="CANDIDATE",
        uncertainty_reason=draft.uncertainty_reason,
        provenance=[a.id for a in anchors],
        created_by="manual-annotation",
    )
    session.add(node)
    session.flush()
    ensure_scientific_object(session, node)
    for anchor in anchors:
        session.add(EvidenceRow(supports_object_id=node.id, anchor_id=anchor.id))
    return Node.model_validate(node)


def semantic_path(
    session: Session,
    source: str,
    target: str,
    relation: Relation | None = None,
    verified_only: bool = False,
) -> PathResult:
    first = session.get(NodeRow, source)
    last = session.get(NodeRow, target)
    if first is None or last is None or first.paper_id != last.paper_id:
        raise NotFound("Path endpoints must exist in one paper")
    query = select(EdgeRow).where(
        EdgeRow.paper_id == first.paper_id,
        EdgeRow.verification_status.not_in(["REJECTED", "STALE", "DISPUTED"]),
    )
    if relation:
        query = query.where(EdgeRow.relation_type == relation)
    if verified_only:
        query = query.where(EdgeRow.verification_status == "VERIFIED")
    valid_nodes = {
        node.id
        for node in session.scalars(select(NodeRow).where(NodeRow.paper_id == first.paper_id))
        if node.verification_status not in INACTIVE
        and (not verified_only or scientific_path_object(session, node))
    }
    if source not in valid_nodes or target not in valid_nodes:
        return PathResult(
            node_ids=[],
            edge_ids=[],
            found=False,
            note="Endpoints lack a current scientific review or are disputed/rejected/stale.",
        )
    adjacency: dict[str, list[EdgeRow]] = {}
    cycles = prerequisite_cycles(
        list(session.scalars(select(EdgeRow).where(EdgeRow.paper_id == first.paper_id)))
    )
    for edge in session.scalars(query):
        if edge.id in cycles:
            continue
        if edge.source_node_id not in valid_nodes or edge.target_node_id not in valid_nodes:
            continue
        try:
            validate_edge(session, edge)
            anchors_for(session, required(session, PaperRow, first.paper_id), edge.provenance)
            if not edge.provenance or (verified_only and not scientific_path_object(session, edge)):
                continue
        except ValueError:
            continue
        adjacency.setdefault(edge.source_node_id, []).append(edge)
    queue: deque[tuple[str, list[str], list[str]]] = deque([(source, [source], [])])
    seen = {source}
    while queue:
        current, nodes, edges = queue.popleft()
        if current == target:
            return PathResult(
                node_ids=nodes,
                edge_ids=edges,
                found=True,
                note="Stored directed path with current scientific reviews."
                if verified_only
                else "Stored candidate path; not a validated scientific explanation.",
            )
        for edge in adjacency.get(current, []):
            if edge.target_node_id not in seen:
                seen.add(edge.target_node_id)
                queue.append(
                    (edge.target_node_id, [*nodes, edge.target_node_id], [*edges, edge.id])
                )
    return PathResult(
        node_ids=[],
        edge_ids=[],
        found=False,
        note="No evidence-backed path is currently stored. Missing relations are not inferred.",
    )


def add_edge(session: Session, paper_id: str, draft: CandidateEdge) -> Edge:
    # Serialize relation changes per paper on SQLite and PostgreSQL before checking cycles.
    session.execute(update(PaperRow).where(PaperRow.id == paper_id).values(title=PaperRow.title))
    paper = session.get(PaperRow, paper_id)
    source = session.get(NodeRow, draft.source_node_id)
    target = session.get(NodeRow, draft.target_node_id)
    if paper is None or source is None or target is None:
        raise NotFound("Graph endpoints not found")
    if source.paper_id != paper_id or target.paper_id != paper_id:
        raise Conflict("Cross-paper edges need an external-source contract")
    if source.id == target.id:
        raise Conflict("Self relations are not permitted")
    anchors = anchors_for(session, paper, draft.anchor_ids)
    edge = EdgeRow(
        paper_id=paper_id,
        source_node_id=source.id,
        target_node_id=target.id,
        relation_type=draft.relation_type,
        confidence=draft.confidence,
        verification_status="CANDIDATE",
        provenance=[a.id for a in anchors],
        created_by="manual-annotation",
        epistemic_status=draft.epistemic_status,
    )
    session.add(edge)
    session.flush()
    validate_edge(session, edge)
    if prerequisite_cycles(
        list(session.scalars(select(EdgeRow).where(EdgeRow.paper_id == paper_id)))
    ):
        raise Conflict("Prerequisite relation would create a cycle")
    return Edge.model_validate(edge)


def verify(session: Session, object_id: str, kind: str, request: Verification) -> Node | Edge:
    row = session.get(NodeRow, object_id) if kind == "node" else session.get(EdgeRow, object_id)
    if row is None:
        raise NotFound("Object not found")
    paper = session.get(PaperRow, row.paper_id)
    if (
        paper is None
        or paper.source_hash != request.source_hash
        or row.version != request.expected_version
    ):
        raise Conflict("Stale source hash or object version; review the current evidence")
    if not row.provenance:
        raise Conflict("Scientific verification needs evidence")
    anchors_for(session, paper, row.provenance)
    session.execute(update(PaperRow).where(PaperRow.id == paper.id).values(title=PaperRow.title))
    if kind == "node" and isinstance(row, NodeRow) and row.type == "PAPER":
        raise Conflict("Paper identity is not a scientific claim")
    if isinstance(row, NodeRow):
        Node.model_validate(row)
        scientific_object(session, row)
    if request.decision == "VERIFIED":
        if request.scope == ReviewScope.SOURCE_ATTRIBUTION:
            if (
                not isinstance(row, NodeRow)
                or row.epistemic_status not in {"PAPER_EXPLICIT", "AUTHOR_CLAIM"}
                or not any(row.text in a.text for a in anchors_for(session, paper, row.provenance))
            ):
                raise Conflict(
                    "Source review verifies literal attribution only; relationships require scientific review"
                )
        if isinstance(row, EdgeRow):
            validate_edge(session, row)
            if prerequisite_cycles(
                list(session.scalars(select(EdgeRow).where(EdgeRow.paper_id == paper.id))),
                include_edge_id=row.id,
            ):
                raise Conflict("Scientific review cannot accept prerequisite cycles")
            endpoints = [
                required(session, NodeRow, row.source_node_id),
                required(session, NodeRow, row.target_node_id),
            ]
            if any(n.verification_status in INACTIVE for n in endpoints):
                raise Conflict("Scientific relationship has a disputed/rejected/stale endpoint")
    evidence_fingerprint = fingerprint(session, row)
    model = NodeRow if kind == "node" else EdgeRow
    result = session.execute(
        update(model)
        .where(model.id == object_id, model.version == request.expected_version)
        .values(
            verification_status=request.decision,
            version=request.expected_version + 1,
            updated_at=timestamp(),
            verification_scope=request.scope,
        )
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise Conflict("Concurrent verification; reload current evidence")
    session.add(
        VerificationRow(
            paper_id=paper.id,
            object_id=row.id,
            object_kind=kind,
            reviewer=request.reviewer,
            decision=request.decision,
            reason=request.reason,
            source_hash=paper.source_hash,
            object_version=request.expected_version,
            scope=request.scope,
            scientific_basis=request.scientific_basis,
            evidence_fingerprint=evidence_fingerprint,
        )
    )
    session.flush()
    session.refresh(row)
    return node_contract(session, row) if isinstance(row, NodeRow) else edge_contract(session, row)
