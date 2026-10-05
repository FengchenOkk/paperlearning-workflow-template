import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

import pymupdf

from .schemas import BBox


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


class MuPDFParser:
    name = "pymupdf"
    version = str(pymupdf.VersionBind)

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
                for block in page.get_text(
                    "dict", sort=True, flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
                )["blocks"]:
                    if block["type"] != 0:
                        continue
                    lines = block.get("lines", [])
                    text = "\n".join(
                        "".join(span["text"] for span in line["spans"]) for line in lines
                    )
                    if not text.strip():
                        continue
                    sizes = [float(span["size"]) for line in lines for span in line["spans"]]
                    bold = any(int(span["flags"]) & 16 for line in lines for span in line["spans"])
                    heading = len(text) < 180 and (max(sizes, default=0) >= 14 or bold)
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
                yield ParsedPage(number, page.rect.width, page.rect.height, page.rotation, blocks)


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
