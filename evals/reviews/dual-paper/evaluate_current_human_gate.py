"""Score the finite current human audit separately from immutable model reports.

Read-only application access; historical decisions are references, never rewritten.
Existing validated production/browser results are reused, not rerun.
"""

import argparse
import copy
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_corrected_source_gate import digest, inspect_current, read
from reconcile_current_review import fingerprint_map
from reevaluate_human_source_gate import THRESHOLDS, check_snapshots, history_digest, require


def ratio(passed, total):
    return {"passed": passed, "total": total, "rate": passed / total if total else None}


def core(anchor):
    value = {k: anchor[k] for k in ("page_number", "start_char", "end_char", "text", "source_hash", "bbox")}
    if isinstance(value["bbox"], str):
        value["bbox"] = json.loads(value["bbox"])
    return value


def adjudicate(predictions, bindings, decisions, historical, resolutions):
    """An unreviewed object gets zero credit; explanation-only is not an ACCEPT."""
    bound = {b["current_node_id"]: b for b in bindings}
    direct = {}
    for event in decisions:
        if event["decision"] != "ACCEPT":
            continue
        direct[event["current_node_id"]] = event
        for obj in event.get("accepted_objects", []):
            require(obj["decision"] == "ACCEPT", "Unaccepted group in an ACCEPT event")
            direct[obj["node_id"]] = event
    result = []
    for prediction in predictions:
        node_id = prediction["node_id"]
        event, binding = direct.get(node_id), bound.get(node_id)
        passed, basis, decision, refs = False, "UNREVIEWED", None, []
        if event:
            require(event["scope"] == "SOURCE_ATTRIBUTION", "Wrong direct review scope")
            passed, basis, decision = True, "EXPLICIT_CURRENT_USER_ACCEPT", "ACCEPT"
            refs = [event["decision_id"]]
        elif binding:
            old = historical[binding["original_decision_id"]]
            require(old["decision"] == binding["original_decision"], "Original decision altered")
            require(old["scope"] == binding["original_decision_scope"] == "SOURCE_ATTRIBUTION", "Scope expanded")
            decision, refs = old["decision"], [binding["binding_id"], old["decision_id"]]
            if decision == "ACCEPT":
                passed, basis = True, "E0_ORIGINAL_ACCEPT_REFERENCE"
            elif decision == "REVISE":
                resolved = [r for r in resolutions if r["decision_id"] == old["decision_id"]
                            and r["status"] == "RESOLVED_EXPLANATION_ONLY"
                            and r.get("source_or_type_revision_requested") is False
                            and r.get("requires_pipeline_fix") is False
                            and r["scope"] == "SOURCE_ATTRIBUTION"
                            and r.get("user_clarification_verbatim")]
                if resolved:
                    passed, basis = True, "E0_EXPLANATION_ONLY_RESOLUTION"
                    refs += [r["resolution_id"] for r in resolved]
        result.append({"node_id": node_id, "prediction_key": prediction["key"],
                       "type": prediction["type"], "correct_identity_type": passed,
                       "basis": basis, "decision_label": decision, "audit_references": refs,
                       "original_decision_rewritten": False})
    return result


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def evaluate(root, output, fidelity_path):
    audit_path = root / "evals/reviews/dual-paper/CURRENT_SOURCE_REVIEW.json"
    audit_hash, audit = digest(audit_path), read(audit_path)
    require(audit["cursor"]["status"] == "TARGETED_REVIEW_COMPLETE_EVALUATION_PENDING", "Reviews not ready")
    require({d["item_id"] for d in audit["decisions"] if d["decision"] == "ACCEPT"}
            == set(audit["presentation_order"]), "Targeted review missing")
    ledger_path = Path(audit["historical_ledger_path"])
    ledger = read(ledger_path)
    require(digest(ledger_path) == audit["historical_ledger_sha256"], "Historical ledger changed")
    require(history_digest(ledger) == audit["historical_decision_history_sha256"], "History changed")
    with sqlite3.connect((root / "backend/data/papergraph.db").as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        checked = check_snapshots(connection, ledger)
    require(checked == 77, "Historical snapshots differ")
    proposal = Path(audit["proposal_manifest_path"])
    require(digest(proposal) == audit["proposal_manifest_sha256"], "Proposal changed")
    for name, expected in read(proposal)["artifacts"].items():
        require(digest(proposal.parent / name) == expected, "Proposal artifact changed: " + name)
    manifest_path = Path(audit["current_revision_manifest_path"])
    manifest = read(manifest_path)
    require(digest(manifest_path) == audit["current_revision_manifest_sha256"], "Current manifest changed")
    require(digest(manifest_path.parent / "revision.json") == manifest["revision_sha256"], "Revision changed")
    revision = read(manifest_path.parent / "revision.json")
    for name, expected in manifest["implementation_sha256"].items():
        require(digest(root / name) == expected, "Current implementation changed: " + name)
    authorization = next(a for a in audit["authorizations"] if a["authorization_id"] == "current-E0-20261011")
    require(authorization["decision"] == "ACCEPT" and authorization["binding_count"] == 35, "Missing E0 authorization")
    require(digest(Path(authorization["response_path"])) == authorization["response_sha256"], "Authorization changed")
    require(len(audit["equivalence_bindings"]) == 35, "Finite binding count changed")
    fidelity = read(fidelity_path)
    require(fidelity["origin"] == "MODEL_SOURCE_REVIEW" and fidelity["human_decision_created"] is False, "Wrong fidelity origin")
    historical = {d["decision_id"]: d for d in ledger["decisions"]}
    quantity_events = {d["decision_id"]: d for d in ledger["quantity_decisions"]}
    sys.path.insert(0, str(root / "backend"))
    from papergraph.notation import notation_text
    from papergraph.schemas import SourceNotation
    from apply_grouping_revision import source_signature

    reports = {}
    for letter in "AB":
        pin, old_pin = audit["current_inputs"][letter], ledger["inputs"][letter]
        for kind in ("gold", "prediction_review", "production_report"):
            require(digest(Path(old_pin[kind + "_path"])) == old_pin[kind + "_sha256"], "Frozen input changed")
        production_path = Path(pin["production_path"])
        require(digest(production_path) == pin["production_sha256"], "Current production changed")
        require(digest(Path(pin["proposal_report_path"])) == pin["proposal_report_sha256"], "Mapping changed")
        require(digest(root / "backend/data/documents" / (pin["source_hash"] + ".pdf")) == pin["source_hash"], "PDF changed")
        production, gold = read(production_path), read(Path(old_pin["gold_path"]))
        require(production["gold_hash"] == old_pin["gold_sha256"], "Gold mismatch")
        database, paper, nodes, anchors, spans, review_count = inspect_current(production_path)
        require(review_count == 0 and paper["source_hash"] == pin["source_hash"], "Application review/source state changed")
        fingerprints = fingerprint_map(root, database)
        fresh_pin = production["fresh_upload_reference"]
        fresh_path = Path(fresh_pin["path"])
        require(digest(fresh_path) == fresh_pin["sha256"], "Fresh upload report changed")
        _, _, fresh_nodes, fresh_anchors, _, fresh_reviews = inspect_current(fresh_path)
        require(fresh_reviews == 0, "Fresh unreviewed upload unexpectedly reviewed")
        require({source_signature(n, anchors) for n in nodes.values()}
                == {source_signature(n, fresh_anchors) for n in fresh_nodes.values()}, "Current/fresh source content differs")
        require(all(n["verification_status"] == "CANDIDATE" or n["type"] in {"PAPER", "SECTION"}
                    and n["verification_status"] == "SUPPORTED" for n in nodes.values()), "Invalid scientific verification state")
        bindings = [b for b in audit["equivalence_bindings"] if b["paper"] == letter]
        events = [e for e in audit["decisions"] if e["paper"] == letter and e["decision"] == "ACCEPT"]
        for b in bindings:
            node = nodes[b["current_node_id"]]
            require(node["version"] == b["current_node_version"] and fingerprints[node["id"]] == b["current_evidence_fingerprint"], "Stale E0 binding")
            require(node["type"] == b["scientific_type"] and node["layer"] == b["layer"]
                    and node["epistemic_status"] == b["epistemic_status"], "E0 type/scope changed")
        for e in events:
            node, snapshot = nodes[e["current_node_id"]], e["reviewed_snapshot"]
            require(node == snapshot["current_node"] and node["version"] == e["current_node_version"]
                    and fingerprints[node["id"]] == e["current_evidence_fingerprint"], "Stale current decision")
            require([anchors[k] for k in node["provenance"]] == snapshot["current_source_anchors"], "Reviewed anchor changed")
            require(e["user_response_verbatim"] and e["review_origin"] == "EXPLICIT_USER_CHAT_RESPONSE", "No real response")
            if snapshot.get("review_card_path"):
                require(digest(Path(snapshot["review_card_path"])) == snapshot["review_card_sha256"], "Review card changed")
            for image in snapshot.get("pdf_evidence", []):
                require(digest(Path(image["path"])) == image["sha256"], "Review image changed")
            for group in snapshot.get("review_groups", []):
                obj = nodes[group["node"]["id"]]
                require(obj == group["node"] and fingerprints[obj["id"]] == group["evidence_fingerprint"], "Accepted group stale")
                require([anchors[k] for k in obj["provenance"]] == group["source_anchors"], "Group anchors stale")
            if snapshot.get("notation_view"):
                source = snapshot["current_source_anchors"][0]
                offset = source["text"].find(node["text"])
                require(offset >= 0, "Notation sentence not contiguous")
                notes = [SourceNotation.model_validate(n).model_copy(update={"start_char": n["start_char"] - offset,
                         "end_char": n["end_char"] - offset}) for n in source["notation"]
                         if offset <= n["start_char"] and n["end_char"] <= offset + len(node["text"])]
                require(notation_text(node["text"], notes) == snapshot["notation_view"]["display"], "Notation display changed")
        for p in production["predictions"]:
            require(p["text"] == nodes[p["node_id"]]["text"] and p["type"] == nodes[p["node_id"]]["type"], "Prediction/DB mismatch")
        judgements = adjudicate(production["predictions"], bindings, events, historical, ledger["revision_resolutions"])
        correct = {j["node_id"] for j in judgements if j["correct_identity_type"]}
        matches = production["matches"]
        require([m["gold_id"] for m in matches] == [g["id"] for g in gold["items"]], "Gold denominator changed")
        metric = copy.deepcopy(production["metrics"])
        metric["precision"] = ratio(len(correct), len(judgements))
        matched = [m for m in matches if m["node_id"]]
        metric["recall"] = ratio(sum(m["same_type"] and m["correct_source"] and m["node_id"] in correct for m in matches), len(matches))
        metric["type_accuracy"] = ratio(sum(m["same_type"] and m["node_id"] in correct for m in matched), len(matched))
        for name, field in (("anchors", "correct_source"), ("pages", "correct_source")):
            metric[name] = ratio(sum(m[field] and m["node_id"] in correct for m in matched), len(matched))
        mappings = read(Path(pin["proposal_report_path"]))
        quantity_audit = []
        for q in mappings["quantity_mapping"]:
            original = quantity_events[q["old_decision_id"]]
            match = next(m for m in matches if m["gold_id"] == q["gold_item_id"])
            source = [anchors[k] for k in nodes[match["node_id"]]["provenance"]]
            require(any(core(s) == core(q["old_source_snapshot"]) for s in source), "Quantity source/context changed")
            require(original["original_quantity"] == q["quantity_and_context"], "Quantity changed")
            passed = original["decision"] == "ACCEPT" and match["quantities"][q["quantity_index"]]["pass"] and match["node_id"] in correct
            quantity_audit.append({"gold_id": q["gold_item_id"], "quantity_index": q["quantity_index"],
                                   "original_decision_id": original["decision_id"], "correct": bool(passed),
                                   "source_context_unchanged": True, "new_accept_created": False})
        require(len(quantity_audit) == sum(len(g["quantities"]) for g in gold["items"]), "Quantity denominator changed")
        metric["quantities"] = ratio(sum(q["correct"] for q in quantity_audit), len(quantity_audit))
        anomaly_audit = []
        for finding in mappings["parser_anomaly_mapping"]:
            require(finding["old_scientific_section_removed"] and finding["source_preserved"], "Parser anomaly unresolved")
            for span in finding["current_source_spans"]:
                require(spans[span["id"]] == span, "Parser span changed")
                require(not any(n["type"] == "SECTION" and n["text"] == span["text"] for n in nodes.values()), "False SECTION persists")
            anomaly_audit.append({"original_decision_id": finding["old_decision_id"], "original_decision": finding["old_decision"],
                                  "technical_source_role_correction": "APPLIED_SOURCE_PRESERVED", "new_accept_created": False})
        browser = next(b for b in revision["validation"]["browser"] if b["source_hash"] == pin["source_hash"])
        require(browser["status"] == "PASS" and all(j["result"] == "PASS" for j in browser["journeys"]), "Browser journey failed")
        if letter == "B":
            eq = next(m for m in matches if m["gold_id"] == "b-equation-1")
            eq_node = nodes[eq["node_id"]]
            eq_check = fidelity["equation_1"]
            prior_eq = historical[eq_check["historical_decision_id"]]
            require(prior_eq["decision"] == "ACCEPT" and prior_eq["reviewed_visual_transcription"] == eq_check["reviewed_visual_transcription"], "Equation acceptance scope changed")
            require(eq_node["version"] == eq_check["current_node_version"] and fingerprints[eq_node["id"]] == eq_check["current_evidence_fingerprint"], "Equation changed")
            require(core(anchors[eq_node["provenance"][0]]) == core(prior_eq["reviewed_snapshot"]["current_source_anchor"]), "Equation source changed")
            require(digest(Path(eq_check["image_path"])) == eq_check["image_sha256"], "Equation image changed")
            require(eq_check["rendered_source_agrees_with_prior_transcription"] is True
                    and eq_check["unresolved_selected_source_glyph"] is False, "Selected equation glyph unresolved")
        checks = {name: (m["rate"] is not None and m["rate"] >= THRESHOLDS[name])
                  or name == "equations" and m["total"] == 0 and bool(gold.get("explicit_absences", {}).get("numbered_equations"))
                  for name, m in metric.items()}
        integrity_ok = production["integrity"]["structurally_valid"] and not any(i["severity"] == "ERROR" for i in production["integrity"]["issues"])
        passed = all(checks.values()) and integrity_ok
        reports[letter] = {
            "schema_version": 1, "paper": letter, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "FROZEN_SOURCE_WINDOWS_AND_GOLD_NOT_FULL_DOCUMENT", "thresholds": THRESHOLDS,
            "inputs": pin, "current_review_audit_sha256": audit_hash,
            "historical_ledger_sha256": audit["historical_ledger_sha256"],
            "human_source_metrics": metric, "human_metric_checks": checks,
            "model_key_metrics_unchanged": production["metrics"], "model_key_checks_unchanged": production["metric_checks"],
            "model_key_sample_pass": production["sampled_measurements_pass"],
            "prediction_adjudications": judgements, "adjudication_basis_counts": dict(Counter(j["basis"] for j in judgements)),
            "gold_matches": matches, "quantity_audit": quantity_audit, "parser_anomaly_audit": anomaly_audit,
            "integrity": production["integrity"], "browser": {"status": "EXISTING_CURRENT_V6_PASS_REUSED", "source_hash": pin["source_hash"],
                         "revision_manifest_sha256": audit["current_revision_manifest_sha256"], "rerun_this_turn": False},
            "source_fidelity_audit_path": str(fidelity_path), "source_fidelity_audit_sha256": digest(fidelity_path),
            "overall_reviewed_gate": "PASS" if passed else "FAIL", "failure_reasons": [k for k,v in checks.items() if not v],
            "scientific_validity": "NOT_ASSESSED", "application_reviews_created": 0, "gate_b": "NOT_STARTED",
            "limitations": ["Scores concern the frozen sample; accepted objects outside windows do not inflate denominators.",
                            "Explanation-only REVISE remains REVISE; correct identity/type is not explicit acceptance coverage.",
                            "Original source/glyph evidence can be reviewed while automatic formula reconstruction remains unknown.",
                            "Additional full-document candidates are unreviewed; source attribution does not verify science."]}
    require(digest(audit_path) == audit_hash, "Audit changed during evaluation")
    output.mkdir(parents=True, exist_ok=False)
    for letter, report in reports.items():
        write_new(output / f"paper-{letter.lower()}.json", report)
    result = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "evaluator_path": str(Path(__file__).resolve()), "evaluator_sha256": digest(Path(__file__)),
              "current_review_audit_sha256": audit_hash, "historical_ledger_sha256": audit["historical_ledger_sha256"],
              "historical_snapshots_unchanged": checked, "current_revision_manifest_sha256": audit["current_revision_manifest_sha256"],
              "thresholds": THRESHOLDS, "source_fidelity_sha256": digest(fidelity_path),
              "papers": {l: {"path": str(output / f"paper-{l.lower()}.json"), "sha256": digest(output / f"paper-{l.lower()}.json"),
                             "overall_reviewed_gate": r["overall_reviewed_gate"]} for l,r in reports.items()},
              "gate_b": "NOT_STARTED", "application_reviews_created": 0, "scientific_validity": "NOT_ASSESSED"}
    write_new(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-fidelity", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.root, args.output, args.source_fidelity), ensure_ascii=False, indent=2))
