"""Shared source-label syntax, independent of paper/domain identities."""

import re

FIGURE = re.compile(r"(?i)^(?:(?:extended data|supplementary)\s+)?fig(?:ure)?\.?\s*(S?\d+)\b")
EQUATION = re.compile(r"\(((?:0|[1-9]\d*)[a-z]?)\)")


def figure_number(text: str) -> str | None:
    match = FIGURE.match(" ".join(text.split()))
    return match[1] if match else None


def equation_number(text: str) -> str | None:
    # A display number may be its own extracted line or trail a compact equation.
    # Leading-zero indices and parentheses inside prose are not display labels.
    for line in text.splitlines():
        match = EQUATION.fullmatch(line.strip())
        if match:
            return match[1]
    compact = " ".join(text.split())
    if len(compact) <= 200:
        match = re.search(EQUATION.pattern + r"\s*$", compact)
        if match:
            return match[1]
    return None
