"""Literal, local evidence retrieval. Normalization never rewrites stored source text."""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AnchorRow, NodeRow, PaperRow
from .provenance import anchors_for
from .schemas import SearchHit


def searchable(text: str) -> str:
    # Join PDF line-wrap hyphens before whitespace collapse; keep genuine word boundaries.
    superscript = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789−+")
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", lambda m: "^" + m[0].translate(superscript), text)
    text = unicodedata.normalize("NFKC", text).casefold().replace("\u00ad", "")
    text = re.sub(r"(?<=\w)[-‐]\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"(?<!\w)-(?=\d)", "−", text)
    return " ".join(re.findall(r"\w+|[−±×Ω°]+", text, flags=re.UNICODE))


def relevance(text: str, query: str) -> int:
    words = searchable(query).split()
    normalized = searchable(text)
    if not words or not all(word in normalized.split() for word in words):
        return 0
    return 2 if " ".join(words) in normalized else 1


def search(session: Session, paper: PaperRow, query: str, limit: int = 50) -> list[SearchHit]:
    # Bounded by the document's upload/page limits. A persistent token index can replace
    # this scan without changing source anchors; no network/provider is involved.
    anchors = list(session.scalars(select(AnchorRow).where(AnchorRow.paper_id == paper.id)))
    nodes = list(session.scalars(select(NodeRow).where(NodeRow.paper_id == paper.id)))
    ranked: list[tuple[int, SearchHit]] = []
    used: set[str] = set()
    for node in nodes:
        score = relevance(node.text, query)
        if not score or not node.provenance:
            continue
        evidence = anchors_for(session, paper, node.provenance)
        # Select the anchor containing the match rather than always jumping to the first.
        anchor = next((a for a in evidence if relevance(a.text, query)), None)
        if anchor is None:
            continue
        used.add(anchor.id)
        ranked.append(
            (
                score,
                SearchHit(
                    node_id=node.id,
                    anchor_id=anchor.id,
                    page_number=anchor.page_number,
                    text=node.text,
                    kind=node.type,
                ),
            )
        )
    for anchor in anchors:
        score = relevance(anchor.text, query)
        if score and anchor.id not in used:
            anchors_for(session, paper, [anchor.id])
            ranked.append(
                (
                    score,
                    SearchHit(
                        node_id=None,
                        anchor_id=anchor.id,
                        page_number=anchor.page_number,
                        text=anchor.text,
                        kind="SOURCE_SPAN",
                    ),
                )
            )
    ranked.sort(
        key=lambda pair: (-pair[0], pair[1].page_number, pair[1].anchor_id, pair[1].node_id or "")
    )
    return [hit for _, hit in ranked[:limit]]
