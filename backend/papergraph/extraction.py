import re
from dataclasses import dataclass

from .ontology import EpistemicStatus, Layer, NodeType
from .source_patterns import equation_number, figure_number
from .text_search import searchable


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
    candidates = []
    caption = figure_number(text) is not None
    if caption:
        candidates.extend(
            [
                EntityCandidate(
                    NodeType.FIGURE,
                    Layer.SOURCE,
                    text,
                    EpistemicStatus.PAPER_EXPLICIT,
                    "Caption candidate only. Axes, curves and claim support have not been analyzed.",
                )
            ]
        )
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
    if (
        len(text) < 700
        and equation_number(text) is not None
        and not caption
        and re.search(r"[=∑∫≤≥]", text)
    ):
        return [
            EntityCandidate(
                NodeType.EQUATION,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Numbered equation candidate. Exact PDF text is preserved; notation, LaTeX and derivation are not verified.",
            )
        ]
    if heading and not caption:
        return [
            EntityCandidate(
                NodeType.SECTION,
                Layer.SOURCE,
                text,
                EpistemicStatus.PAPER_EXPLICIT,
                "Heading classification is a font/length heuristic; section boundaries are not verified.",
            )
        ]
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z]|[a-z](?:[\s,.–]|$))", text):
        clean = searchable(sentence)
        if len(clean) < 35 or len(clean) > 1200:
            continue
        node_type: NodeType | None = None
        if re.search(r"\b(assum(?:e[sd]?|ing|ptions?))\b", clean):
            node_type = NodeType.ASSUMPTION
        elif re.search(r"\b(is defined as|we define|where \w+ is .+ and \w+ is)\b", clean):
            node_type = NodeType.DEFINITION
        elif re.search(
            r"\b(uncertainties|suffers from|major limitation|stability issues)\b", clean
        ):
            node_type = NodeType.LIMITATION
        elif not caption and re.search(
            r"\b(but .+ suffer|development .+ requires|remains a critical challenge)\b", clean
        ):
            node_type = NodeType.RESEARCH_PROBLEM
        elif not caption and re.search(
            r"\b(simulations? were (carried out|performed)|were modeled in|calculations were performed)\b",
            clean,
        ):
            node_type = NodeType.SIMULATION
        elif not caption and re.search(
            r"\b(our complete device integrates|the complete .+ integrates)\b", clean
        ):
            node_type = NodeType.DEVICE
        elif not caption and re.search(
            r"\b(we (propose|introduce|present|use|employed|fabricated)|we (then |further )?extract(?:ed)?|we address .+ by|here we .+ by|treatment was performed|structures were fully relaxed|the (proposed|key) (method|idea)|is a technique|our (method|approach))\b",
            clean,
        ):
            node_type = NodeType.METHOD
        elif not caption and re.search(
            r"\b(we (show|find|demonstrate|observe)|results (show|demonstrate|reveal)|achieves?|outperforms?|reaches|\w+ exhibits? a (low|high)|\w+ show(?:s)? (a|an|current|no|negligible|excellent)|the average .+ was|no obvious degradation .+ observed|was calculated to be)\b",
            clean,
        ):
            node_type = NodeType.RESULT
        elif not caption and re.search(
            r"(?i)\b(we (argue|conclude|claim)|this (shows|suggests|demonstrates))\b", clean
        ):
            node_type = NodeType.CLAIM
        if node_type:
            candidates.append(
                EntityCandidate(
                    node_type,
                    Layer.SEMANTIC
                    if node_type in {NodeType.METHOD, NodeType.DEFINITION}
                    or node_type
                    in {
                        NodeType.ASSUMPTION,
                        NodeType.RESEARCH_PROBLEM,
                        NodeType.SIMULATION,
                        NodeType.DEVICE,
                    }
                    else Layer.ARGUMENT,
                    sentence,
                    EpistemicStatus.AUTHOR_CLAIM,
                    "Rule-based attribution candidate. Source wording is exact; classification and scientific support need review.",
                )
            )
    return candidates
