"""Score a frozen source sample AFTER the unchanged production upload/worker pipeline.

Local PDF paths are explicit arguments, never fixtures or production extraction inputs.
Gold cannot create nodes, edges, reviews or source text. Each invocation uses fresh storage.
"""

import argparse
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from papergraph.config import Settings
from papergraph.database import Database
from papergraph.integrity import report
from papergraph.models import (
    AnchorRow,
    EdgeRow,
    EquationRow,
    FigureRow,
    JobRow,
    NodeRow,
    PaperRow,
    VerificationRow,
)
from papergraph.provenance import anchors_for
from papergraph.repository import required
from papergraph.services import upload
from papergraph.storage import DocumentStorage
from papergraph.worker import run_once


def compact(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def numeric_text(text: str) -> str:
    # Keep an observed superscript distinct from a neighboring baseline digit.
    table = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", lambda m: "^" + m[0].translate(table), text)
    text = unicodedata.normalize("NFKC", text).replace("−", "-").replace("×", "*")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"(?<=\d)-(?=[A-Za-z])", "", text)
    return "".join(text.split())


def contains(outer: list[float], inner: list[float]) -> bool:
    return all((outer[i] <= inner[i] + 1 if i < 2 else outer[i] >= inner[i] - 1) for i in range(4))


def quantity_matches(text: str, quantity: dict) -> bool:
    unit = "" if quantity["unit"] == "dimensionless" else quantity["unit"]
    expected = re.escape(numeric_text(quantity["value"] + " " + unit))
    return bool(re.search(r"(?<![0-9.^+\-])" + expected + r"(?![0-9^/+\-])", numeric_text(text)))


def score(pdf: Path, gold_path: Path, output: Path, adjudication: Path | None) -> dict:
    content = pdf.read_bytes()
    gold_bytes = gold_path.read_bytes()
    gold = json.loads(gold_bytes)
    if hashlib.sha256(content).hexdigest() != gold["source_hash"]:
        raise ValueError("PDF hash differs from frozen gold; do not substitute a different edition")
    output.parent.mkdir(parents=True, exist_ok=True)
    runtime = output.parent / (output.stem + "-runtime")
    runtime.mkdir(exist_ok=False)
    settings = Settings(
        database_url=f"sqlite:///{(runtime / 'graph.db').resolve().as_posix()}",
        storage_dir=runtime / "documents",
    )
    previous = os.environ.get("PAPERGRAPH_DATABASE_URL")
    os.environ["PAPERGRAPH_DATABASE_URL"] = settings.database_url
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        if previous is None:
            os.environ.pop("PAPERGRAPH_DATABASE_URL", None)
        else:
            os.environ["PAPERGRAPH_DATABASE_URL"] = previous
    db = Database(settings.database_url)
    storage = DocumentStorage(settings.storage_dir)
    # Gold is deliberately not passed to either production entry point.
    uploaded = upload(db, storage, content, pdf.name)
    assert run_once(db, storage, settings)
    decisions = json.loads(adjudication.read_bytes()) if adjudication else {}
    with db.session() as session:
        paper = required(session, PaperRow, uploaded.paper.id)
        job = required(session, JobRow, uploaded.job.id)
        if job.status not in {"READY", "PARTIAL"}:
            raise ValueError(f"Production job failed: {job.error}")
        nodes = list(session.scalars(select(NodeRow).where(NodeRow.paper_id == paper.id)))
        edges = list(session.scalars(select(EdgeRow).where(EdgeRow.paper_id == paper.id)))
        anchors = {
            a.id: a
            for a in session.scalars(select(AnchorRow).where(AnchorRow.paper_id == paper.id))
        }
        integrity = report(session, paper.id).model_dump(mode="json")
        valid_nodes = []
        for n in nodes:
            try:
                anchors_for(session, paper, n.provenance)
                if n.provenance:
                    valid_nodes.append(n.id)
            except ValueError:
                pass
        valid_edges = []
        for edge in edges:
            try:
                anchors_for(session, paper, edge.provenance)
                if edge.provenance:
                    valid_edges.append(edge.id)
            except ValueError:
                pass
        predictions = []
        for n in nodes:
            if n.type in {"PAPER", "SECTION"}:
                continue
            locations = [anchors[a] for a in n.provenance]
            if any(
                a.page_number == w["page"] and contains(a.bbox, w["bbox"])
                for a in locations
                for w in gold["precision_windows"]
            ):
                key = hashlib.sha256((n.type + "\n" + n.text).encode()).hexdigest()
                decision = decisions.get(key, {})
                predictions.append(
                    {
                        "key": key,
                        "node_id": n.id,
                        "type": n.type,
                        "text": n.text,
                        "page": locations[0].page_number,
                        "bbox": locations[0].bbox,
                        "adjudication": decision or {"correct": False, "origin": "UNREVIEWED"},
                    }
                )
        matches = []
        for item in gold["items"]:
            candidates = [
                n
                for n in nodes
                if n.type not in {"PAPER", "SECTION"}
                and all(
                    any(
                        anchors[a].page_number == item["page"]
                        and contains(anchors[a].bbox, c["bbox"])
                        and compact(c["text"]) in compact(n.text)
                        for a in n.provenance
                    )
                    for c in item["components"]
                )
            ]
            selected = next(
                (n for n in candidates if n.type == item["type"]),
                candidates[0] if candidates else None,
            )
            same_type = selected is not None and selected.type == item["type"]
            exact_source = selected is not None and selected.id in valid_nodes
            observed_number = None
            if selected is not None and selected.type == "FIGURE":
                figure = session.get(FigureRow, selected.id)
                observed_number = figure.figure_number if figure else None
            elif selected is not None and selected.type == "EQUATION":
                equation = session.get(EquationRow, selected.id)
                observed_number = equation.equation_number if equation else None
            matches.append(
                {
                    "gold_id": item["id"],
                    "expected_type": item["type"],
                    "node_id": selected.id if selected else None,
                    "actual_type": selected.type if selected else None,
                    "same_type": same_type,
                    "correct_source": exact_source,
                    "number_correct": item["number"] is None or observed_number == item["number"],
                    "quantities": [
                        {
                            "value": q["value"],
                            "unit": q["unit"],
                            "context": q["context"],
                            "pass": bool(
                                same_type
                                and exact_source
                                and selected is not None
                                and quantity_matches(selected.text, q)
                            ),
                            "issue": None
                            if selected is not None
                            and same_type
                            and quantity_matches(selected.text, q)
                            else q.get("representation_warning")
                            or "No same-type object with the expected value/unit representation",
                        }
                        for q in item["quantities"]
                    ],
                }
            )

        def ratio(passed: int, total: int) -> dict:
            return {"passed": passed, "total": total, "rate": passed / total if total else None}

        matched = [m for m in matches if m["node_id"]]
        quantities = [q for m in matches for q in m["quantities"]]
        figures = [m for m in matches if m["expected_type"] == "FIGURE"]
        equations = [m for m in matches if m["expected_type"] == "EQUATION"]
        metrics = {
            "precision": ratio(
                sum(p["adjudication"].get("correct") is True for p in predictions), len(predictions)
            ),
            "recall": ratio(sum(m["same_type"] for m in matches), len(matches)),
            "type_accuracy": ratio(sum(m["same_type"] for m in matched), len(matched)),
            "anchors": ratio(sum(m["correct_source"] for m in matched), len(matched)),
            "pages": ratio(sum(m["correct_source"] for m in matched), len(matched)),
            "figures": ratio(
                sum(m["same_type"] and m["number_correct"] for m in figures), len(figures)
            ),
            "equations": ratio(
                sum(m["same_type"] and m["number_correct"] for m in equations), len(equations)
            ),
            "quantities": ratio(sum(q["pass"] for q in quantities), len(quantities)),
            "node_provenance": ratio(len(valid_nodes), len(nodes)),
            "edge_provenance": ratio(len(valid_edges), len(edges)),
        }
        thresholds = {
            "precision": 0.9,
            "recall": 0.8,
            "type_accuracy": 0.9,
            "anchors": 1,
            "pages": 1,
            "figures": 1,
            "equations": 1,
            "quantities": 1,
            "node_provenance": 1,
            "edge_provenance": 1,
        }
        metric_checks = {
            name: (metric["rate"] is not None and metric["rate"] >= thresholds[name])
            or (
                name == "equations"
                and metric["total"] == 0
                and bool(gold.get("explicit_absences", {}).get("numbered_equations"))
            )
            for name, metric in metrics.items()
        }
        result = {
            "source_hash": paper.source_hash,
            "gold_hash": hashlib.sha256(gold_bytes).hexdigest(),
            "parser": paper.parser,
            "parser_version": paper.parser_version,
            "pipeline_version": job.pipeline_version,
            "job_status": job.status,
            "title": paper.title,
            "page_count": paper.page_count,
            "nodes": len(nodes),
            "edges": len(edges),
            "semantic_edges": sum(e.relation_type != "CONTAINS" for e in edges),
            "verification_records": len(list(session.scalars(select(VerificationRow)))),
            "metrics": metrics,
            "metric_checks": metric_checks,
            "sampled_measurements_pass": all(metric_checks.values())
            and integrity["structurally_valid"],
            "matches": matches,
            "predictions": predictions,
            "integrity": integrity,
            "human_review": "PENDING",
            "overall_reviewed_gate": "FAIL",
            "limitations": [
                "Precision requires separately recorded source adjudication; unreviewed predictions count as incorrect.",
                "Numeric scoring is a frozen model source-review comparison, not scientific validity or human acceptance.",
                "Anchor/page rates are conditional on matched objects; missing figures/equations fail their own measures.",
                "Browser results are recorded separately. No semantic reasoning quality is established by an empty semantic graph.",
            ],
        }
    db.engine.dispose()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path)
    args = parser.parse_args()
    result = score(args.pdf, args.gold, args.output, args.adjudication)
    print(
        json.dumps(
            {"metrics": result["metrics"], "overall_reviewed_gate": result["overall_reviewed_gate"]}
        )
    )
