import re
from dataclasses import dataclass

from .ontology import EpistemicStatus, Layer, NodeType
from .parser import ParsedPage
from .source_patterns import TEMPLATE_HEADER, equation_number, figure_number
from .text_search import searchable


@dataclass(frozen=True)
class EntityCandidate:
    type: NodeType
    layer: Layer
    text: str
    epistemic_status: EpistemicStatus
    reason: str
    source_blocks: tuple[tuple[int, int], ...] = ()


def extract(
    text: str, heading: bool, method_section: bool = False, section_titles: tuple[str, ...] = ()
) -> list[EntityCandidate]:
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
        titles = section_titles or tuple(
            t for t in text.splitlines() if not TEMPLATE_HEADER.fullmatch(t.strip())
        )
        return [
            EntityCandidate(
                NodeType.SECTION,
                Layer.SOURCE,
                title,
                EpistemicStatus.PAPER_EXPLICIT,
                "Source body heading candidate; boundaries and hierarchy are not verified.",
            )
            for title in titles
        ]
    if section_titles and not caption:
        candidates.extend(
            EntityCandidate(
                NodeType.SECTION,
                Layer.SOURCE,
                title,
                EpistemicStatus.PAPER_EXPLICIT,
                "Body heading observed inside an original text block; hierarchy unverified.",
            )
            for title in section_titles
        )
        # Only strip a literal leading heading. The original source block is retained.
        for title in section_titles:
            if text.startswith(title + "\n"):
                text = text[len(title) + 1 :]
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
            background = re.search(
                r"^(although|while) .+ (is capable|can|has been)\b", clean
            ) and not re.search(r"\b(we|our|this work|this study)\b", clean)
            if not background:
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
            r"\b(our complete device integrates|the complete .+ integrates|our device .+ consists|device (structure|stack) .+ (consists|comprises)|capacitor .+ comprised)\b",
            clean,
        ):
            node_type = NodeType.DEVICE
        elif not caption and re.search(
            r"\bwe (?:\w+ ){0,3}(?:extract(?:ed)?|explore[ds]?|investigat(?:e[ds]?|ing)|examin(?:e[ds]?|ing)|stud(?:y|ied))\b.+\b(as a function of|relationship|correlation|dependence)\b",
            clean,
        ):
            node_type = NodeType.RELATIONSHIP_ANALYSIS
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
        elif (
            method_section
            and not caption
            and re.search(
                r"\b(?:was|were) (?:\w+ ){0,3}(?:deposited|patterned|etched|fabricated|transferred|exfoliated|picked up|removed|cleaned|cladded|polished|assembled|grown|annealed|heated|cooled|immersed)\b|\b(?:after|following) (?:the )?(?:transfer|polishing|etching|deposition)\b|\b(?:lithography|etching|deposition|transfer|processing) (?:was|were) (?:used|performed)\b",
                clean,
            )
        ):
            node_type = NodeType.METHOD
        if node_type:
            candidates.append(
                EntityCandidate(
                    node_type,
                    Layer.SEMANTIC
                    if node_type
                    in {NodeType.METHOD, NodeType.DEFINITION, NodeType.RELATIONSHIP_ANALYSIS}
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


def document_candidates(pages: list[ParsedPage]) -> dict[tuple[int, int], list[EntityCandidate]]:
    """Compile fabrication and characterization separately under Methods headings.

    A multi-block PROCESS is a labeled compilation of literal excerpts, not an
    inferred recipe/order or a copied review summary. Its epistemic status reflects
    the extractor's grouping. Source blocks and their individual quotes stay intact.
    """
    result: dict[tuple[int, int], list[EntityCandidate]] = {}
    methods = False
    section_purpose = "fabrication/processing"
    group: list[tuple[tuple[int, int], list[str]]] = []
    characterization: list[tuple[tuple[int, int], list[str]]] = []
    compilations: list[tuple[str, EntityCandidate]] = []

    def flush(purpose: str = "fabrication/processing") -> None:
        selected = group if purpose == "fabrication/processing" else characterization
        if sum(len(excerpts) for _, excerpts in selected) >= (
            2 if purpose == "fabrication/processing" else 1
        ):
            keys = tuple(k for k, _ in selected)
            compilations.append(
                (
                    purpose,
                    EntityCandidate(
                        NodeType.PROCESS,
                        Layer.SEMANTIC,
                        "\n".join(t for _, excerpts in selected for t in excerpts),
                        EpistemicStatus.AI_INTERPRETATION,
                        f"Source-excerpt compilation of {purpose} under a Methods heading. "
                        "Characterization includes preparation of the stated measurement samples; "
                        "Grouping is an extractor interpretation; no missing steps or execution order inferred.",
                        keys,
                    ),
                )
            )
        selected.clear()

    def heading_purpose(text: str) -> str:
        clean = searchable(text)
        if re.search(r"\b(fabrication|preparation|synthesis|processing)\b", clean):
            return "fabrication/processing"
        if re.search(
            r"\b(characteri[sz]ation|measurements?|spectroscopy|microscopy|testing)\b", clean
        ):
            return "characterization and measurement-sample preparation"
        return "fabrication/processing"

    def characterization_activity(text: str) -> bool:
        return bool(
            re.search(
                r"\b(spectra|resistance|thickness|properties|response|measurements?|characteri[sz]ation|microscopy|mapping|spectroscopy|current.voltage|imaging)\b.*\b(was|were|is|are)\b.*\b(acquired|measured|characteri[sz]ed|verified|determined|performed|collected)\b",
                searchable(text),
            )
        )

    for page in pages:
        for block in page.blocks:
            key = (page.number, block.order)
            titles = block.section_titles or ((block.text,) if block.kind == "heading" else ())
            if titles:
                flush()
                flush("characterization and measurement-sample preparation")
                section_purpose = heading_purpose(" ".join(titles))
                if any(
                    re.fullmatch(
                        r"(?:\d+[. ]+)?(?:materials and |experimental )?methods",
                        " ".join(t.split()).casefold(),
                    )
                    for t in titles
                ):
                    methods = True
                elif any(
                    re.match(
                        r"(?:references|acknowledg|data availability|code availability|author contributions|results|discussion|conclusions)\b",
                        " ".join(t.split()).casefold(),
                    )
                    for t in titles
                ):
                    methods = False
            elif (
                methods
                and block.kind == "paragraph"
                and 5 <= len(block.text.strip()) < 160
                and not re.search(r"[.!?;:=]", block.text)
            ):
                # A possible unrecognized subsection label is a conservative grouping
                # boundary. It does not create a SECTION or infer heading hierarchy.
                flush()
                flush("characterization and measurement-sample preparation")
                section_purpose = heading_purpose(block.text)
            result[key] = (
                []
                if block.kind in {"header", "panel_label"}
                else extract(
                    block.text,
                    block.kind == "heading",
                    methods,
                    block.section_titles,
                )
            )
            excerpts = [
                c.text
                for c in result[key]
                if c.type == NodeType.METHOD
                and re.search(
                    r"\b(?:deposited|patterned|etched|fabricated|transferred|exfoliated|picked up|removed|cleaned|cladded|polished|assembled|grown|annealed|immersed|oxidation|etching|lithography)\b",
                    searchable(c.text),
                )
            ]
            if (
                group
                and block.kind == "paragraph"
                and not titles
                and not re.search(r"[.!?]$", group[-1][1][-1].rstrip())
            ):
                # Retain the literal continuation of a selected sentence split by
                # source blocks. Both anchors are kept; no missing wording inferred.
                continuation = re.split(r"(?<=[.!?])\s+(?=[A-Z])", block.text)[0]
                if continuation not in excerpts:
                    excerpts.insert(0, continuation)
            if methods and block.kind == "paragraph":
                sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z]|[a-z](?:[\s,.–]|$))", block.text)
                paragraph_characterization = characterization_activity(sentences[0])
                if paragraph_characterization:
                    # The paragraph explicitly states a measurement purpose. Its
                    # sample/contact preparation must not join device fabrication.
                    flush()
                    flush("characterization and measurement-sample preparation")
                fabrication_excerpts = []
                characterization_excerpts = []
                measurement_context = False
                for sentence in sentences:
                    if paragraph_characterization or section_purpose != "fabrication/processing":
                        if len(searchable(sentence)) >= 35:
                            characterization_excerpts.append(sentence)
                    elif sentence in excerpts:
                        fabrication_excerpts.append(sentence)
                        measurement_context = False
                    elif characterization_activity(sentence):
                        characterization_excerpts.append(sentence)
                        measurement_context = True
                    elif measurement_context and len(searchable(sentence)) >= 35:
                        characterization_excerpts.append(sentence)
                # A cross-block continuation can be shorter than a standalone
                # sentence. Preserve it literally with its second source anchor.
                for excerpt in excerpts:
                    if excerpt not in sentences and section_purpose == "fabrication/processing":
                        fabrication_excerpts.insert(0, excerpt)
                if fabrication_excerpts:
                    if len(group) == 20:
                        flush()
                    group.append((key, fabrication_excerpts))
                if characterization_excerpts:
                    if len(characterization) == 20:
                        flush("characterization and measurement-sample preparation")
                    characterization.append((key, characterization_excerpts))
    flush()
    flush("characterization and measurement-sample preparation")
    # Append fabrication compilations first, preserving existing child indices
    # wherever the individual candidate set and fabrication grouping are unchanged.
    for purpose in (
        "fabrication/processing",
        "characterization and measurement-sample preparation",
    ):
        for candidate_purpose, candidate in compilations:
            if purpose == candidate_purpose:
                result[candidate.source_blocks[0]].append(candidate)
    return result
