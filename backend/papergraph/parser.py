import math
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import Protocol

import pymupdf

from .notation import block_notation
from .notation import glyph_text as glyph_text
from .schemas import BBox, SourceNotation
from .source_patterns import BODY_SECTION, EQUATION, TEMPLATE_HEADER, figure_number


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    bbox: BBox
    kind: str
    order: int
    font_size: float = 0
    notation: list[SourceNotation] = field(default_factory=list)
    notation_issues: list[str] = field(default_factory=list)
    section_titles: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedPage:
    number: int
    width: float
    height: float
    rotation: int
    blocks: list[ParsedBlock]


class DocumentParser(Protocol):
    name: str
    version: str

    def pages(self, content: bytes, max_pages: int) -> Iterator[ParsedPage]: ...


def join_fragments(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    """Join spatially aligned caption columns and overlapping display-math fragments.

    The union remains TEXT_BLOCK precision. No equation algebra, image-region anchor
    or semantic linkage is inferred. Source glyph order within each fragment is kept.
    """
    groups: dict[int, list[int]] = {}
    claimed: set[int] = set()
    for i, block in enumerate(blocks):
        caption = figure_number(block.text) is not None
        numbered = any(EQUATION.fullmatch(line.strip()) for line in block.text.splitlines())
        if i in claimed or not (caption or numbered):
            continue
        peers = [i]
        for j, other in enumerate(blocks):
            if j == i or j in claimed:
                continue
            left, top, right, bottom = block.bbox
            x0, y0, x1, y1 = other.bbox
            if caption:
                aligned = (
                    0 <= x0 - right <= 35
                    and abs(top - y0) < 3
                    and abs(bottom - y1) < 12
                    and abs(block.font_size - other.font_size) < 0.6
                    and len(other.text) > 50
                    and figure_number(other.text) is None
                )
            else:
                aligned = (
                    min(bottom, y1) > max(top, y0)
                    and left - 30 <= x0 < right - 20
                    and x1 <= right
                    and len(other.text) < 100
                )
            if aligned:
                peers.append(j)
        if numbered and not any(re.search(r"[=∑∫≤≥]", blocks[j].text) for j in peers):
            continue
        if len(peers) > 1:
            groups[i] = peers
            claimed.update(peers)
    output: list[ParsedBlock] = []
    for i, block in enumerate(blocks):
        if i in claimed and i not in groups:
            continue
        fragments = [blocks[j] for j in groups.get(i, [i])]
        if len(fragments) > 1:
            fragments.sort(key=lambda b: b.bbox[0])
            text = "\n".join(b.text for b in fragments)
            box = (
                min(b.bbox[0] for b in fragments),
                min(b.bbox[1] for b in fragments),
                max(b.bbox[2] for b in fragments),
                max(b.bbox[3] for b in fragments),
            )
            notes: list[SourceNotation] = []
            offset = 0
            for fragment in fragments:
                notes.extend(
                    n.model_copy(
                        update={
                            "start_char": n.start_char + offset,
                            "end_char": n.end_char + offset,
                        }
                    )
                    for n in fragment.notation
                )
                offset += len(fragment.text) + 1
            block = ParsedBlock(
                text,
                box,
                "paragraph",
                len(output),
                max(b.font_size for b in fragments),
                notes,
                [issue for b in fragments for issue in b.notation_issues],
            )
        output.append(replace(block, order=len(output)))
    return output


class MuPDFParser:
    name = "pymupdf"
    version = str(pymupdf.VersionBind) + "+layout-v3-notation"

    def pages(self, content: bytes, max_pages: int) -> Iterator[ParsedPage]:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("ENCRYPTED_PDF")
            if len(document) > max_pages:
                raise ValueError("PAGE_LIMIT_EXCEEDED")
            if not len(document):
                raise ValueError("EMPTY_PDF")
            parsed_pages = []
            for number, page in enumerate(document, 1):
                blocks: list[ParsedBlock] = []
                layout = page.get_text(
                    "rawdict",
                    sort=True,
                    flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES,
                )["blocks"]
                body_fonts: Counter[float] = Counter()
                for block in layout:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            literal = "".join(c["c"] for c in span["chars"])
                            if len(literal.strip()) >= 35:
                                body_fonts[round(float(span["size"]), 1)] += len(literal)
                body_size = body_fonts.most_common(1)[0][0] if body_fonts else 0
                rules = []
                for drawing in page.get_drawings():
                    rect = drawing["rect"]
                    # Filled thin rectangles and single horizontal strokes only. Paths
                    # with several segments may be figures, tables or radical layout.
                    if (
                        len(drawing["items"]) == 1
                        and drawing["items"][0][0] in {"re", "l"}
                        and 0 <= rect.height <= 0.9
                        and 0.5 <= rect.width <= 20
                    ):
                        rules.append(tuple(rect))
                for block in layout:
                    if block["type"] != 0:
                        continue
                    lines = block.get("lines", [])
                    text, notation, notation_issues = block_notation(block, rules)
                    if not text.strip():
                        continue
                    sizes = [float(span["size"]) for line in lines for span in line["spans"]]
                    bold = any(
                        int(span["flags"]) & 16 or str(span["font"]).endswith(".B")
                        for line in lines
                        for span in line["spans"]
                    )
                    section_titles = []
                    for line in lines:
                        literal = "".join(
                            glyph_text("".join(c["c"] for c in s["chars"]), int(s["flags"]))
                            for s in line["spans"]
                        )
                        label = " ".join(literal.split())
                        line_bold = any(
                            int(s["flags"]) & 16 or str(s["font"]).endswith(".B")
                            for s in line["spans"]
                        )
                        if (
                            BODY_SECTION.fullmatch(label)
                            or line_bold
                            and 5 <= len(label) < 140
                            and not re.search(r"[.!?:]$", label)
                            and max(float(s["size"]) for s in line["spans"]) >= body_size - 0.5
                        ):
                            if not TEMPLATE_HEADER.fullmatch(label):
                                section_titles.append(literal)
                    heading = (
                        5 <= len(text) < 180
                        and block["bbox"][1] < page.mediabox.height * 0.94
                        and (
                            max(sizes, default=0) >= 14
                            or any(
                                BODY_SECTION.fullmatch(" ".join(t.split())) for t in section_titles
                            )
                            or bold
                            and max(sizes, default=0) >= body_size - 0.5
                        )
                    )
                    box = block["bbox"]
                    compact = " ".join(text.split())
                    kind = "heading" if heading else "paragraph"
                    if box[1] < page.mediabox.height * 0.12 and TEMPLATE_HEADER.fullmatch(compact):
                        kind = "header"
                    elif re.fullmatch(
                        r"(?:[a-z]|\d+(?:\.\d+)?)\s*(?:(?:[a-z]|\d+(?:\.\d+)?)\s*){0,8}",
                        text.strip(),
                    ) and re.search(r"\b[a-z]\b", text):
                        kind = "panel_label"
                    if kind in {"header", "panel_label"}:
                        section_titles = []
                    blocks.append(
                        ParsedBlock(
                            text,
                            (box[0], box[1], box[2], box[3]),
                            kind,
                            len(blocks),
                            max(sizes, default=0),
                            notation,
                            notation_issues,
                            tuple(section_titles),
                        )
                    )
                # Prose-only two-column pages are read by column. Figure pages retain
                # the parser's original order; neither order is scientifically verified.
                if not any(figure_number(b.text) for b in blocks):
                    left = [
                        b
                        for b in blocks
                        if len(b.text) > 250 and b.bbox[2] < page.mediabox.width * 0.55
                    ]
                    right = [
                        b
                        for b in blocks
                        if len(b.text) > 250 and b.bbox[0] > page.mediabox.width * 0.45
                    ]
                    if left and right:
                        top = [b for b in blocks if b.bbox[1] < page.mediabox.height * 0.1]
                        rest = [b for b in blocks if b not in top]
                        rest.sort(key=lambda b: (b.bbox[0] > page.mediabox.width * 0.45, b.bbox[1]))
                        blocks = [replace(b, order=i) for i, b in enumerate(top + rest)]
                parsed_pages.append(
                    ParsedPage(
                        number,
                        page.rect.width,
                        page.rect.height,
                        page.rotation,
                        join_fragments(blocks),
                    )
                )
            # Running headers retain their individual source blocks. No node merging.
            margins: Counter[str] = Counter()
            for parsed in parsed_pages:
                margins.update(
                    {
                        " ".join(b.text.split()).casefold()
                        for b in parsed.blocks
                        if len(b.text) < 180
                        and (b.bbox[1] < parsed.height * 0.1 or b.bbox[1] > parsed.height * 0.94)
                    }
                )
            for parsed in parsed_pages:
                yield replace(
                    parsed,
                    blocks=[
                        replace(b, kind="header", section_titles=())
                        if margins[" ".join(b.text.split()).casefold()] >= 2
                        and (b.bbox[1] < parsed.height * 0.1 or b.bbox[1] > parsed.height * 0.94)
                        else b
                        for b in parsed.blocks
                    ],
                )


def page_image(content: bytes, number: int) -> bytes:
    with pymupdf.open(stream=content, filetype="pdf") as document:
        if number < 1 or number > len(document):
            raise ValueError("PAGE_NOT_FOUND")
        page = document[number - 1]
        if (
            not math.isfinite(page.rect.width * page.rect.height)
            or page.rect.width <= 0
            or page.rect.height <= 0
        ):
            raise ValueError("INVALID_PAGE_DIMENSIONS")
        scale = min(1.5, 3000 / max(page.rect.width, page.rect.height))
        return bytes(
            page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png")
        )


def display_box(content: bytes, number: int, bbox: BBox) -> BBox:
    with pymupdf.open(stream=content, filetype="pdf") as document:
        rect = pymupdf.Rect(bbox) * document[number - 1].rotation_matrix
        return rect.x0, rect.y0, rect.x1, rect.y1
