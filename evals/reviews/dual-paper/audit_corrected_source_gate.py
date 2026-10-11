"""Read-only reconciliation of corrected production with immutable human history.

This adapter does not issue human decisions. A text-key match is a comparison aid,
not permission to attach an old ACCEPT to a fresh node/source/version identity.
Frozen model metrics remain exactly as emitted by evaluate_source_gate.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from reevaluate_human_source_gate import THRESHOLDS, history_digest, latest, require


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def content_fingerprint(snapshot):
    return hashlib.sha256(
        json.dumps(
            snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def inspect_current(path):
    database = path.parent / (path.stem + "-runtime") / "graph.db"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        spans = {
            r["id"]: dict(r) for r in connection.execute("SELECT * FROM source_spans")
        }
        anchors = {
            r["id"]: dict(r) for r in connection.execute("SELECT * FROM source_anchors")
        }
        nodes = {
            r["id"]: dict(r)
            for r in connection.execute("SELECT * FROM knowledge_nodes")
        }
        paper = dict(connection.execute("SELECT * FROM papers").fetchone())
        reviews = connection.execute(
            "SELECT COUNT(*) FROM verification_records"
        ).fetchone()[0]
    for span in spans.values():
        for key in ["bbox", "notation", "notation_issues", "section_titles"]:
            span[key] = json.loads(span[key])
    for anchor in anchors.values():
        anchor["bbox"] = json.loads(anchor["bbox"])
        source = spans[anchor["span_id"]]
        anchor["notation"] = source["notation"]
        anchor["notation_issues"] = source["notation_issues"]
        anchor["section_titles"] = source["section_titles"]
    for node in nodes.values():
        node["provenance"] = json.loads(node["provenance"])
    return database, paper, nodes, anchors, spans, reviews


def audit(root, productions, browser, public_browser, output):
    sys.path.insert(0, str(root / "backend"))
    from papergraph.models import NodeRow
    from papergraph.provenance import fingerprint
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    ledger_path = root / "evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json"
    ledger_hash = digest(ledger_path)
    ledger = read(ledger_path)
    manifest = read(
        root / "evals/reports/dual-paper/human-reviewed-20261011-r2/manifest.json"
    )
    require(
        history_digest(ledger) == manifest["human_decision_history_sha256"],
        "Human history changed",
    )
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for letter, path in productions.items():
        pins = ledger["inputs"][letter]
        for name in ["gold", "prediction_review", "production_report"]:
            require(
                digest(Path(pins[name + "_path"])) == pins[name + "_sha256"],
                "Frozen input changed",
            )
        current = read(path)
        require(current["source_hash"] == pins["source_sha256"], "Source hash changed")
        require(current["gold_hash"] == pins["gold_sha256"], "Gold hash changed")
        db, paper, nodes, anchors, spans, reviews = inspect_current(path)
        require(
            paper["source_hash"] == current["source_hash"] and reviews == 0,
            "Unexpected source/review state",
        )
        engine = create_engine(f"sqlite:///file:{db.as_posix()}?mode=ro&uri=true")
        with Session(engine) as session:
            fingerprints = {
                n.id: fingerprint(session, n) for n in session.scalars(select(NodeRow))
            }
        engine.dispose()
        original = latest(ledger["decisions"], letter, production_only=True)
        by_key = {e["prediction_key"]: e for e in original.values()}
        comparison = []
        matched_old = set()
        for prediction in current["predictions"]:
            node = nodes[prediction["node_id"]]
            evidence = [anchors[k] for k in node["provenance"]]
            fingerprint_payload = {
                "node_id": node["id"],
                "node_version": node["version"],
                "type": node["type"],
                "layer": node["layer"],
                "text": node["text"],
                "epistemic_status": node["epistemic_status"],
                "parser_version": paper["parser_version"],
                "anchors": evidence,
            }
            event = by_key.get(prediction["key"])
            if event is None:
                possible = [
                    e
                    for e in original.values()
                    if e["original_prediction"]["page"] == prediction["page"]
                    and e["original_prediction"]["text"] == prediction["text"]
                ]
                if len(possible) == 1:
                    event = possible[0]
            material = []
            if event:
                matched_old.add(event["prediction_key"])
                old = event["reviewed_snapshot"]["current_local_node"]
                old_anchor = event["reviewed_snapshot"]["current_source_anchor"]
                for key in ["type", "layer", "text", "epistemic_status", "version"]:
                    if old[key] != node[key]:
                        material.append("node." + key)
                for key in [
                    "page_number",
                    "start_char",
                    "end_char",
                    "text",
                    "source_hash",
                ]:
                    if len(evidence) != 1 or evidence[0][key] != old_anchor[key]:
                        material.append("source." + key)
                if len(evidence) != 1 or evidence[0]["bbox"] != json.loads(
                    old_anchor["bbox"]
                ):
                    material.append("source.bbox")
                if any(
                    a["notation"] or a["notation_issues"] or a["section_titles"]
                    for a in evidence
                ):
                    material.append("source.typography_or_heading_metadata")
            comparison.append(
                {
                    "prediction_key": prediction["key"],
                    "node_id": node["id"],
                    "node_version": node["version"],
                    "type": node["type"],
                    "text": node["text"],
                    "source_hash": paper["source_hash"],
                    "evidence_fingerprint": fingerprints[node["id"]],
                    "evaluation_snapshot_digest": content_fingerprint(
                        fingerprint_payload
                    ),
                    "source_snapshot": evidence,
                    "previous_decision_id": event["decision_id"] if event else None,
                    "previous_human_decision": event["decision"] if event else None,
                    "comparison_status": (
                        "STALE_REQUIRES_CURRENT_REVIEW"
                        if material
                        else "MATCHING_REQUIRES_CURRENT_REVIEW_BINDING"
                    )
                    if event
                    else "NEW_UNREVIEWED",
                    "material_changes": material,
                    "human_acceptance_inherited": False,
                    "current_human_decision": None,
                    "current_review_scope": "SOURCE_ATTRIBUTION",
                }
            )
        removed = []
        for key, event in by_key.items():
            if key not in matched_old:
                quote = event["original_prediction"]["text"]
                removed.append(
                    {
                        "prediction_key": key,
                        "previous_decision_id": event["decision_id"],
                        "previous_human_decision": event["decision"],
                        "source_preserved": any(
                            quote in s["text"] for s in spans.values()
                        ),
                        "status": "REMOVED_OR_CHANGED_TEXT_REQUIRES_RECONCILIATION",
                    }
                )
        anomalies = []
        for event in ledger["parser_anomaly_decisions"]:
            if event["paper"] != letter:
                continue
            snapshot = event["reviewed_snapshot"]
            seen = set()
            for instance in [snapshot, *snapshot.get("related_header_instances", [])]:
                old = instance["current_source_anchor"]
                if old["id"] in seen:
                    continue
                seen.add(old["id"])
                found = [
                    s
                    for s in spans.values()
                    if s["text"] == old["text"]
                    and s["page_number"] == old["page_number"]
                ]
                anomalies.append(
                    {
                        "previous_decision_id": event["decision_id"],
                        "page": old["page_number"],
                        "text": old["text"],
                        "current_source_roles": [s["kind"] for s in found],
                        "scientific_section_removed": not any(
                            n["type"] == "SECTION" and n["text"] == old["text"]
                            for n in nodes.values()
                        ),
                        "human_decision_unchanged": True,
                    }
                )
        issues = [
            {
                "span_id": s["id"],
                "page": s["page_number"],
                "bbox": s["bbox"],
                "issues": s["notation_issues"],
            }
            for s in spans.values()
            if s["notation_issues"]
        ]
        unknown_keys = [
            p["key"]
            for p in current["predictions"]
            if p["adjudication"].get("origin") == "UNREVIEWED"
        ]
        for issue in issues:
            issue["matched_gold_ids"] = [
                m["gold_id"]
                for m in current["matches"]
                if m["node_id"]
                and any(
                    anchors[k]["span_id"] == issue["span_id"]
                    for k in nodes[m["node_id"]]["provenance"]
                )
            ]
        browser_entry = next(
            x for x in read(browser) if x["source_hash"] == current["source_hash"]
        )
        require(
            browser_entry["status"] == "PASS"
            and read(public_browser)["status"] == "PASS",
            "Browser validation incomplete",
        )
        result = {
            "schema_version": 1,
            "paper": letter,
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_hash": current["source_hash"],
            "gold_sha256": current["gold_hash"],
            "human_ledger_sha256": ledger_hash,
            "human_decision_history_sha256": history_digest(ledger),
            "production_path": str(path),
            "production_sha256": digest(path),
            "isolated_database": str(db),
            "parser_version": current["parser_version"],
            "pipeline_version": current["pipeline_version"],
            "thresholds": THRESHOLDS,
            "frozen_model_comparison_metrics": current["metrics"],
            "frozen_model_metric_checks": current["metric_checks"],
            "frozen_model_sampled_measurements_pass": current[
                "sampled_measurements_pass"
            ],
            "prior_human_review": "COMPLETE",
            "current_production_human_review": "REQUIRES_CURRENT_REVIEW",
            "current_human_precision": None,
            "human_acceptance_inherited": False,
            "prediction_reconciliation": comparison,
            "frozen_model_unreviewed_prediction_keys": unknown_keys,
            "removed_or_changed_predictions": removed,
            "parser_anomaly_reconciliation": anomalies,
            "unresolved_notation_spans": issues,
            "nodes": current["nodes"],
            "edges": current["edges"],
            "integrity": current["integrity"],
            "semantic_edges": current["semantic_edges"],
            "application_verification_records": reviews,
            "browser": browser_entry,
            "public_browser": read(public_browser),
            "scientific_validity": "NOT_ASSESSED",
            "overall_reviewed_gate": "FAIL",
            "gate_b": "NOT_STARTED",
            "failure_basis": [
                "Corrected production lacks attributable current human review/binding; no old ACCEPT was copied."
            ]
            + [
                f"Frozen model comparison {k} failed."
                for k, v in current["metric_checks"].items()
                if not v
            ],
            "limitations": [
                "Frozen model comparison precision counts unknown changed/new text-type keys incorrect.",
                "This reconciliation does not establish human precision or accept scientific classifications.",
                "Raw source strings/anchors stay literal; typography is a geometry-backed view, not reconstructed formula algebra.",
                "Canonical existing application graphs were preserved; this report describes fresh isolated production only.",
            ],
        }
        target = output / f"paper-{letter.lower()}.json"
        target.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        results[letter] = {
            "path": str(target),
            "sha256": digest(target),
            "overall_reviewed_gate": "FAIL",
        }
    require(digest(ledger_path) == ledger_hash, "Human ledger changed during audit")
    final = {
        "schema_version": 1,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "papers": results,
        "human_ledger_sha256": ledger_hash,
        "human_decision_history_sha256": history_digest(ledger),
        "evaluator_sha256": digest(Path(__file__)),
        "browser_sha256": digest(browser),
        "public_browser_sha256": digest(public_browser),
        "thresholds": THRESHOLDS,
        "gate_b": "NOT_STARTED",
        "new_human_decisions_created": 0,
    }
    (output / "manifest.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--production-a", type=Path, required=True)
    parser.add_argument("--production-b", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--public-browser", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(
        args.root,
        {"A": args.production_a, "B": args.production_b},
        args.browser,
        args.public_browser,
        args.output,
    )
