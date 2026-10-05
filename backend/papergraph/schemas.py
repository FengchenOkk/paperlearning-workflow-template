from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .ontology import (
    EpistemicStatus,
    JobStatus,
    Layer,
    NodeType,
    Relation,
    ReviewScope,
    VerificationStatus,
    valid_layer,
)

Identifier = Annotated[
    str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
]
Confidence = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Coordinate = Annotated[float, Field(allow_inf_nan=False)]
BBox = tuple[Coordinate, Coordinate, Coordinate, Coordinate]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class Anchor(Contract):
    id: Identifier
    paper_id: Identifier
    span_id: Identifier
    page_number: int
    start_char: int
    end_char: int
    bbox: BBox
    text: str
    source_hash: str
    localization_precision: Literal["TEXT_BLOCK"]


class Node(Contract):
    id: Identifier
    paper_id: Identifier
    type: NodeType
    layer: Layer
    label: str
    text: str
    epistemic_status: EpistemicStatus
    verification_status: VerificationStatus
    confidence: Confidence
    uncertainty_reason: str
    provenance: list[Identifier]
    created_by: str
    model: str
    prompt_version: str
    created_at: str
    updated_at: str
    version: int
    verification_scope: ReviewScope | None
    review_current: bool | None = None

    @model_validator(mode="after")
    def check_layer(self) -> "Node":
        if not valid_layer(self.type, self.layer):
            raise ValueError("Node type is incompatible with layer")
        return self


class Edge(Contract):
    id: Identifier
    paper_id: Identifier
    source_node_id: Identifier
    target_node_id: Identifier
    relation_type: Relation
    verification_status: VerificationStatus
    confidence: Confidence
    provenance: list[Identifier]
    created_by: str
    model: str
    prompt_version: str
    created_at: str
    updated_at: str
    version: int
    epistemic_status: EpistemicStatus
    verification_scope: ReviewScope | None
    review_current: bool | None = None


class Graph(Contract):
    nodes: list[Node]
    edges: list[Edge]
    total_nodes: int
    truncated: bool


class Span(Contract):
    id: Identifier
    anchor_id: Identifier
    paper_id: Identifier
    page_number: int
    reading_order: int
    text: str
    bbox: BBox
    kind: Literal["paragraph", "heading"]


class Page(Contract):
    number: int
    width: float
    height: float
    rotation: int
    spans: list[Span]


class Document(Contract):
    paper_id: Identifier
    parser: str
    parser_version: str
    warnings: list[str]
    pages: list[Page]


class Paper(Contract):
    id: Identifier
    title: str
    source_hash: str
    page_count: int
    created_at: str
    job_id: Identifier


class Job(Contract):
    id: Identifier
    paper_id: Identifier
    status: JobStatus
    progress: int
    error: str | None
    input_hash: str
    pipeline_version: str
    attempt: int
    updated_at: str


class UploadResult(Contract):
    paper: Paper
    job: Job
    deduplicated: bool


class EvidenceItem(Contract):
    id: Identifier
    supports_object_id: Identifier
    evidence_type: str
    support_type: str
    confidence: Confidence
    verification_status: VerificationStatus
    note: str
    anchor: Anchor


class ScientificStatement(Contract):
    text: str
    epistemic_status: EpistemicStatus
    anchor_ids: list[Identifier] = Field(min_length=1)


class ScientificSymbol(Contract):
    symbol: str
    definition: ScientificStatement


class Claim(Contract):
    kind: Literal["CLAIM"] = "CLAIM"
    node_id: Identifier
    source_anchor_id: Identifier
    claim_type: str
    qualifiers: list[str]
    support_strength: Literal["NOT_ASSESSED"]
    assumption_node_ids: list[Identifier]
    evidence_node_ids: list[Identifier]


class Equation(Contract):
    kind: Literal["EQUATION"] = "EQUATION"
    node_id: Identifier
    source_anchor_id: Identifier
    original_expression: str
    equation_number: str | None
    normalized_expression: str | None
    latex: str | None
    symbols: list[ScientificSymbol]
    mathematical_meaning: ScientificStatement | None
    physical_meaning: ScientificStatement | None
    definition_node_ids: list[Identifier]
    assumption_node_ids: list[Identifier]
    approximation_node_ids: list[Identifier]
    derivation_edge_ids: list[Identifier]
    used_by_node_ids: list[Identifier]


class Figure(Contract):
    kind: Literal["FIGURE"] = "FIGURE"
    node_id: Identifier
    source_anchor_id: Identifier
    figure_number: str | None
    caption_explicit: str
    visual_anchor_id: Identifier | None
    surrounding_text: list[ScientificStatement]
    visual_observations: list[ScientificStatement]
    interpretations: list[ScientificStatement]
    observation_node_ids: list[Identifier]
    claim_node_ids: list[Identifier]


ScientificObject = Claim | Equation | Figure


class EvidenceBundle(Contract):
    node: Node
    evidence: list[EvidenceItem]
    scientific_object: ScientificObject | None


class SearchHit(Contract):
    node_id: Identifier | None
    anchor_id: Identifier
    page_number: int
    text: str
    kind: str


class CandidateNode(Contract):
    type: NodeType
    layer: Layer
    label: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=10000)
    anchor_ids: list[Identifier] = Field(min_length=1, max_length=20)
    epistemic_status: EpistemicStatus = EpistemicStatus.AI_INTERPRETATION
    uncertainty_reason: str = Field(min_length=1, max_length=2000)
    confidence: Confidence = 0.5

    @model_validator(mode="after")
    def check_layer(self) -> "CandidateNode":
        if not valid_layer(self.type, self.layer):
            raise ValueError("Node type is incompatible with layer")
        return self


class CandidateEdge(Contract):
    source_node_id: Identifier
    target_node_id: Identifier
    relation_type: Relation
    anchor_ids: list[Identifier] = Field(min_length=1, max_length=20)
    confidence: Confidence = 0.5
    epistemic_status: EpistemicStatus = EpistemicStatus.AI_INTERPRETATION


class Verification(Contract):
    decision: Literal["VERIFIED", "REJECTED", "DISPUTED"]
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=10, max_length=5000)
    source_hash: str
    expected_version: int = Field(ge=1)
    scope: ReviewScope = ReviewScope.SOURCE_ATTRIBUTION
    scientific_basis: str | None = Field(default=None, min_length=20, max_length=10000)

    @model_validator(mode="after")
    def require_scientific_basis(self) -> "Verification":
        if not self.reviewer.strip() or len(self.reason.strip()) < 10:
            raise ValueError("Review needs an identifiable reviewer and a substantive reason")
        if (
            self.decision == "VERIFIED"
            and self.scope == ReviewScope.SCIENTIFIC_VALIDITY
            and (not self.scientific_basis or len(self.scientific_basis.strip()) < 20)
        ):
            raise ValueError("Scientific review requires an explicit evidence assessment")
        return self


class PathResult(Contract):
    node_ids: list[Identifier]
    edge_ids: list[Identifier]
    found: bool
    note: str


class IntegrityIssue(Contract):
    code: str
    object_id: str
    severity: Literal["ERROR", "WARNING"] = "ERROR"
    detail: str


class IntegrityReport(Contract):
    paper_id: Identifier
    issues: list[IntegrityIssue]
    structurally_valid: bool
    scientific_validity: Literal["NOT_ASSESSED"] = "NOT_ASSESSED"
