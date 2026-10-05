import math
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

import pymupdf

from .schemas import BBox
from .source_patterns import EQUATION, figure_number

SUPERSCRIPT = str.maketrans("0123456789+-−()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁽⁾")


def glyph_text(text: str, flags: int) -> str:
    """Preserve PDF superscript typography, without interpreting its scientific role."""
    return text.translate(SUPERSCRIPT) if flags & 1 else text


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    bbox: BBox
    kind: str
    order: int
    font_size: float = 0


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
            block = ParsedBlock(
                text, box, "paragraph", len(output), max(b.font_size for b in fragments)
            )
        output.append(ParsedBlock(block.text, block.bbox, block.kind, len(output), block.font_size))
    return output


class MuPDFParser:
    name = "pymupdf"
    version = str(pymupdf.VersionBind) + "+layout-v2"

    def pages(self, content: bytes, max_pages: int) -> Iterator[ParsedPage]:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("ENCRYPTED_PDF")
            if len(document) > max_pages:
                raise ValueError("PAGE_LIMIT_EXCEEDED")
            if not len(document):
                raise ValueError("EMPTY_PDF")
            for number, page in enumerate(document, 1):
                blocks: list[ParsedBlock] = []
                layout = page.get_text(
                    "dict", sort=True, flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
                )["blocks"]
                body_fonts: Counter[float] = Counter()
                for block in layout:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            if len(span["text"].strip()) >= 35:
                                body_fonts[round(float(span["size"]), 1)] += len(span["text"])
                body_size = body_fonts.most_common(1)[0][0] if body_fonts else 0
                for block in layout:
                    if block["type"] != 0:
                        continue
                    lines = block.get("lines", [])
                    text = "\n".join(
                        "".join(
                            glyph_text(span["text"], int(span["flags"])) for span in line["spans"]
                        )
                        for line in lines
                    )
                    if not text.strip():
                        continue
                    sizes = [float(span["size"]) for line in lines for span in line["spans"]]
                    bold = any(int(span["flags"]) & 16 for line in lines for span in line["spans"])
                    heading = (
                        5 <= len(text) < 180
                        and block["bbox"][1] < page.mediabox.height * 0.94
                        and (
                            max(sizes, default=0) >= 14
                            or bold
                            and max(sizes, default=0) >= body_size - 0.5
                        )
                    )
                    box = block["bbox"]
                    blocks.append(
                        ParsedBlock(
                            text,
                            (box[0], box[1], box[2], box[3]),
                            "heading" if heading else "paragraph",
                            len(blocks),
                            max(sizes, default=0),
                        )
                    )
                yield ParsedPage(
                    number, page.rect.width, page.rect.height, page.rotation, join_fragments(blocks)
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
