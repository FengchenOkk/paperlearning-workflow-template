"""Structural integrity checks, deliberately not an automatic scientific referee."""

from collections import defaultdict
from typing import cast

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .errors import Conflict, NotFound
from .models import (
    AnchorRow,
    ClaimRow,
    EdgeRow,
    EquationRow,
    EvidenceRow,
    FigureRow,
    NodeRow,
    PaperRow,
    SpanRow,
    VerificationRow,
)
from .ontology import Relation
from .provenance import anchors_for, current_review
from .schemas import Edge, IntegrityIssue, IntegrityReport, Node
from .scientific_objects import scientific_object

INACTIVE = {"REJECTED", "DISPUTED", "STALE"}


def validate_edge(session: Session, edge: EdgeRow) -> None:
    source = session.get(NodeRow, edge.source_node_id)
    target = session.get(NodeRow, edge.target_node_id)
    if (
        source is None
        or target is None
        or source.paper_id != edge.paper_id
        or target.paper_id != edge.paper_id
    ):
        raise Conflict("Invalid or foreign-paper edge endpoints")
    Node.model_validate(source)
    Node.model_validate(target)
    Edge.model_validate(edge)
    scientific_object(session, source)
    scientific_object(session, target)
    if source.id == target.id:
        raise Conflict("Self relations are not permitted")
    if edge.relation_type == "ASSUMES" and target.type not in {"ASSUMPTION", "APPROXIMATION"}:
        raise Conflict("ASSUMES must target an ASSUMPTION or APPROXIMATION")
    if edge.relation_type == "EVIDENCE_FOR" and target.type not in {
        "CLAIM",
        "RESULT",
        "CONCLUSION",
        "HYPOTHESIS",
    }:
        raise Conflict("EVIDENCE_FOR must target an argument claim")
    if edge.relation_type == "CONTAINS" and source.type not in {"PAPER", "SECTION"}:
        raise Conflict("CONTAINS is source structure, not a scientific inference")


def prerequisite_cycles(edges: list[EdgeRow], include_edge_id: str | None = None) -> set[str]:
    """Normalize A DEPENDS_ON B to B → A, then detect directed cycles."""
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in edges:
        if edge.verification_status in INACTIVE and edge.id != include_edge_id:
            continue
        if edge.relation_type == Relation.PREREQUISITE_OF:
            adjacency[edge.source_node_id].append((edge.target_node_id, edge.id))
        elif edge.relation_type == Relation.DEPENDS_ON:
            adjacency[edge.target_node_id].append((edge.source_node_id, edge.id))
    cyclic = set()
    # Iterative reachability avoids recursion limits on large uploaded graphs.
    for start, links in adjacency.items():
        for target, edge_id in links:
            frontier, visited = [target], set()
            while frontier:
                current = frontier.pop()
                if current == start:
                    cyclic.add(edge_id)
                    break
                if current in visited:
                    continue
                visited.add(current)
                frontier.extend(key for key, _ in adjacency.get(current, []))
    return cyclic


def report(session: Session, paper_id: str) -> IntegrityReport:
    paper = session.get(PaperRow, paper_id)
    if paper is None:
        raise NotFound("Paper not found")
    issues: list[IntegrityIssue] = []

    def issue(code: str, key: str, detail: str, warning: bool = False) -> None:
        issues.append(
            IntegrityIssue(
                code=code, object_id=key, detail=detail, severity="WARNING" if warning else "ERROR"
            )
        )

    nodes = list(session.scalars(select(NodeRow).where(NodeRow.paper_id == paper_id)))
    edges = list(session.scalars(select(EdgeRow).where(EdgeRow.paper_id == paper_id)))
    connected = {key for e in edges for key in (e.source_node_id, e.target_node_id)}
    duplicates: dict[tuple[str, str], str] = {}
    for node in nodes:
        try:
            Node.model_validate(node)
            if node.type != "PAPER" and not node.provenance:
                raise Conflict("Paper-derived node has no source provenance")
            anchors_for(session, paper, node.provenance)
            if (
                node.epistemic_status in {"PAPER_EXPLICIT", "AUTHOR_CLAIM"}
                and node.type != "PAPER"
                and not any(
                    node.text in a.text for a in anchors_for(session, paper, node.provenance)
                )
            ):
                raise Conflict("Attributed node text does not match source")
            scientific_object(session, node)
        except (ValueError, TypeError) as error:
            issue("INVALID_NODE", node.id, str(error))
        if node.type != "PAPER" and node.id not in connected:
            issue(
                "ORPHAN_NODE",
                node.id,
                "No stored graph relationship; source attribution alone is not a relationship",
                True,
            )
        key = (node.type, " ".join(node.text.casefold().split()))
        if key in duplicates:
            issue(
                "DUPLICATE_CANDIDATE",
                node.id,
                f"Same type/text as {duplicates[key]}; no automatic merge",
                True,
            )
        duplicates[key] = node.id
    for edge in edges:
        try:
            validate_edge(session, edge)
            if not edge.provenance:
                raise Conflict("Relationship has no evidence anchors")
            anchors_for(session, paper, edge.provenance)
            if (
                edge.verification_status == "VERIFIED"
                and edge.verification_scope != "SCIENTIFIC_VALIDITY"
            ):
                raise Conflict("Verified relationship lacks a scientific review scope")
        except (ValueError, TypeError) as error:
            issue("INVALID_EDGE", edge.id, str(error))
    objects: list[NodeRow | EdgeRow] = [*nodes, *edges]
    for row in objects:
        if row.verification_status in {"VERIFIED", "REJECTED", "DISPUTED"} and not current_review(
            session, row
        ):
            issue(
                "CONFLICTING_VERIFICATION",
                row.id,
                "Missing, duplicate, stale or mismatched review/evidence fingerprint",
            )
        if (
            row.verification_status not in {"VERIFIED", "REJECTED", "DISPUTED"}
            and row.verification_scope is not None
        ):
            issue("CONFLICTING_VERIFICATION", row.id, "Unreviewed status carries a review scope")
    for anchor in session.scalars(select(AnchorRow).where(AnchorRow.paper_id == paper_id)):
        try:
            anchors_for(session, paper, [anchor.id])
        except (ValueError, TypeError) as error:
            issue("INVALID_ANCHOR", anchor.id, str(error))
    for evidence in session.scalars(
        select(EvidenceRow)
        .join(NodeRow, NodeRow.id == EvidenceRow.supports_object_id)
        .where(NodeRow.paper_id == paper_id)
    ):
        owner = session.get(NodeRow, evidence.supports_object_id)
        try:
            anchors_for(session, paper, [evidence.anchor_id])
            if owner is None or evidence.anchor_id not in owner.provenance:
                raise Conflict("Evidence association conflicts with canonical provenance")
        except (ValueError, TypeError) as error:
            issue("INVALID_EVIDENCE", evidence.id, str(error))
    for span in session.scalars(select(SpanRow).where(SpanRow.paper_id == paper_id)):
        if (
            session.scalar(
                select(AnchorRow.id).where(
                    AnchorRow.span_id == span.id, AnchorRow.paper_id == paper_id
                )
            )
            is None
        ):
            issue(
                "UNANCHORED_SOURCE_SPAN", span.id, "Parsed source span has no local source anchor"
            )
    for subtype, kinds in (
        (ClaimRow, {"CLAIM", "RESULT", "CONCLUSION", "HYPOTHESIS"}),
        (EquationRow, {"EQUATION"}),
        (FigureRow, {"FIGURE"}),
    ):
        for obj in session.scalars(
            select(subtype)
            .join(NodeRow, NodeRow.id == subtype.__table__.c.node_id)
            .where(NodeRow.paper_id == paper_id)
        ):
            typed_object = cast(ClaimRow | EquationRow | FigureRow, obj)
            subtype_id = typed_object.node_id
            subtype_node = session.get(NodeRow, subtype_id)
            if subtype_node is None or subtype_node.type not in kinds:
                issue(
                    "INVALID_SUBTYPE",
                    subtype_id,
                    "Scientific subtype is incompatible with canonical node",
                )
    for audit in session.scalars(
        select(VerificationRow).where(VerificationRow.paper_id == paper_id)
    ):
        reviewed: NodeRow | EdgeRow | None = None
        if audit.object_kind == "node":
            reviewed = session.get(NodeRow, audit.object_id)
        elif audit.object_kind == "edge":
            reviewed = session.get(EdgeRow, audit.object_id)
        if (
            reviewed is None
            or reviewed.paper_id != paper_id
            or audit.object_version >= reviewed.version
        ):
            issue(
                "INVALID_REVIEW_REFERENCE", audit.id, "Review refers to an invalid object/version"
            )
    for cycle_id in sorted(prerequisite_cycles(edges)):
        issue("PREREQUISITE_CYCLE", cycle_id, "PREREQUISITE_OF / inverse DEPENDS_ON forms a cycle")
    return IntegrityReport(
        paper_id=paper_id,
        issues=issues,
        structurally_valid=not any(i.severity == "ERROR" for i in issues),
    )


def scientific_path_object(session: Session, row: NodeRow | EdgeRow) -> bool:
    if row.verification_status != "VERIFIED" or not current_review(session, row, scientific=True):
        return False
    try:
        if isinstance(row, NodeRow):
            Node.model_validate(row)
            scientific_object(session, row)
        else:
            validate_edge(session, row)
        return True
    except (Conflict, ValidationError):
        return False
