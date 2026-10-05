import re
from dataclasses import dataclass

from .ontology import EpistemicStatus, Layer, NodeType


@dataclass(frozen=True)
class EntityCandidate:
    type: NodeType
    layer: Layer
    text: str
    epistemic_status: EpistemicStatus
    reason: str


def extract(text: str, heading: bool) -> list[EntityCandidate]:
    """Conservative attribution only; no inferred scientific relations."""
    compact = " ".join(text.split())
    if re.match(r"(?i)^fig(?:ure)?\.?\s*\d+\s*[:.\-]", compact):
        return [
            EntityCandidate(
                NodeType.FIGURE,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Caption candidate only. Axes, curves and claim support have not been analyzed.",
            )
        ]
    if re.match(r"(?i)^table\s+\d+\s*[:.\-]", compact):
        return [
            EntityCandidate(
                NodeType.TABLE,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Caption candidate only; table cells and units have not been reconstructed.",
            )
        ]
    if len(text) < 700 and re.search(r"\(\d+[a-z]?\)\s*$", compact) and re.search(r"[=∑∫≤≥]", text):
        return [
            EntityCandidate(
                NodeType.EQUATION,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Numbered equation candidate. Exact PDF text is preserved; notation, LaTeX and derivation are not verified.",
            )
        ]
    candidates = []
    if heading:
        return [
            EntityCandidate(
                NodeType.SECTION,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Heading classification is a font/length heuristic; section boundaries are not verified.",
            )
        ]
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
        clean = " ".join(sentence.split())
        if len(clean) < 35 or len(clean) > 1200:
            continue
        node_type: NodeType | None = None
        if re.search(
            r"(?i)\b(we (propose|introduce|present|use)|the (proposed|key) (method|idea)|is a technique|our (method|approach))\b",
            clean,
        ):
            node_type = NodeType.METHOD
        elif re.search(
            r"(?i)\b(we (show|find|demonstrate|observe)|results (show|demonstrate)|achieves?|outperforms?)\b",
            clean,
        ):
            node_type = NodeType.RESULT
        elif re.search(r"(?i)\b(is defined as|we define)\b", clean):
            node_type = NodeType.DEFINITION
        elif re.search(
            r"(?i)\b(we (argue|conclude|claim)|this (shows|suggests|demonstrates))\b", clean
        ):
            node_type = NodeType.CLAIM
        if node_type:
            candidates.append(
                EntityCandidate(
                    node_type,
                    Layer.SEMANTIC
                    if node_type in {NodeType.METHOD, NodeType.DEFINITION}
                    else Layer.ARGUMENT,
                    sentence,
                    EpistemicStatus.AUTHOR_CLAIM,
                    "Rule-based attribution candidate. Source wording is exact; classification and scientific support need review.",
                )
            )
    return candidates
