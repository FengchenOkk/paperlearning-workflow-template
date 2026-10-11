"""Geometry-backed typography observations. Never rewrite the literal source string."""

from collections import Counter
from typing import Any, Literal

from .schemas import SourceNotation

SUPERSCRIPT = str.maketrans("0123456789+-−()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁽⁾")


def glyph_text(text: str, flags: int) -> str:
    return text.translate(SUPERSCRIPT) if flags & 1 else text


def block_notation(
    block: dict[str, Any], rules: list[tuple[float, float, float, float]]
) -> tuple[str, list[SourceNotation], list[str]]:
    text = ""
    notes: list[SourceNotation] = []
    glyphs: list[tuple[int, dict[str, Any], float]] = []
    issues: list[str] = []
    for number, line in enumerate(block.get("lines", [])):
        if number:
            text += "\n"
        spans = line["spans"]
        sizes: Counter[float] = Counter()
        for span in spans:
            sizes[round(float(span["size"]), 1)] += len(span["chars"])
        body_size = sizes.most_common(1)[0][0] if sizes else 0
        baselines = [float(s["origin"][1]) for s in spans if s["size"] >= body_size * 0.9]
        baseline = min(baselines) if baselines else 0
        for span in spans:
            raw = "".join(c["c"] for c in span["chars"])
            observed = glyph_text(raw, int(span["flags"]))
            start = len(text)
            text += observed
            for offset, char in enumerate(span["chars"]):
                glyphs.append((start + offset, char, float(span["size"])))
            if not raw.strip() or line.get("dir") != (1.0, 0.0):
                continue
            superscript = bool(int(span["flags"]) & 1)
            reduced = span["size"] < body_size * 0.8
            displacement = float(span["origin"][1]) - baseline
            previous = text[:start]
            attached = bool(previous and previous[-1].isalnum() and not previous[-1].isspace())
            symbolic = any(c.isalnum() for c in raw) and not raw.startswith(
                (" ", ",", ".", ")", "(")
            )
            subscript = (
                reduced
                and attached
                and symbolic
                and body_size * 0.1 < displacement < body_size * 0.55
            )
            raised = (
                reduced and attached and symbolic and -body_size < displacement < -body_size * 0.1
            )
            if superscript or subscript or raised:
                kind: Literal["SUBSCRIPT", "SUPERSCRIPT"] = (
                    "SUBSCRIPT" if subscript and not superscript else "SUPERSCRIPT"
                )
                display_raw = observed.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾", "0123456789+−()"))
                notes.append(
                    SourceNotation(
                        start_char=start,
                        end_char=len(text),
                        raw=observed,
                        display=("_" if kind == "SUBSCRIPT" else "^") + display_raw,
                        kind=kind,
                        bbox=tuple(span["bbox"]),
                        basis="PDF_SUPERSCRIPT_FLAG" if superscript else "PDF_BASELINE_AND_SIZE",
                    )
                )
            elif reduced and attached and symbolic and abs(displacement) > body_size * 0.07:
                issues.append(
                    f"Ambiguous shifted glyph at characters {start}:{len(text)}; read the original PDF."
                )
    for x0, y0, x1, y1 in rules:
        if not (
            block["bbox"][0] <= (x0 + x1) / 2 <= block["bbox"][2]
            and block["bbox"][1] <= (y0 + y1) / 2 <= block["bbox"][3]
        ):
            continue
        candidates = []
        for index, char, size in glyphs:
            cx0, _, cx1, _ = char["bbox"]
            baseline = char["origin"][1]
            if (
                char["c"].isalnum()
                and size * 0.5 <= baseline - (y0 + y1) / 2 <= size * 1.05
                and cx0 - 0.2 <= x0
                and x1 <= cx1 + 0.2
            ):
                candidates.append((index, char))
        if len(candidates) == 1:
            index, char = candidates[0]
            if any(n.start_char <= index < n.end_char for n in notes):
                issues.append("Overlapping typography observations; read the original PDF.")
                continue
            notes.append(
                SourceNotation(
                    start_char=index,
                    end_char=index + 1,
                    raw=text[index : index + 1],
                    display=text[index : index + 1] + "\u0305",
                    kind="OVERBAR",
                    bbox=tuple(char["bbox"]),
                    basis="PDF_DRAWING_AND_GLYPH",
                )
            )
        elif candidates:
            issues.append("Ambiguous overbar geometry; read the original PDF.")
        else:
            # A short rule near glyph tops may be mathematical layout, not an overbar.
            nearby = [
                c
                for _, c, size in glyphs
                if c["c"].isalnum()
                and size * 0.5 <= c["origin"][1] - (y0 + y1) / 2 <= size * 1.05
                and min(x1, c["bbox"][2]) > max(x0, c["bbox"][0])
            ]
            if nearby:
                issues.append(
                    "Unresolved short mathematical rule; no symbol reconstruction inferred."
                )
    notes.sort(key=lambda n: (n.start_char, n.end_char))
    return text, notes, list(dict.fromkeys(issues))


def notation_text(text: str, notes: list[SourceNotation]) -> str:
    result = text
    for note in reversed(notes):
        result = result[: note.start_char] + note.display + result[note.end_char :]
    return result
