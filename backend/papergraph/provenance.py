import hashlib
import json
import math

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .errors import Conflict
from .models import (
    AnchorRow,
    ClaimRow,
    EdgeRow,
    EquationRow,
    FigureRow,
    NodeRow,
    PageRow,
    PaperRow,
    SpanRow,
    VerificationRow,
)
from .schemas import Anchor, SourceNotation


def validated_notation(span: SpanRow) -> list[SourceNotation]:
    try:
        notes = [SourceNotation.model_validate(n) for n in span.notation]
    except ValidationError as error:
        raise Conflict("Invalid source notation metadata") from error
    end = 0
    for n in notes:
        if (
            not end <= n.start_char < n.end_char <= len(span.text)
            or span.text[n.start_char : n.end_char] != n.raw
            or not span.bbox[0] <= n.bbox[0] < n.bbox[2] <= span.bbox[2] + 0.01
            or not span.bbox[1] <= n.bbox[1] < n.bbox[3] <= span.bbox[3] + 0.01
        ):
            raise Conflict("Source notation range/text/geometry does not match its span")
        end = n.end_char
    if any(not title.strip() or title not in span.text for title in span.section_titles):
        raise Conflict("Body heading does not match its source block")
    return notes


def anchor_contract(session: Session, anchor: AnchorRow) -> Anchor:
    span = session.get(SpanRow, anchor.span_id)
    if span is None:
        raise Conflict("Missing source span")
    notes = [
        n.model_copy(
            update={
                "start_char": n.start_char - anchor.start_char,
                "end_char": n.end_char - anchor.start_char,
            }
        )
        for n in validated_notation(span)
        if anchor.start_char <= n.start_char and n.end_char <= anchor.end_char
    ]
    return Anchor.model_validate(anchor).model_copy(
        update={
            "notation": notes,
            "notation_issues": span.notation_issues,
        }
    )


def anchors_for(session: Session, paper: PaperRow, ids: list[str]) -> list[AnchorRow]:
    anchors = []
    for key in dict.fromkeys(ids):
        anchor = session.get(AnchorRow, key)
        if anchor is None or anchor.paper_id != paper.id:
            raise Conflict("Evidence must refer to this paper")
        if anchor.source_hash != paper.source_hash:
            raise Conflict("Evidence source hash is stale")
        span = session.get(SpanRow, anchor.span_id)
        if span is None or span.paper_id != paper.id or span.page_number != anchor.page_number:
            raise Conflict("Evidence span ownership is invalid")
        page = session.get(PageRow, span.page_id)
        if page is None or page.paper_id != paper.id or page.number != anchor.page_number:
            raise Conflict("Evidence page ownership is invalid")
        if not 1 <= page.number <= paper.page_count:
            raise Conflict("Evidence page is outside the parsed document")
        if (
            not 0 <= anchor.start_char < anchor.end_char <= len(span.text)
            or span.text[anchor.start_char : anchor.end_char] != anchor.text
        ):
            raise Conflict("Evidence text does not match its source range")
        if anchor.bbox != span.bbox or anchor.localization_precision != "TEXT_BLOCK":
            raise Conflict("Evidence coordinates do not match the source block")
        validated_notation(span)
        width, height = (
            (page.height, page.width) if page.rotation in {90, 270} else (page.width, page.height)
        )
        box = anchor.bbox
        if (
            page.rotation not in {0, 90, 180, 270}
            or not math.isfinite(width)
            or not math.isfinite(height)
            or not isinstance(box, list)
            or len(box) != 4
            or not all(
                isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
                for x in box
            )
            or not 0 <= box[0] < box[2] <= width + 0.01
            or not 0 <= box[1] < box[3] <= height + 0.01
        ):
            raise Conflict("Evidence bounding box is invalid or outside its page")
        anchors.append(anchor)
    return anchors


def fingerprint(session: Session, row: NodeRow | EdgeRow) -> str:
    paper = session.get(PaperRow, row.paper_id)
    if paper is None:
        raise Conflict("Missing paper")
    anchors = anchors_for(session, paper, row.provenance)
    fields = ["id", "paper_id", "provenance", "version", "created_by", "model", "prompt_version"]
    fields += (
        ["type", "layer", "text", "epistemic_status"]
        if isinstance(row, NodeRow)
        else ["source_node_id", "target_node_id", "relation_type", "epistemic_status"]
    )
    payload: dict[str, object] = {key: getattr(row, key) for key in fields if key != "version"}
    source_records = []
    for a in anchors:
        span = session.get(SpanRow, a.span_id)
        page = session.get(PageRow, span.page_id) if span else None
        if page is None:
            raise Conflict("Missing source page")
        source_records.append(
            {
                "id": a.id,
                "span_id": a.span_id,
                "page": a.page_number,
                "range": [a.start_char, a.end_char],
                "bbox": a.bbox,
                "text": a.text,
                "hash": a.source_hash,
                "page_geometry": [page.width, page.height, page.rotation],
            }
        )
        if span is not None and (span.notation or span.notation_issues):
            # Empty additive fields preserve historical fingerprints. New typography
            # evidence changes the fingerprint and requires a fresh review.
            source_records[-1]["notation"] = span.notation
            source_records[-1]["notation_issues"] = span.notation_issues
        if span is not None and span.section_titles:
            source_records[-1]["section_titles"] = span.section_titles
    payload["anchors"] = source_records
    if isinstance(row, EdgeRow):
        endpoints = []
        for key in (row.source_node_id, row.target_node_id):
            node = session.get(NodeRow, key)
            if node is None or node.paper_id != row.paper_id:
                raise Conflict("Missing relationship endpoint")
            endpoints.append(
                {
                    "id": node.id,
                    "type": node.type,
                    "layer": node.layer,
                    "text": node.text,
                    "epistemic_status": node.epistemic_status,
                    "provenance": node.provenance,
                }
            )
        payload["endpoints"] = endpoints
    if isinstance(row, NodeRow):
        for subtype in (ClaimRow, EquationRow, FigureRow):
            obj = session.get(subtype, row.id)
            if obj is not None:
                payload["scientific_object"] = {
                    column.key: getattr(obj, column.key) for column in subtype.__table__.columns
                }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def current_review(session: Session, row: NodeRow | EdgeRow, scientific: bool = False) -> bool:
    if row.verification_status not in {"VERIFIED", "REJECTED", "DISPUTED"}:
        return False
    paper = session.get(PaperRow, row.paper_id)
    kind = "node" if isinstance(row, NodeRow) else "edge"
    audits = list(
        session.scalars(
            select(VerificationRow).where(
                VerificationRow.object_id == row.id,
                VerificationRow.object_kind == kind,
                VerificationRow.object_version == row.version - 1,
            )
        )
    )
    if paper is None or len(audits) != 1:
        return False
    audit = audits[0]
    try:
        return (
            audit.paper_id == row.paper_id
            and audit.source_hash == paper.source_hash
            and audit.decision == row.verification_status
            and audit.scope == row.verification_scope
            and bool(audit.reviewer.strip())
            and len(audit.reason.strip()) >= 10
            and (
                not scientific
                or (audit.scope == "SCIENTIFIC_VALIDITY" and bool(audit.scientific_basis))
            )
            and audit.evidence_fingerprint == fingerprint(session, row)
        )
    except Conflict:
        return False
