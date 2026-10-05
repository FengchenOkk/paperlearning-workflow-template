/* Generated from Pydantic; do not edit. */
export type Id = string;
export type PaperId = string;
export type SpanId = string;
export type PageNumber = number;
export type StartChar = number;
export type EndChar = number;
/**
 * @minItems 4
 * @maxItems 4
 */
export type Bbox = [any, any, any, any];
export type Text = string;
export type SourceHash = string;
export type LocalizationPrecision = "TEXT_BLOCK";
export type SourceNodeId = string;
export type TargetNodeId = string;
export type Relation =
  | "CONTAINS"
  | "MENTIONS"
  | "DEFINES"
  | "DESCRIBES"
  | "DERIVES_FROM"
  | "MATHEMATICALLY_DERIVES_FROM"
  | "DEPENDS_ON"
  | "PREREQUISITE_OF"
  | "USES"
  | "APPLIES"
  | "IMPLEMENTS"
  | "ASSUMES"
  | "APPROXIMATES"
  | "EXPLAINS"
  | "CAUSES"
  | "AFFECTS"
  | "MEASURES"
  | "MEASURED_BY"
  | "SIMULATES"
  | "SIMULATED_BY"
  | "VALIDATES"
  | "VALIDATED_BY"
  | "SUPPORTS"
  | "SUPPORTED_BY"
  | "CONTRADICTS"
  | "COMPARES_WITH"
  | "EXTENDS"
  | "IMPROVES"
  | "MOTIVATES"
  | "ADDRESSES"
  | "SOLVES"
  | "PRODUCES"
  | "RESULTS_IN"
  | "CITES"
  | "CITED_BY"
  | "EVIDENCE_FOR"
  | "PART_OF";
/**
 * @minItems 1
 * @maxItems 20
 */
export type AnchorIds =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ];
export type Confidence = number;
export type EpistemicStatus =
  | "PAPER_EXPLICIT"
  | "PAPER_IMPLICIT"
  | "AUTHOR_CLAIM"
  | "OBSERVED_DATA"
  | "REFERENCE_DERIVED"
  | "BACKGROUND_KNOWLEDGE"
  | "AI_INTERPRETATION"
  | "AI_DERIVATION"
  | "AI_HYPOTHESIS"
  | "UNVERIFIED"
  | "CONFLICTING"
  | "UNKNOWN"
  | "NOT_SPECIFIED_IN_PAPER";
export type NodeType =
  | "PAPER"
  | "SECTION"
  | "PARAGRAPH"
  | "SOURCE_SPAN"
  | "FIGURE"
  | "TABLE"
  | "EQUATION"
  | "REFERENCE"
  | "FIRST_PRINCIPLE"
  | "MATHEMATICAL_CONCEPT"
  | "MATHEMATICAL_THEOREM"
  | "MATHEMATICAL_METHOD"
  | "PHYSICAL_LAW"
  | "PHYSICAL_CONCEPT"
  | "PHYSICAL_QUANTITY"
  | "PHENOMENON"
  | "CHEMICAL_CONCEPT"
  | "MATERIAL"
  | "THEORY"
  | "MODEL"
  | "DEFINITION"
  | "ASSUMPTION"
  | "APPROXIMATION"
  | "METHOD"
  | "ALGORITHM"
  | "PROCESS"
  | "DEVICE"
  | "ARCHITECTURE"
  | "EXPERIMENT"
  | "SIMULATION"
  | "DATASET"
  | "PARAMETER"
  | "METRIC"
  | "RESEARCH_PROBLEM"
  | "MOTIVATION"
  | "RESEARCH_GAP"
  | "HYPOTHESIS"
  | "CLAIM"
  | "OBSERVATION"
  | "EVIDENCE"
  | "RESULT"
  | "CONCLUSION"
  | "CONTRIBUTION"
  | "INNOVATION"
  | "LIMITATION"
  | "OPEN_QUESTION"
  | "PRIOR_WORK";
export type Layer = "SOURCE" | "SEMANTIC" | "ARGUMENT" | "LEARNING" | "CONTEXT";
export type Label = string;
export type Text1 = string;
/**
 * @minItems 1
 * @maxItems 20
 */
export type AnchorIds1 =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ];
export type EpistemicStatus1 =
  | "PAPER_EXPLICIT"
  | "PAPER_IMPLICIT"
  | "AUTHOR_CLAIM"
  | "OBSERVED_DATA"
  | "REFERENCE_DERIVED"
  | "BACKGROUND_KNOWLEDGE"
  | "AI_INTERPRETATION"
  | "AI_DERIVATION"
  | "AI_HYPOTHESIS"
  | "UNVERIFIED"
  | "CONFLICTING"
  | "UNKNOWN"
  | "NOT_SPECIFIED_IN_PAPER";
export type UncertaintyReason = string;
export type Confidence1 = number;
export type Kind = "CLAIM";
export type NodeId = string;
export type SourceAnchorId = string;
export type ClaimType = string;
export type Qualifiers = string[];
export type SupportStrength = "NOT_ASSESSED";
export type AssumptionNodeIds = string[];
export type EvidenceNodeIds = string[];
export type PaperId1 = string;
export type Parser = string;
export type ParserVersion = string;
export type Warnings = string[];
export type Number = number;
export type Width = number;
export type Height = number;
export type Rotation = number;
export type Id1 = string;
export type AnchorId = string;
export type PaperId2 = string;
export type PageNumber1 = number;
export type ReadingOrder = number;
export type Text2 = string;
/**
 * @minItems 4
 * @maxItems 4
 */
export type Bbox1 = [any, any, any, any];
export type Kind1 = "paragraph" | "heading";
export type Spans = Span[];
export type Pages = Page[];
export type Id2 = string;
export type PaperId3 = string;
export type SourceNodeId1 = string;
export type TargetNodeId1 = string;
export type VerificationStatus =
  "CANDIDATE" | "SUPPORTED" | "VERIFIED" | "DISPUTED" | "REJECTED" | "STALE";
export type Confidence2 = number;
export type Provenance = string[];
export type CreatedBy = string;
export type Model = string;
export type PromptVersion = string;
export type CreatedAt = string;
export type UpdatedAt = string;
export type Version = number;
export type EpistemicStatus2 =
  | "PAPER_EXPLICIT"
  | "PAPER_IMPLICIT"
  | "AUTHOR_CLAIM"
  | "OBSERVED_DATA"
  | "REFERENCE_DERIVED"
  | "BACKGROUND_KNOWLEDGE"
  | "AI_INTERPRETATION"
  | "AI_DERIVATION"
  | "AI_HYPOTHESIS"
  | "UNVERIFIED"
  | "CONFLICTING"
  | "UNKNOWN"
  | "NOT_SPECIFIED_IN_PAPER";
export type ReviewScope = "SOURCE_ATTRIBUTION" | "SCIENTIFIC_VALIDITY";
export type ReviewCurrent = boolean | null;
export type Kind2 = "EQUATION";
export type NodeId1 = string;
export type SourceAnchorId1 = string;
export type OriginalExpression = string;
export type EquationNumber = string | null;
export type NormalizedExpression = string | null;
export type Latex = string | null;
export type Symbol = string;
export type Text3 = string;
/**
 * @minItems 1
 */
export type AnchorIds2 = [string, ...string[]];
export type Symbols = ScientificSymbol[];
export type DefinitionNodeIds = string[];
export type AssumptionNodeIds1 = string[];
export type ApproximationNodeIds = string[];
export type DerivationEdgeIds = string[];
export type UsedByNodeIds = string[];
export type Id3 = string;
export type PaperId4 = string;
export type Label1 = string;
export type Text4 = string;
export type Confidence3 = number;
export type UncertaintyReason1 = string;
export type Provenance1 = string[];
export type CreatedBy1 = string;
export type Model1 = string;
export type PromptVersion1 = string;
export type CreatedAt1 = string;
export type UpdatedAt1 = string;
export type Version1 = number;
export type ReviewCurrent1 = boolean | null;
export type Id4 = string;
export type SupportsObjectId = string;
export type EvidenceType = string;
export type SupportType = string;
export type Confidence4 = number;
export type Note = string;
export type Evidence = EvidenceItem[];
export type ScientificObject = Claim | Equation | Figure | null;
export type Kind3 = "FIGURE";
export type NodeId2 = string;
export type SourceAnchorId2 = string;
export type FigureNumber = string | null;
export type CaptionExplicit = string;
export type VisualAnchorId = string | null;
export type SurroundingText = ScientificStatement[];
export type VisualObservations = ScientificStatement[];
export type Interpretations = ScientificStatement[];
export type ObservationNodeIds = string[];
export type ClaimNodeIds = string[];
export type Nodes = Node[];
export type Edges = Edge[];
export type TotalNodes = number;
export type Truncated = boolean;
export type Code = string;
export type ObjectId = string;
export type Severity = "ERROR" | "WARNING";
export type Detail = string;
export type PaperId5 = string;
export type Issues = IntegrityIssue[];
export type StructurallyValid = boolean;
export type ScientificValidity = "NOT_ASSESSED";
export type Id5 = string;
export type PaperId6 = string;
export type JobStatus =
  | "UPLOADED"
  | "PARSING"
  | "PARSED"
  | "ENTITY_EXTRACTION"
  | "GRAPH_BUILDING"
  | "READY"
  | "PARTIAL"
  | "FAILED";
export type Progress = number;
export type Error = string | null;
export type InputHash = string;
export type PipelineVersion = string;
export type Attempt = number;
export type UpdatedAt2 = string;
export type Id6 = string;
export type Title = string;
export type SourceHash1 = string;
export type PageCount = number;
export type CreatedAt2 = string;
export type JobId = string;
export type NodeIds = string[];
export type EdgeIds = string[];
export type Found = boolean;
export type Note1 = string;
export type NodeId3 = string | null;
export type AnchorId1 = string;
export type PageNumber2 = number;
export type Text5 = string;
export type Kind4 = string;
export type Deduplicated = boolean;
export type Decision = "VERIFIED" | "REJECTED" | "DISPUTED";
export type Reviewer = string;
export type Reason = string;
export type SourceHash2 = string;
export type ExpectedVersion = number;
export type ReviewScope1 = "SOURCE_ATTRIBUTION" | "SCIENTIFIC_VALIDITY";
export type ScientificBasis = string | null;

export interface PaperGraphContracts {
  Anchor: Anchor;
  CandidateEdge: CandidateEdge;
  CandidateNode: CandidateNode;
  Claim: Claim;
  Document: Document;
  Edge: Edge;
  EpistemicStatus: EpistemicStatus2;
  Equation: Equation;
  EvidenceBundle: EvidenceBundle;
  EvidenceItem: EvidenceItem;
  Figure: Figure;
  Graph: Graph;
  IntegrityIssue: IntegrityIssue;
  IntegrityReport: IntegrityReport;
  Job: Job;
  JobStatus: JobStatus;
  Layer: Layer;
  Node: Node;
  NodeType: NodeType;
  Page: Page;
  Paper: Paper;
  PathResult: PathResult;
  Relation: Relation;
  ReviewScope: ReviewScope;
  ScientificStatement: ScientificStatement;
  ScientificSymbol: ScientificSymbol;
  SearchHit: SearchHit;
  Span: Span;
  UploadResult: UploadResult;
  Verification: Verification;
  VerificationStatus: VerificationStatus;
}
export interface Anchor {
  id: Id;
  paper_id: PaperId;
  span_id: SpanId;
  page_number: PageNumber;
  start_char: StartChar;
  end_char: EndChar;
  bbox: Bbox;
  text: Text;
  source_hash: SourceHash;
  localization_precision: LocalizationPrecision;
}
export interface CandidateEdge {
  source_node_id: SourceNodeId;
  target_node_id: TargetNodeId;
  relation_type: Relation;
  anchor_ids: AnchorIds;
  confidence?: Confidence;
  epistemic_status?: EpistemicStatus;
}
export interface CandidateNode {
  type: NodeType;
  layer: Layer;
  label: Label;
  text: Text1;
  anchor_ids: AnchorIds1;
  epistemic_status?: EpistemicStatus1;
  uncertainty_reason: UncertaintyReason;
  confidence?: Confidence1;
}
export interface Claim {
  kind?: Kind;
  node_id: NodeId;
  source_anchor_id: SourceAnchorId;
  claim_type: ClaimType;
  qualifiers: Qualifiers;
  support_strength: SupportStrength;
  assumption_node_ids: AssumptionNodeIds;
  evidence_node_ids: EvidenceNodeIds;
}
export interface Document {
  paper_id: PaperId1;
  parser: Parser;
  parser_version: ParserVersion;
  warnings: Warnings;
  pages: Pages;
}
export interface Page {
  number: Number;
  width: Width;
  height: Height;
  rotation: Rotation;
  spans: Spans;
}
export interface Span {
  id: Id1;
  anchor_id: AnchorId;
  paper_id: PaperId2;
  page_number: PageNumber1;
  reading_order: ReadingOrder;
  text: Text2;
  bbox: Bbox1;
  kind: Kind1;
}
export interface Edge {
  id: Id2;
  paper_id: PaperId3;
  source_node_id: SourceNodeId1;
  target_node_id: TargetNodeId1;
  relation_type: Relation;
  verification_status: VerificationStatus;
  confidence: Confidence2;
  provenance: Provenance;
  created_by: CreatedBy;
  model: Model;
  prompt_version: PromptVersion;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  version: Version;
  epistemic_status: EpistemicStatus2;
  verification_scope: ReviewScope | null;
  review_current?: ReviewCurrent;
}
export interface Equation {
  kind?: Kind2;
  node_id: NodeId1;
  source_anchor_id: SourceAnchorId1;
  original_expression: OriginalExpression;
  equation_number: EquationNumber;
  normalized_expression: NormalizedExpression;
  latex: Latex;
  symbols: Symbols;
  mathematical_meaning: ScientificStatement | null;
  physical_meaning: ScientificStatement | null;
  definition_node_ids: DefinitionNodeIds;
  assumption_node_ids: AssumptionNodeIds1;
  approximation_node_ids: ApproximationNodeIds;
  derivation_edge_ids: DerivationEdgeIds;
  used_by_node_ids: UsedByNodeIds;
}
export interface ScientificSymbol {
  symbol: Symbol;
  definition: ScientificStatement;
}
export interface ScientificStatement {
  text: Text3;
  epistemic_status: EpistemicStatus2;
  anchor_ids: AnchorIds2;
}
export interface EvidenceBundle {
  node: Node;
  evidence: Evidence;
  scientific_object: ScientificObject;
}
export interface Node {
  id: Id3;
  paper_id: PaperId4;
  type: NodeType;
  layer: Layer;
  label: Label1;
  text: Text4;
  epistemic_status: EpistemicStatus2;
  verification_status: VerificationStatus;
  confidence: Confidence3;
  uncertainty_reason: UncertaintyReason1;
  provenance: Provenance1;
  created_by: CreatedBy1;
  model: Model1;
  prompt_version: PromptVersion1;
  created_at: CreatedAt1;
  updated_at: UpdatedAt1;
  version: Version1;
  verification_scope: ReviewScope | null;
  review_current?: ReviewCurrent1;
}
export interface EvidenceItem {
  id: Id4;
  supports_object_id: SupportsObjectId;
  evidence_type: EvidenceType;
  support_type: SupportType;
  confidence: Confidence4;
  verification_status: VerificationStatus;
  note: Note;
  anchor: Anchor;
}
export interface Figure {
  kind?: Kind3;
  node_id: NodeId2;
  source_anchor_id: SourceAnchorId2;
  figure_number: FigureNumber;
  caption_explicit: CaptionExplicit;
  visual_anchor_id: VisualAnchorId;
  surrounding_text: SurroundingText;
  visual_observations: VisualObservations;
  interpretations: Interpretations;
  observation_node_ids: ObservationNodeIds;
  claim_node_ids: ClaimNodeIds;
}
export interface Graph {
  nodes: Nodes;
  edges: Edges;
  total_nodes: TotalNodes;
  truncated: Truncated;
}
export interface IntegrityIssue {
  code: Code;
  object_id: ObjectId;
  severity?: Severity;
  detail: Detail;
}
export interface IntegrityReport {
  paper_id: PaperId5;
  issues: Issues;
  structurally_valid: StructurallyValid;
  scientific_validity?: ScientificValidity;
}
export interface Job {
  id: Id5;
  paper_id: PaperId6;
  status: JobStatus;
  progress: Progress;
  error: Error;
  input_hash: InputHash;
  pipeline_version: PipelineVersion;
  attempt: Attempt;
  updated_at: UpdatedAt2;
}
export interface Paper {
  id: Id6;
  title: Title;
  source_hash: SourceHash1;
  page_count: PageCount;
  created_at: CreatedAt2;
  job_id: JobId;
}
export interface PathResult {
  node_ids: NodeIds;
  edge_ids: EdgeIds;
  found: Found;
  note: Note1;
}
export interface SearchHit {
  node_id: NodeId3;
  anchor_id: AnchorId1;
  page_number: PageNumber2;
  text: Text5;
  kind: Kind4;
}
export interface UploadResult {
  paper: Paper;
  job: Job;
  deduplicated: Deduplicated;
}
export interface Verification {
  decision: Decision;
  reviewer: Reviewer;
  reason: Reason;
  source_hash: SourceHash2;
  expected_version: ExpectedVersion;
  scope?: ReviewScope1;
  scientific_basis?: ScientificBasis;
}
