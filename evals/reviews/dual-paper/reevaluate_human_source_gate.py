"""Audit frozen production measurements against separately recorded human reviews.

This evaluation-only script never edits gold, human decisions or the application DB.
Run the unchanged production evaluator first, then supply its fresh reports here.
"""

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


THRESHOLDS = {
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
HISTORY_FIELDS = (
    "decisions", "quantity_decisions", "parser_anomaly_decisions",
    "revision_resolutions", "review_explanation_overrides", "revision_proposals",
    "resolved_revision_requests", "revision_clarifications",
    "review_presentation_decisions", "review_display_overrides",
    "review_presentation_resolutions", "supplementary_method_summaries",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def history_digest(ledger):
    content = {key: ledger.get(key) for key in HISTORY_FIELDS}
    return hashlib.sha256(json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(event):
    if "quantity_index" in event:
        return f"{event['gold_item_id']}:quantity:{event['quantity_index']}"
    return event.get("gold_item_id") or event.get("review_item_id") or event.get("prediction_key")


def latest(events, paper, production_only=False):
    result = {}
    for event in events:
        if event["paper"] != paper:
            continue
        if production_only and event.get("review_target"):
            # A separately accepted revision draft is not a production correction.
            continue
        require(bool(identity(event)), "Review event lacks a stable identity")
        result[identity(event)] = event
    return result


def counts(events):
    values = Counter(event["decision"] for event in events)
    return {key: values[key] for key in ("ACCEPT", "REVISE", "REJECT")}


def check_snapshots(connection, ledger):
    checked = set()
    for field in ("decisions", "quantity_decisions", "parser_anomaly_decisions"):
        for event in ledger[field]:
            require(event["review_origin"] == "HUMAN_SOURCE_REVIEW", "Wrong review origin")
            require(event["scope"] == "SOURCE_ATTRIBUTION", "Wrong review scope")
            require(bool(event["user_response_verbatim"]), "No attributable user response")
            pins = ledger["inputs"][event["paper"]]
            require(event["source_sha256"] == pins["source_sha256"], "Stale review source hash")
            require(event["gold_sha256"] == pins["gold_sha256"], "Stale review gold hash")
            snapshot = event["reviewed_snapshot"]
            for instance in [snapshot, *snapshot.get("related_header_instances", [])]:
                for field_name, table in (
                    ("current_local_node", "knowledge_nodes"),
                    ("current_source_anchor", "source_anchors"),
                ):
                    expected = instance[field_name]
                    row = connection.execute(
                        f"SELECT * FROM {table} WHERE id = ?", (expected["id"],)
                    ).fetchone()
                    require(row is not None, "Reviewed source object is missing")
                    actual = dict(row)
                    for key, value in expected.items():
                        require(key in actual and actual[key] == value,
                                f"Stale {table} snapshot: {expected['id']} / {key}")
                    checked.add((table, expected["id"]))
    return len(checked)


def audit(root, production_paths, output):
    ledger_path = root / "evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json"
    ledger = json.loads(ledger_path.read_bytes())
    require(ledger.get("pending_revision") is None, "Review clarification is pending")
    completion = {entry["paper"]: entry for entry in ledger["paper_review_completion_records"]}
    for paper in ("A", "B"):
        require(completion[paper]["human_source_review_complete"] is True, "Incomplete review")
        for path_key, hash_key in (
            ("gold_path", "gold_sha256"),
            ("prediction_review_path", "prediction_review_sha256"),
            ("production_report_path", "production_report_sha256"),
        ):
            pins = ledger["inputs"][paper]
            require(digest(Path(pins[path_key])) == pins[hash_key], "Frozen input changed")
        pdf = root / "backend/data/documents" / (pins["source_sha256"] + ".pdf")
        require(digest(pdf) == pins["source_sha256"], "PDF changed")
    db_path = root / "backend/data/papergraph.db"
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        checked_snapshots = check_snapshots(connection, ledger)
    resolution_by_event = {r["decision_id"]: r for r in ledger["revision_resolutions"]}
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    for paper in ("A", "B"):
        pins = ledger["inputs"][paper]
        fresh = json.loads(production_paths[paper].read_bytes())
        frozen = json.loads(Path(pins["production_report_path"]).read_bytes())
        gold = json.loads(Path(pins["gold_path"]).read_bytes())
        require(fresh["source_hash"] == pins["source_sha256"], "Fresh report source mismatch")
        require(fresh["gold_hash"] == pins["gold_sha256"], "Fresh report gold mismatch")
        old_predictions = {p["key"]: p for p in frozen["predictions"]}
        new_predictions = {p["key"]: p for p in fresh["predictions"]}
        require(new_predictions.keys() == old_predictions.keys(), "Production candidates changed")
        for key, prediction in new_predictions.items():
            for field in ("type", "text", "page", "bbox"):
                require(prediction[field] == old_predictions[key][field], "Production source changed")
        require(fresh["metrics"] == frozen["metrics"], "Frozen comparison metrics changed")
        require([m["gold_id"] for m in fresh["matches"]] == [g["id"] for g in gold["items"]],
                "A gold item was dropped")
        checks = {
            name: metric["rate"] is not None and metric["rate"] >= THRESHOLDS[name]
            or name == "equations" and metric["total"] == 0
            and bool(gold.get("explicit_absences", {}).get("numbered_equations"))
            for name, metric in fresh["metrics"].items()
        }
        require(checks == fresh["metric_checks"], "Threshold comparison changed")
        effective = latest(ledger["decisions"], paper)
        original = latest(ledger["decisions"], paper, production_only=True)
        require({e["prediction_key"] for e in original.values()} == old_predictions.keys(),
                "Human review does not cover every frozen prediction")
        require({e["gold_item_id"] for e in effective.values() if e.get("gold_item_id")}
                == {g["id"] for g in gold["items"]}, "Human review misses a gold item")
        require(counts(effective.values()) == {
            k: ledger["progress"][paper][k] for k in ("ACCEPT", "REVISE", "REJECT")
        }, "Effective decision totals disagree")
        item_audit = []
        for item_id, event in original.items():
            resolution = resolution_by_event.get(event["decision_id"], {})
            explanation_only = resolution.get("status") == "RESOLVED_EXPLANATION_ONLY"
            correction_required = event["decision"] in {"REVISE", "REJECT"} and not explanation_only
            current = effective[item_id]
            item_audit.append({
                "review_item_id": item_id, "gold_item_id": event.get("gold_item_id"),
                "prediction_key": event["prediction_key"],
                "production_decision_id": event["decision_id"],
                "production_decision": event["decision"],
                "current_review_view_decision_id": current["decision_id"],
                "current_review_view_decision": current["decision"],
                "current_review_target": current.get("review_target", "ORIGINAL_PRODUCTION"),
                "explanation_only": explanation_only,
                "production_correction_required": correction_required,
                "correction_resolution": resolution or current.get("human_correction"),
                "application_correction_applied": False,
            })
        blockers = [i for i in item_audit if i["production_correction_required"]]
        anomalies = list(latest(ledger["parser_anomaly_decisions"], paper).values())
        require(all(a["frozen_sample_scoring_affected"] is False for a in anomalies),
                "Parser anomaly scope changed")
        quantities = list(latest(ledger["quantity_decisions"], paper).values())
        require(len(quantities) == sum(len(g["quantities"]) for g in gold["items"]),
                "Quantity review coverage mismatch")
        # Counts are review coverage, not a relabeling of model precision/type accuracy.
        # Apply the existing protocol, not an added "all items ACCEPT" rule.
        # Remediation findings remain separate from threshold decisions.
        if paper == "A":
            require(original["a-limitation"]["decision"] == "REJECT"
                    and original["a-prediction-c935580f9be3"]["decision"] == "REVISE"
                    and "object_type" in original["a-prediction-c935580f9be3"]
                    ["human_correction"]["target_fields"], "A precision-bound evidence changed")
            identity_type_errors = 2
            precision_upper_bound = (len(original) - identity_type_errors) / len(original)
            protocol_human_checks = {
                "identity_type_precision_can_meet_frozen_threshold":
                    precision_upper_bound >= THRESHOLDS["precision"],
            }
        else:
            require(original["b-contact-method"]["decision"] == "REVISE"
                    and original["b-stability"]["decision"] == "REVISE",
                    "B source-fidelity failure evidence changed")
            protocol_human_checks = {"frozen_unresolved_glyph_clause_satisfied": False}
        human_audit_pass = all(protocol_human_checks.values())
        packaged_production = output / ("production-" + paper.lower() + ".json")
        packaged_production.write_bytes(production_paths[paper].read_bytes())
        result = {
            "schema_version": 1, "paper": paper,
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "FROZEN_SAMPLE_AND_DOCUMENTED_PARSER_ANOMALY",
            "inputs": pins,
            "human_ledger_sha256_at_evaluation": digest(ledger_path),
            "human_decision_history_sha256": history_digest(ledger),
            "production_rerun_path": str(packaged_production),
            "production_rerun_sha256": digest(packaged_production),
            "isolated_runtime_report_path": str(production_paths[paper]),
            "production_pipeline_modified": False, "frozen_gold_modified": False,
            "thresholds": THRESHOLDS, "model_source_metrics": fresh["metrics"],
            "model_metric_checks": checks,
            "model_sampled_measurements_pass": fresh["sampled_measurements_pass"],
            "human_source_review": "COMPLETE",
            "effective_review_view_counts": counts(effective.values()),
            "original_production_decision_counts": counts(original.values()),
            "explicit_original_production_acceptance_coverage": {
                "accepted": counts(original.values())["ACCEPT"], "total": len(original),
                "is_protocol_precision": False,
            },
            "quantity_review_counts": counts(quantities),
            "item_audit": item_audit,
            "unapplied_production_corrections": blockers,
            "parser_anomaly_review": [{
                "review_item_id": a["review_item_id"], "decision_id": a["decision_id"],
                "decision": a["decision"], "human_correction": a["human_correction"],
                "frozen_sample_scoring_affected": False,
                "application_correction_applied": False,
            } for a in anomalies],
            "reviewed_source_audit_pass": human_audit_pass,
            "protocol_human_checks": protocol_human_checks,
            "overall_reviewed_gate": "PASS" if human_audit_pass
                and fresh["sampled_measurements_pass"] else "FAIL",
            "scientific_validity": "NOT_ASSESSED", "gate_b": "NOT_STARTED",
            "browser_journey": {"status": "HISTORICAL_PASS_NOT_RERUN",
                               "reported_on": "2026-10-05",
                               "path": "evals/reports/dual-paper/browser.json"},
            "notes": [
                "Frozen model source comparisons retain their original denominators and review origin.",
                "Human review is complete; explicit production source/type corrections remain unapplied.",
                "Explanation-only revisions are resolved without inventing production ACCEPT or extraction errors.",
                "Accepted expanded method/visual equation review views are not production parser repairs.",
                "Section anomalies are reported separately and do not alter frozen scientific windows.",
                "No application DB review, VERIFIED record or scientific acceptance was created.",
            ],
        }
        if paper == "A":
            result["human_identity_type_precision_upper_bound"] = {
                "passed_at_most": len(original) - identity_type_errors,
                "total": len(original), "rate_at_most": precision_upper_bound,
                "threshold": THRESHOLDS["precision"], "threshold_can_be_met": False,
                "excluded_items": ["a-limitation", "a-prediction-c935580f9be3"],
                "note": "Even granting every other item, these explicit identity/type objections fail 90%.",
            }
        else:
            result["source_fidelity_failure_basis"] = (
                "Frozen protocol: unresolved numeric/glyph ambiguity fails that gold item; "
                "b-contact-method overbar and b-stability subscripts remain uncorrected in production. "
                "16/18 is explicit acceptance coverage, not an invented type-accuracy score."
            )
        result_path = output / ("paper-" + paper.lower() + ".json")
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports[paper] = {"path": str(result_path), "sha256": digest(result_path),
                          "overall_reviewed_gate": result["overall_reviewed_gate"]}
    manifest = {
        "schema_version": 1, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_path": str(Path(__file__).absolute()),
        "evaluator_sha256": digest(Path(__file__)),
        "human_decision_history_sha256": history_digest(ledger),
        "readonly_snapshot_objects_checked": checked_snapshots,
        "thresholds": THRESHOLDS, "papers": reports,
        "gate_b": "NOT_STARTED", "application_corrections_applied": False,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--production-a", type=Path, required=True)
    parser.add_argument("--production-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root, {"A": args.production_a, "B": args.production_b}, args.output)))
