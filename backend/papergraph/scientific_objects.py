"""First-class node subtypes; all relations are projections of canonical edges."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .errors import Conflict
from .models import ClaimRow, EdgeRow, EquationRow, FigureRow, NodeRow, PaperRow
from .provenance import anchors_for
from .schemas import (
    Claim,
    Equation,
    Figure,
    ScientificObject,
    ScientificStatement,
    ScientificSymbol,
)
from .source_patterns import equation_number, figure_number

CLAIM_TYPES = {"CLAIM", "RESULT", "CONCLUSION", "HYPOTHESIS"}


def ensure_scientific_object(session: Session, node: NodeRow) -> None:
    """Persist only observed source fields. Unknown analyses stay null/empty."""
    if not node.provenance:
        return
    if node.type in CLAIM_TYPES and session.get(ClaimRow, node.id) is None:
        session.add(
            ClaimRow(node_id=node.id, source_anchor_id=node.provenance[0], claim_type=node.type)
        )
    elif node.type == "EQUATION" and session.get(EquationRow, node.id) is None:
        session.add(
            EquationRow(
                node_id=node.id,
                source_anchor_id=node.provenance[0],
                equation_number=equation_number(node.text),
            )
        )
    elif node.type == "FIGURE" and session.get(FigureRow, node.id) is None:
        session.add(
            FigureRow(
                node_id=node.id,
                source_anchor_id=node.provenance[0],
                figure_number=figure_number(node.text),
            )
        )
    session.flush()


def scientific_object(session: Session, node: NodeRow) -> ScientificObject | None:
    model = (
        ClaimRow
        if node.type in CLAIM_TYPES
        else EquationRow
        if node.type == "EQUATION"
        else FigureRow
        if node.type == "FIGURE"
        else None
    )
    if model is None:
        return None
    obj: ClaimRow | EquationRow | FigureRow | None
    if node.type in CLAIM_TYPES:
        obj = session.get(ClaimRow, node.id)
    elif node.type == "EQUATION":
        obj = session.get(EquationRow, node.id)
    else:
        obj = session.get(FigureRow, node.id)
    paper = session.get(PaperRow, node.paper_id)
    if obj is None or paper is None or obj.source_anchor_id not in node.provenance:
        raise Conflict("Scientific object is missing or disconnected from node provenance")
    anchors_for(session, paper, [obj.source_anchor_id])
    edges = list(
        session.scalars(
            select(EdgeRow).where(
                EdgeRow.paper_id == node.paper_id,
                (EdgeRow.source_node_id == node.id) | (EdgeRow.target_node_id == node.id),
                EdgeRow.verification_status.not_in(["REJECTED", "DISPUTED", "STALE"]),
            )
        )
    )

    def outgoing(*relations: str) -> list[str]:
        return sorted(
            {
                e.target_node_id
                for e in edges
                if e.source_node_id == node.id and e.relation_type in relations
            }
        )

    def incoming(*relations: str) -> list[str]:
        return sorted(
            {
                e.source_node_id
                for e in edges
                if e.target_node_id == node.id and e.relation_type in relations
            }
        )

    def assumed(kind: str) -> list[str]:
        return [
            key
            for key in outgoing("ASSUMES")
            if (target := session.get(NodeRow, key)) is not None and target.type == kind
        ]

    def statements(
        raw: list[dict[str, object]], statuses: set[str] | None = None
    ) -> list[ScientificStatement]:
        values = [ScientificStatement.model_validate(value) for value in raw]
        for value in values:
            anchors_for(session, paper, value.anchor_ids)
            if statuses is not None and value.epistemic_status not in statuses:
                raise Conflict(
                    "Scientific interpretation is assigned to the wrong evidence channel"
                )
            if value.epistemic_status in {"PAPER_EXPLICIT", "AUTHOR_CLAIM"} and not any(
                value.text in a.text for a in anchors_for(session, paper, value.anchor_ids)
            ):
                raise Conflict("Attributed analysis does not match source wording")
        return values

    if isinstance(obj, ClaimRow):
        if obj.support_strength != "NOT_ASSESSED":
            raise Conflict("Claim support assessment is not implemented")
        return Claim(
            node_id=node.id,
            source_anchor_id=obj.source_anchor_id,
            claim_type=obj.claim_type,
            qualifiers=obj.qualifiers,
            support_strength="NOT_ASSESSED",
            assumption_node_ids=assumed("ASSUMPTION"),
            evidence_node_ids=sorted(
                set(incoming("SUPPORTS", "EVIDENCE_FOR") + outgoing("SUPPORTED_BY"))
            ),
        )
    if isinstance(obj, EquationRow):
        symbols = [ScientificSymbol.model_validate(value) for value in obj.symbols]
        for symbol in symbols:
            statements([symbol.definition.model_dump()])
        mathematical = (
            statements([obj.mathematical_meaning])[0] if obj.mathematical_meaning else None
        )
        physical = statements([obj.physical_meaning])[0] if obj.physical_meaning else None
        return Equation(
            node_id=node.id,
            source_anchor_id=obj.source_anchor_id,
            original_expression=node.text,
            equation_number=obj.equation_number,
            normalized_expression=obj.normalized_expression,
            latex=obj.latex,
            symbols=symbols,
            mathematical_meaning=mathematical,
            physical_meaning=physical,
            definition_node_ids=incoming("DEFINES"),
            assumption_node_ids=assumed("ASSUMPTION"),
            approximation_node_ids=assumed("APPROXIMATION"),
            derivation_edge_ids=sorted(
                e.id
                for e in edges
                if e.relation_type in {"DERIVES_FROM", "MATHEMATICALLY_DERIVES_FROM"}
            ),
            used_by_node_ids=incoming("USES", "APPLIES"),
        )
    if obj.visual_anchor_id or obj.visual_observations:
        raise Conflict(
            "Visual-region evidence requires an image-region parser contract; text blocks cannot establish it"
        )
    return Figure(
        node_id=node.id,
        source_anchor_id=obj.source_anchor_id,
        figure_number=obj.figure_number,
        caption_explicit=node.text,
        visual_anchor_id=obj.visual_anchor_id,
        surrounding_text=statements(obj.surrounding_text, {"PAPER_EXPLICIT", "AUTHOR_CLAIM"}),
        visual_observations=statements(obj.visual_observations, {"OBSERVED_DATA"}),
        interpretations=statements(obj.interpretations, {"AI_INTERPRETATION", "AI_HYPOTHESIS"}),
        observation_node_ids=outgoing("PRODUCES", "RESULTS_IN"),
        claim_node_ids=outgoing("SUPPORTS", "EVIDENCE_FOR"),
    )
