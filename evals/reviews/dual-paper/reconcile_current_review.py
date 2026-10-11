"""Deterministic equivalence proposals, never human decisions or application reviews.

Only whitespace and a literal heading observed in the current source are removed
for statement comparison. Numbers, units, qualifiers and mathematical signs are
never normalized away. Frozen scoring and immutable human history stay separate.
"""

import argparse
import json
import re
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_corrected_source_gate import digest, inspect_current, read
from reevaluate_human_source_gate import (
    THRESHOLDS,
    check_snapshots,
    history_digest,
    latest,
    require,
)


def compact(text):
    return " ".join(text.split())


def without_heading(text, titles):
    removed = []
    for title in titles:
        if text.startswith(title + "\n"):
            text = text[len(title) + 1 :]
            removed.append(title)
    return text, removed


def compared_text(node, evidence):
    titles = [
        t for a in evidence for t in a.get("section_titles", []) if t in a["text"]
    ]
    text, removed = without_heading(node["text"], titles)
    if node["type"] in {"PAPER", "SECTION"}:
        from papergraph.source_patterns import TEMPLATE_HEADER

        first, separator, rest = text.partition("\n")
        if (
            separator
            and TEMPLATE_HEADER.fullmatch(first.strip())
            and any(a["text"].startswith(first + "\n") for a in evidence)
        ):
            text = rest
            removed.append(first)
    return text, removed


def rows(database, table):
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(r) for r in connection.execute(f"SELECT * FROM {table}")]


def decode(node):
    node = dict(node)
    if isinstance(node["provenance"], str):
        node["provenance"] = json.loads(node["provenance"])
    return node


def anchor_identity(anchor):
    bbox = anchor["bbox"]
    if isinstance(bbox, str):
        bbox = json.loads(bbox)
    return {
        k: anchor[k]
        for k in ("source_hash", "page_number", "start_char", "end_char", "text")
    } | {"bbox": bbox}


def statement_notes(node, anchors):
    result = []
    for a in anchors:
        start = a["text"].find(node["text"])
        if start < 0:
            continue  # Compilations retain their full snapshots separately.
        end = start + len(node["text"])
        for note in a.get("notation", []):
            if note["start_char"] < end and note["end_char"] > start:
                result.append(note | {"anchor_id": a["id"]})
    return result


def compare(old, new, old_anchors, new_anchors):
    old_text, stripped = compared_text(old, new_anchors)
    new_text, new_stripped = compared_text(new, new_anchors)
    raw_source_equal = sorted(
        json.dumps(anchor_identity(a), sort_keys=True) for a in old_anchors
    ) == sorted(json.dumps(anchor_identity(a), sort_keys=True) for a in new_anchors)
    same_wording = compact(old_text) == compact(new_text)
    differences = [
        "node." + k for k in ("type", "layer", "epistemic_status") if old[k] != new[k]
    ]
    if not same_wording:
        differences.append("node.scientific_wording")
    if not raw_source_equal:
        differences.append("source.identity_or_wording_or_geometry")
    # Equality includes every scientific character after a proven literal heading
    # removal. This is stronger than merely comparing a list of numeric tokens.
    proof = {
        "same_source_hash": {a["source_hash"] for a in old_anchors}
        == {a["source_hash"] for a in new_anchors},
        "original_source_wording_page_offsets_bbox_equal": raw_source_equal,
        "literal_heading_removed": stripped,
        "current_literal_heading_removed": new_stripped,
        "normalized_statement_equal": same_wording,
        "normalized_old_statement": compact(old_text),
        "normalized_new_statement": compact(new_text),
        "same_scientific_type": old["type"] == new["type"],
        "same_layer": old["layer"] == new["layer"],
        "same_epistemic_status": old["epistemic_status"] == new["epistemic_status"],
        "quantities_units_qualifiers_all_characters_preserved": same_wording,
        "numeric_tokens": re.findall(
            r"[+−-]?\d+(?:\.\d+)?(?:[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)?", old_text
        ),
        "current_statement_notation": statement_notes(new, new_anchors),
        "notation_is_separate_pdf_display_not_rewritten_source": True,
        "equivalence_scope": "Original statement attribution and localization. New notation display, type revisions and prior unresolved corrections are not accepted by this proposal.",
        "source_typography_uncertainty": [
            {"anchor_id": a["id"], "issues": a.get("notation_issues", [])}
            for a in new_anchors
            if a.get("notation_issues")
        ],
    }
    metadata = [
        k
        for k in ("id", "paper_id", "version", "label", "created_by")
        if old.get(k) != new.get(k)
    ]
    if stripped or new_stripped:
        metadata.append("literal_heading_separation")
    if any(
        a.get("notation") or a.get("notation_issues") or a.get("section_titles")
        for a in new_anchors
    ):
        metadata.append("source_display_or_heading_metadata")
    if [a["id"] for a in old_anchors] != [a["id"] for a in new_anchors]:
        metadata.append("source_anchor_ids")
    category = (
        "MATERIAL_CONTENT_OR_TYPE_CHANGE"
        if differences
        else ("NONMATERIAL_METADATA_CHANGE" if metadata else "EXACT_MATCH")
    )
    return category, proof, differences, metadata


def find_old(node, evidence, old_nodes, old_anchors):
    text, _ = compared_text(node, evidence)
    possible = []
    for old in old_nodes:
        old_text, _ = compared_text(old, evidence)
        if compact(old_text) != compact(text):
            continue
        original = [old_anchors[k] for k in old["provenance"]]
        if {a["source_hash"] for a in original} == {
            a["source_hash"] for a in evidence
        } and (
            {a["page_number"] for a in original} == {a["page_number"] for a in evidence}
        ):
            possible.append(old)
    typed = [n for n in possible if n["type"] == node["type"]]
    return typed or possible


def fingerprint_map(root, database):
    sys.path.insert(0, str(root / "backend"))
    from papergraph.models import NodeRow
    from papergraph.provenance import fingerprint
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    engine = create_engine(f"sqlite:///file:{database.as_posix()}?mode=ro&uri=true")
    with Session(engine) as session:
        result = {
            n.id: fingerprint(session, n) for n in session.scalars(select(NodeRow))
        }
    engine.dispose()
    return result


def reconcile(root, productions, output):
    ledger_path = root / "evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json"
    ledger = read(ledger_path)
    require(
        digest(ledger_path)
        == "4c9220d03943ddc25583270fd2c08a1f20aa0853c518860db7cef9c31f7e9d99",
        "Immutable ledger changed",
    )
    historical = read(
        root / "evals/reports/dual-paper/human-reviewed-20261011-r2/manifest.json"
    )
    require(
        history_digest(ledger) == historical["human_decision_history_sha256"],
        "Immutable history changed",
    )
    canonical = root / "backend/data/papergraph.db"
    with sqlite3.connect(canonical.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        snapshot_count = check_snapshots(connection, ledger)
    old_nodes_all = [decode(n) for n in rows(canonical, "knowledge_nodes")]
    old_anchors = {a["id"]: a for a in rows(canonical, "source_anchors")}
    old_fingerprints = fingerprint_map(root, canonical)
    output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    for letter, path in productions.items():
        pins = ledger["inputs"][letter]
        pdf = root / "backend/data/documents" / (pins["source_sha256"] + ".pdf")
        require(digest(pdf) == pins["source_sha256"], "Original PDF changed")
        for name in ("gold", "prediction_review", "production_report"):
            require(
                digest(Path(pins[name + "_path"])) == pins[name + "_sha256"],
                "Frozen input changed: " + name,
            )
        current = read(path)
        require(current["source_hash"] == pins["source_sha256"], "Source changed")
        database, paper, nodes, anchors, spans, review_count = inspect_current(path)
        require(review_count == 0, "Unexpected application reviews")
        new_fingerprints = fingerprint_map(root, database)
        old_paper_ids = {
            a["paper_id"]
            for a in old_anchors.values()
            if a["source_hash"] == pins["source_sha256"]
        }
        originals = [n for n in old_nodes_all if n["paper_id"] in old_paper_ids]
        events = latest(ledger["decisions"], letter, production_only=True)
        events_by_node = {e["local_node_id"]: e for e in events.values()}
        graph_mapping = []
        paired = set()
        for node in nodes.values():
            evidence = [anchors[k] for k in node["provenance"]]
            possible = find_old(node, evidence, originals, old_anchors)
            record = {
                "new_node_id": node["id"],
                "new_version": node["version"],
                "new_type": node["type"],
                "new_text": node["text"],
                "current_evidence_fingerprint": new_fingerprints[node["id"]],
                "source_hash": paper["source_hash"],
                "current_source_snapshots": evidence,
                "current_human_decision": None,
                "human_acceptance_inherited": False,
                "candidate_old_node_ids": [n["id"] for n in possible],
            }
            if len(possible) == 1:
                old = possible[0]
                category, proof, differences, metadata = compare(
                    old, node, [old_anchors[k] for k in old["provenance"]], evidence
                )
                paired.add(old["id"])
                event = events_by_node.get(old["id"])
                record |= {
                    "category": category,
                    "old_node_id": old["id"],
                    "old_version": old["version"],
                    "old_type": old["type"],
                    "old_text": old["text"],
                    "old_evidence_fingerprint": old_fingerprints[old["id"]],
                    "previous_decision_id": event["decision_id"] if event else None,
                    "previous_decision": event["decision"] if event else None,
                    "equivalence_proof": proof,
                    "material_differences": differences,
                    "metadata_differences": metadata,
                    "binding_status": "PROPOSED_EQUIVALENCE_AWAITING_EXPLICIT_POLICY_CONFIRMATION"
                    if not differences and event
                    else "NO_REVIEW_REBOUND",
                }
            else:
                record["category"] = "AMBIGUOUS_MATCH" if possible else "NEW_CANDIDATE"
            graph_mapping.append(record)
        for old in originals:
            if old["id"] not in paired:
                event = events_by_node.get(old["id"])
                graph_mapping.append(
                    {
                        "category": "REMOVED_CANDIDATE",
                        "old_node_id": old["id"],
                        "old_type": old["type"],
                        "old_text": old["text"],
                        "old_version": old["version"],
                        "old_evidence_fingerprint": old_fingerprints[old["id"]],
                        "previous_decision_id": event["decision_id"] if event else None,
                        "previous_decision": event["decision"] if event else None,
                        "original_source_snapshots": [
                            old_anchors[k] for k in old["provenance"]
                        ],
                        "source_preserved": all(
                            any(
                                a["page_number"] == s["page_number"]
                                and a["text"] == s["text"]
                                for s in spans.values()
                            )
                            for a in [old_anchors[k] for k in old["provenance"]]
                        ),
                        "human_acceptance_inherited": False,
                    }
                )
        mappings_by_new = {
            m["new_node_id"]: m for m in graph_mapping if "new_node_id" in m
        }
        old_edges = [
            e
            for e in rows(canonical, "knowledge_edges")
            if e["paper_id"] in old_paper_ids
        ]
        edge_mapping = []
        paired_edges = set()
        for edge in rows(database, "knowledge_edges"):
            source = mappings_by_new[edge["source_node_id"]]
            target = mappings_by_new[edge["target_node_id"]]
            possible = [
                e
                for e in old_edges
                if e["source_node_id"] == source.get("old_node_id")
                and e["target_node_id"] == target.get("old_node_id")
                and e["relation_type"] == edge["relation_type"]
            ]
            record = {
                "new_edge": edge,
                "human_acceptance_inherited": False,
                "scope": "Structural containment identity only; no scientific dependence asserted",
            }
            if len(possible) == 1:
                old = possible[0]
                paired_edges.add(old["id"])
                old_evidence = [old_anchors[k] for k in json.loads(old["provenance"])]
                new_evidence = [anchors[k] for k in json.loads(edge["provenance"])]
                equal = sorted(
                    json.dumps(anchor_identity(a), sort_keys=True) for a in old_evidence
                ) == sorted(
                    json.dumps(anchor_identity(a), sort_keys=True) for a in new_evidence
                )
                material = not equal or any(
                    m["category"] == "MATERIAL_CONTENT_OR_TYPE_CHANGE"
                    for m in (source, target)
                )
                record |= {
                    "old_edge": old,
                    "original_source_equivalent": equal,
                    "category": "MATERIAL_CONTENT_OR_TYPE_CHANGE"
                    if material
                    else "NONMATERIAL_METADATA_CHANGE",
                }
            else:
                record["category"] = "AMBIGUOUS_MATCH" if possible else "NEW_CANDIDATE"
            edge_mapping.append(record)
        edge_mapping.extend(
            {
                "old_edge": e,
                "category": "REMOVED_CANDIDATE",
                "human_acceptance_inherited": False,
            }
            for e in old_edges
            if e["id"] not in paired_edges
        )
        predictions = []
        for p in current["predictions"]:
            m = mappings_by_new[p["node_id"]]
            unknown = p["adjudication"]["origin"] == "UNREVIEWED"
            reason = None
            if unknown:
                reason = (
                    "Literal source heading removal changed the SHA-256 prediction key; same scientific statement/type."
                    if m.get("equivalence_proof", {}).get("literal_heading_removed")
                    else "Scientific type changed, so the frozen type+text prediction key no longer matches."
                    if m["category"] == "MATERIAL_CONTENT_OR_TYPE_CHANGE"
                    else "New source-anchored candidate has no entry in immutable prediction adjudication."
                )
            predictions.append(
                {
                    "prediction_key": p["key"],
                    "node_id": p["node_id"],
                    "type": p["type"],
                    "text": p["text"],
                    "page": p["page"],
                    "bbox": p["bbox"],
                    "category": m["category"],
                    "previous_decision_id": m.get("previous_decision_id"),
                    "previous_decision": m.get("previous_decision"),
                    "old_node_id": m.get("old_node_id"),
                    "frozen_adjudication": p["adjudication"],
                    "why_counted_incorrect": reason,
                    "current_human_decision": None,
                    "human_acceptance_inherited": False,
                    "genuine_false_positive_established": False,
                }
            )
        quantity_mapping = []
        for e in latest(ledger["quantity_decisions"], letter).values():
            p = e["reviewed_snapshot"]["current_source_anchor"]
            matching = [
                a for a in anchors.values() if anchor_identity(a) == anchor_identity(p)
            ]
            quantity_mapping.append(
                {
                    "old_decision_id": e["decision_id"],
                    "old_decision": e["decision"],
                    "gold_item_id": e["gold_item_id"],
                    "quantity_index": e["quantity_index"],
                    "category": "NONMATERIAL_METADATA_CHANGE"
                    if len(matching) == 1
                    else "AMBIGUOUS_MATCH",
                    "old_source_snapshot": p,
                    "new_source_snapshots": matching,
                    "quantity_and_context": e["reviewed_snapshot"].get("gold_quantity"),
                    "same_original_source_wording_page_offsets_bbox": len(matching)
                    == 1,
                    "human_acceptance_inherited": False,
                }
            )
        anomaly_mapping = []
        for e in latest(ledger["parser_anomaly_decisions"], letter).values():
            snapshot = e["reviewed_snapshot"]
            seen = set()
            for instance in [snapshot, *snapshot.get("related_header_instances", [])]:
                a = instance["current_source_anchor"]
                if a["id"] in seen:
                    continue
                seen.add(a["id"])
                source = [
                    s
                    for s in spans.values()
                    if s["text"] == a["text"] and s["page_number"] == a["page_number"]
                ]
                anomaly_mapping.append(
                    {
                        "old_decision_id": e["decision_id"],
                        "old_decision": e["decision"],
                        "old_node_id": instance["current_local_node"]["id"],
                        "category": "REMOVED_CANDIDATE",
                        "old_scientific_section_removed": not any(
                            n["type"] == "SECTION" and n["text"] == a["text"]
                            for n in nodes.values()
                        ),
                        "original_source_snapshot": a,
                        "current_source_spans": source,
                        "source_preserved": len(source) == 1,
                        "human_acceptance_inherited": False,
                    }
                )
        result = {
            "paper": letter,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_hash": paper["source_hash"],
            "gold_sha256": pins["gold_sha256"],
            "original_pdf_path": str(pdf),
            "pipeline_version": current["pipeline_version"],
            "parser_version": current["parser_version"],
            "production_path": str(path),
            "production_sha256": digest(path),
            "isolated_database": str(database),
            "thresholds": THRESHOLDS,
            "frozen_model_metrics": current["metrics"],
            "metric_checks": current["metric_checks"],
            "graph_node_mapping": graph_mapping,
            "graph_edge_mapping": edge_mapping,
            "prediction_mapping": predictions,
            "quantity_mapping": quantity_mapping,
            "parser_anomaly_mapping": anomaly_mapping,
            "mapping_counts": dict(Counter(m["category"] for m in graph_mapping)),
            "prediction_mapping_counts": dict(
                Counter(p["category"] for p in predictions)
            ),
            "gold_misses": [m for m in current["matches"] if not m["same_type"]],
            "integrity": current["integrity"],
            "application_verification_records": review_count,
            "current_human_precision": None,
            "current_human_review": "PENDING_TARGETED_REVIEW",
            "prior_human_review": "COMPLETE_UNCHANGED",
            "human_acceptance_inherited": False,
            "overall_reviewed_gate": "FAIL",
            "scientific_validity": "NOT_ASSESSED",
            "gate_b": "NOT_STARTED",
            "binding_policy": "Frozen protocol has no explicit automatic equivalence-rebinding procedure. Proposals need one explicit scoped confirmation, not repeated scientific review of equivalent items.",
        }
        (output / f"paper-{letter.lower()}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        shutil.copyfile(path, output / f"production-{letter.lower()}.json")
        summaries[letter] = {
            k: result[k]
            for k in (
                "mapping_counts",
                "prediction_mapping_counts",
                "frozen_model_metrics",
                "overall_reviewed_gate",
                "gold_misses",
            )
        }
    manifest = {
        "scope": "TECHNICAL_RECONCILIATION_PROPOSALS_BEFORE_CURRENT_HUMAN_DECISIONS",
        "human_ledger_sha256": digest(ledger_path),
        "human_decision_history_sha256": history_digest(ledger),
        "unchanged_historical_snapshots_checked": snapshot_count,
        "thresholds": THRESHOLDS,
        "papers": summaries,
        "human_decisions_created": 0,
        "application_reviews_created": 0,
        "scientific_validity": "NOT_ASSESSED",
        "gate_b": "NOT_STARTED",
        "artifacts": {p.name: digest(p) for p in output.iterdir() if p.is_file()},
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({l: s["prediction_mapping_counts"] for l, s in summaries.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-a", type=Path, required=True)
    parser.add_argument("--production-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reconcile(
        Path(__file__).resolve().parents[3],
        {"A": args.production_a.resolve(), "B": args.production_b.resolve()},
        args.output.resolve(),
    )
