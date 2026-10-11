"""Persist the user's finite E0 authorization after read-only staleness checks.

This writes a separate evaluation audit. It never creates a scientific decision,
modifies immutable history, changes application objects or promotes REVISE.
"""

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_corrected_source_gate import digest, inspect_current, read
from reconcile_current_review import compare, decode, fingerprint_map, rows
from reevaluate_human_source_gate import check_snapshots, history_digest, require


def bind(root, authorization, output):
    require(not output.exists(), "Current audit already exists; do not overwrite it")
    response = authorization.read_text(encoding="utf-8-sig")
    require(
        response.lstrip().startswith("E0 ACCEPT."),
        "No explicit E0 ACCEPT in supplied response",
    )
    report = root / "evals/reports/dual-paper/reconciliation-20261011-r4"
    manifest = read(report / "manifest.json")
    for name, expected in manifest["artifacts"].items():
        require(digest(report / name) == expected, "Proposal artifact changed: " + name)
    for name, expected in manifest["implementation_sha256"].items():
        require(
            digest(root / name) == expected,
            "Production/proposal implementation changed: " + name,
        )
    ledger_path = root / "evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json"
    ledger = read(ledger_path)
    require(
        digest(ledger_path) == manifest["human_ledger_sha256"],
        "Immutable ledger changed",
    )
    require(
        history_digest(ledger) == manifest["human_decision_history_sha256"],
        "History changed",
    )
    events = {e["decision_id"]: e for e in ledger["decisions"]}
    canonical = root / "backend/data/papergraph.db"
    with sqlite3.connect(canonical.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        snapshots_checked = check_snapshots(connection, ledger)
    old_nodes = {n["id"]: decode(n) for n in rows(canonical, "knowledge_nodes")}
    old_anchors = {a["id"]: a for a in rows(canonical, "source_anchors")}
    old_fingerprints = fingerprint_map(root, canonical)
    bindings = []
    current_inputs = {}
    for letter in "AB":
        d = read(report / f"paper-{letter.lower()}.json")
        production = Path(d["production_path"])
        require(
            digest(production) == d["production_sha256"],
            "Current production report changed",
        )
        require(
            digest(Path(d["original_pdf_path"])) == d["source_hash"],
            "Original source changed",
        )
        pins = ledger["inputs"][letter]
        for name in ("gold", "prediction_review", "production_report"):
            require(
                digest(Path(pins[name + "_path"])) == pins[name + "_sha256"],
                "Frozen input changed",
            )
        database, paper, nodes, anchors, _, reviews = inspect_current(production)
        require(reviews == 0, "Unexpected current application verification records")
        current_fingerprints = fingerprint_map(root, database)
        current_inputs[letter] = {
            "proposal_report_path": str(report / f"paper-{letter.lower()}.json"),
            "proposal_report_sha256": digest(report / f"paper-{letter.lower()}.json"),
            "production_path": str(production),
            "production_sha256": digest(production),
            "database": str(database),
            "source_hash": d["source_hash"],
            "gold_sha256": d["gold_sha256"],
            "parser_version": paper["parser_version"],
            "pipeline_version": d["pipeline_version"],
        }
        for p in d["prediction_mapping"]:
            if p["category"] != "NONMATERIAL_METADATA_CHANGE":
                continue
            m = next(
                m
                for m in d["graph_node_mapping"]
                if m.get("new_node_id") == p["node_id"]
            )
            event = events[p["previous_decision_id"]]
            require(
                not event.get("review_target"),
                "A draft/view acceptance cannot bind production",
            )
            require(
                event["scope"] == "SOURCE_ATTRIBUTION", "Wrong original review scope"
            )
            old, current = old_nodes[m["old_node_id"]], nodes[p["node_id"]]
            require(old["version"] == m["old_version"], "Old version changed")
            require(current["version"] == m["new_version"], "Current version changed")
            require(
                old_fingerprints[old["id"]] == m["old_evidence_fingerprint"],
                "Old evidence changed",
            )
            require(
                current_fingerprints[current["id"]]
                == m["current_evidence_fingerprint"],
                "Current evidence changed",
            )
            original_source = [old_anchors[k] for k in old["provenance"]]
            current_source = [anchors[k] for k in current["provenance"]]
            category, proof, changes, metadata = compare(
                old, current, original_source, current_source
            )
            require(
                category == "NONMATERIAL_METADATA_CHANGE" and not changes,
                "Material/ambiguous object cannot use E0",
            )
            require(
                all(
                    proof[k]
                    for k in (
                        "same_source_hash",
                        "original_source_wording_page_offsets_bbox_equal",
                        "normalized_statement_equal",
                        "same_scientific_type",
                        "same_layer",
                        "same_epistemic_status",
                        "quantities_units_qualifiers_all_characters_preserved",
                    )
                ),
                "Equivalence proof failed",
            )
            require(
                event["local_node_id"] == old["id"]
                and event["decision"] == p["previous_decision"],
                "Decision identity changed",
            )
            bindings.append(
                {
                    "binding_id": f"E0-{letter}-{current['id']}",
                    "authorization_id": "current-E0-20261011",
                    "paper": letter,
                    "current_prediction_key": p["prediction_key"],
                    "original_decision_id": event["decision_id"],
                    "original_decision": event["decision"],
                    "original_decision_scope": event["scope"],
                    "original_ledger_sha256": digest(ledger_path),
                    "old_node_id": old["id"],
                    "old_node_version": old["version"],
                    "old_evidence_fingerprint": old_fingerprints[old["id"]],
                    "current_node_id": current["id"],
                    "current_node_version": current["version"],
                    "current_evidence_fingerprint": current_fingerprints[current["id"]],
                    "source_hash": paper["source_hash"],
                    "original_source_anchor_ids": old["provenance"],
                    "current_source_anchor_ids": current["provenance"],
                    "scientific_type": current["type"],
                    "layer": current["layer"],
                    "epistemic_status": current["epistemic_status"],
                    "equivalence_proof": proof,
                    "metadata_differences": metadata,
                    "binding_status": "BOUND_WITHIN_ORIGINAL_SCOPE",
                    "binding_effect": "REFERENCE_ORIGINAL_ACCEPT_ONLY"
                    if event["decision"] == "ACCEPT"
                    else "PRESERVE_ORIGINAL_REVISE_WITHOUT_PROMOTION",
                    "existing_resolution_ids": [
                        r["resolution_id"]
                        for r in ledger["revision_resolutions"]
                        if r["decision_id"] == event["decision_id"]
                    ],
                    "new_human_acceptance_created": False,
                    "excluded_scope": [
                        "NEW_SCIENTIFIC_CONTENT",
                        "TYPE_CHANGE",
                        "SYMBOL_REVISION",
                        "AI_DERIVATION",
                        "MATHEMATICAL_RECONSTRUCTION",
                        "SCIENTIFIC_VALIDITY",
                    ],
                }
            )
    require(
        Counter(b["paper"] for b in bindings) == {"A": 17, "B": 18},
        "Unexpected binding set",
    )
    require(
        Counter(b["original_decision"] for b in bindings)
        == {"ACCEPT": 30, "REVISE": 5},
        "Original decisions changed",
    )
    now = datetime.now(timezone.utc).isoformat()
    audit = {
        "schema_version": 1,
        "created_at_utc": now,
        "updated_at_utc": now,
        "scope": "CURRENT_SOURCE_ATTRIBUTION_REVIEW_WITH_FINITE_E0_BINDINGS",
        "historical_ledger_path": str(ledger_path),
        "historical_ledger_sha256": digest(ledger_path),
        "historical_decision_history_sha256": history_digest(ledger),
        "proposal_manifest_path": str(report / "manifest.json"),
        "proposal_manifest_sha256": digest(report / "manifest.json"),
        "authorizations": [
            {
                "authorization_id": "current-E0-20261011",
                "decision": "ACCEPT",
                "authorization_scope": "FINITE_AUDITABLE_EQUIVALENCE_MAPPING_ONLY",
                "review_origin": "EXPLICIT_USER_DOCUMENT_RESPONSE",
                "recorded_at_utc": now,
                "response_path": str(authorization),
                "response_sha256": digest(authorization),
                "user_response_verbatim": response,
                "reviewer": {
                    "kind": "conversation_user",
                    "personal_name": None,
                    "identity_note": "Document supplied by user in this chat; no authenticated or personal identity inferred.",
                },
                "binding_count": 35,
                "new_scientific_decisions_created": 0,
            }
        ],
        "current_inputs": current_inputs,
        "equivalence_bindings": bindings,
        "decisions": [],
        "presentation_order": ["A1", "A2a", "A2b", "A3", "A4", "B1", "B2"],
        "cursor": {"item": "A1", "status": "AWAITING_EXPLICIT_USER_DECISION"},
        "historical_snapshots_checked": snapshots_checked,
        "current_human_metrics": {"A": None, "B": None},
        "reviewed_gate": {
            "A": "FAIL",
            "B": "FAIL",
            "reason": "TARGETED_REVIEW_NOT_COMPLETE",
        },
        "scientific_validity": "NOT_ASSESSED",
        "application_reviews_created": 0,
        "gate_b": "NOT_STARTED",
    }
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "bindings": len(bindings),
                "original_decisions": dict(
                    Counter(b["original_decision"] for b in bindings)
                ),
                "new_scientific_decisions": 0,
                "next": "A1",
                "history_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bind(
        Path(__file__).resolve().parents[3],
        args.authorization.resolve(),
        args.output.resolve(),
    )
