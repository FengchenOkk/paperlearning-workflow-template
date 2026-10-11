"""Replay grouping changes in new isolated DB copies, preserving existing identities.

Fresh ordinary uploads independently check the resulting scientific/source content.
This never mutates canonical graphs, old evaluations or reviews, and cannot accept
a revision. Unchanged E0 objects retain exactly their existing IDs/versions/evidence.
"""

import argparse
import copy
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from audit_corrected_source_gate import digest, inspect_current, read
from reconcile_current_review import fingerprint_map


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def source_signature(node, anchors):
    return (
        node["type"],
        node["layer"],
        node["text"],
        node["epistemic_status"],
        tuple(
            (
                anchors[a]["page_number"],
                tuple(anchors[a]["bbox"]),
                anchors[a]["text"],
                anchors[a]["source_hash"],
            )
            for a in node["provenance"]
        ),
    )


def apply(root, runtime, output):
    import sys

    sys.path.insert(0, str(root / "backend"))
    from papergraph.database import Database
    from papergraph.extraction import document_candidates
    from papergraph.integrity import report
    from papergraph.models import EdgeRow, EvidenceRow, JobRow, NodeRow, timestamp
    from papergraph.parser import MuPDFParser
    from papergraph.worker import stable
    from sqlalchemy import delete, select

    audit_path = root / "evals/reviews/dual-paper/CURRENT_SOURCE_REVIEW.json"
    audit = read(audit_path)
    assert audit["cursor"] == {"item": "A2a", "status": "REVISION_IN_PROGRESS"}
    assert audit["decisions"][-1]["decision"] == "REVISE"
    old_audit_hash = digest(audit_path)
    proposal_path = Path(audit["proposal_manifest_path"])
    assert digest(proposal_path) == audit["proposal_manifest_sha256"]
    for name, expected in read(proposal_path)["artifacts"].items():
        assert digest(proposal_path.parent / name) == expected, name
    old_inputs = copy.deepcopy(audit["current_inputs"])
    browser = read(runtime / "browser-05/results.json")
    public_browser = read(runtime / "public-browser-02/results.json")
    assert all(item["status"] == "PASS" for item in browser)
    assert public_browser["status"] == "PASS"
    ledger = read(Path(audit["historical_ledger_path"]))
    for letter in "AB":
        for kind in ("gold", "prediction_review", "production_report"):
            frozen = ledger["inputs"][letter]
            assert digest(Path(frozen[kind + "_path"])) == frozen[kind + "_sha256"]
    output.mkdir(parents=True, exist_ok=False)
    changes = {}
    new_inputs = {}
    current_snapshots = {}
    for letter in "AB":
        pin = old_inputs[letter]
        old_production = Path(pin["production_path"])
        assert digest(old_production) == pin["production_sha256"]
        old_db, paper, old_nodes, old_anchors, old_spans, count = inspect_current(
            old_production
        )
        assert count == 0
        source_pdf = root / "backend/data/documents" / (pin["source_hash"] + ".pdf")
        assert digest(source_pdf) == pin["source_hash"]
        fresh_production = runtime / f"fresh-{letter.lower()}.json"
        _, _, fresh_nodes, fresh_anchors, _, fresh_count = inspect_current(
            fresh_production
        )
        assert fresh_count == 0
        current_production = runtime / f"current-{letter.lower()}.json"
        current_runtime = runtime / f"current-{letter.lower()}-runtime"
        current_runtime.mkdir(exist_ok=False)
        destination_db = current_runtime / "graph.db"
        with (
            sqlite3.connect(old_db.as_uri() + "?mode=ro", uri=True) as source,
            sqlite3.connect(destination_db) as target,
        ):
            source.backup(target)
        shutil.copytree(old_db.parent / "documents", current_runtime / "documents")
        parsed = list(MuPDFParser().pages(source_pdf.read_bytes(), 500))
        for page in parsed:
            for block in page.blocks:
                span = old_spans[
                    stable(paper["id"], f"span:{page.number}:{block.order}")
                ]
                assert span["text"] == block.text and span["bbox"] == list(block.bbox)
                assert span["kind"] == block.kind
                assert span["notation"] == [
                    n.model_dump(mode="json") for n in block.notation
                ]
                assert span["notation_issues"] == block.notation_issues
                assert span["section_titles"] == list(block.section_titles)
        candidates = document_candidates(parsed)
        db = Database(f"sqlite:///{destination_db.as_posix()}")
        updated = []
        added = []
        expected_ids = {paper["id"]}
        with db.session() as session:
            for (page_number, order), entries in candidates.items():
                span_id = stable(paper["id"], f"span:{page_number}:{order}")
                for index, candidate in enumerate(entries):
                    node_id = stable(paper["id"], f"node:{span_id}:{index}")
                    expected_ids.add(node_id)
                    anchor_ids = [
                        stable(
                            paper["id"],
                            f"anchor:{stable(paper['id'], f'span:{p}:{o}')}",
                        )
                        for p, o in candidate.source_blocks
                    ] or [stable(paper["id"], f"anchor:{span_id}")]
                    fields = {
                        "type": candidate.type,
                        "layer": candidate.layer,
                        "text": candidate.text,
                        "epistemic_status": candidate.epistemic_status,
                        "provenance": anchor_ids,
                    }
                    node = session.get(NodeRow, node_id)
                    if node is not None and all(
                        getattr(node, key) == value for key, value in fields.items()
                    ):
                        continue
                    assert candidate.type == "PROCESS", (
                        "Grouping may not modify individual scientific candidates"
                    )
                    label = " ".join(candidate.text.split())
                    label = label[:110] + ("…" if len(label) > 110 else "")
                    if node is None:
                        node = NodeRow(
                            id=node_id,
                            paper_id=paper["id"],
                            label=label,
                            confidence=0.6,
                            verification_status="CANDIDATE",
                            created_by="local-rule-extractor-v5",
                            uncertainty_reason=candidate.reason,
                            **fields,
                        )
                        session.add(node)
                        session.flush()
                        added.append(node_id)
                        edge = EdgeRow(
                            id=stable(paper["id"], f"edge:{node_id}"),
                            paper_id=paper["id"],
                            source_node_id=paper["id"],
                            target_node_id=node_id,
                            relation_type="CONTAINS",
                            confidence=1,
                            verification_status="SUPPORTED",
                            provenance=anchor_ids,
                            created_by="document-parser",
                            epistemic_status="PAPER_EXPLICIT",
                        )
                        session.add(edge)
                    else:
                        assert (
                            node.type == "PROCESS"
                            and node.verification_status == "CANDIDATE"
                        )
                        before_version = node.version
                        for key, value in fields.items():
                            setattr(node, key, value)
                        node.label = label
                        node.uncertainty_reason = candidate.reason
                        node.created_by = "local-rule-extractor-v5"
                        node.version += 1
                        node.updated_at = timestamp()
                        updated.append(
                            {
                                "node_id": node_id,
                                "old_version": before_version,
                                "new_version": node.version,
                            }
                        )
                        edge = session.get(
                            EdgeRow, stable(paper["id"], f"edge:{node_id}")
                        )
                        assert edge is not None
                        edge.provenance = anchor_ids
                        edge.version += 1
                        edge.updated_at = timestamp()
                        session.execute(
                            delete(EvidenceRow).where(
                                EvidenceRow.supports_object_id == node_id
                            )
                        )
                    for anchor_id in anchor_ids:
                        session.add(
                            EvidenceRow(
                                id=stable(
                                    paper["id"], f"evidence:{node_id}:{anchor_id}"
                                ),
                                supports_object_id=node_id,
                                anchor_id=anchor_id,
                            )
                        )
            assert set(old_nodes).issubset(expected_ids), (
                "Unexpected removal outside revision"
            )
            for job in session.scalars(select(JobRow)):
                job.pipeline_version = "source-graph-v6"
                job.updated_at = timestamp()
            session.flush()
            integrity = report(session, paper["id"]).model_dump(mode="json")
            assert integrity["structurally_valid"]
            assert not [i for i in integrity["issues"] if i["severity"] == "ERROR"]
        db.engine.dispose()
        # Inspect the copied DB without requiring the report to exist first.
        _, current_paper, nodes, anchors, spans, current_count = inspect_current(
            current_production
        )
        assert (
            current_count == 0
            and current_paper == paper
            and spans == old_spans
            and anchors == old_anchors
        )
        fresh_signatures = {
            source_signature(n, fresh_anchors): n["id"] for n in fresh_nodes.values()
        }
        current_signatures = {
            source_signature(n, anchors): n["id"] for n in nodes.values()
        }
        assert len(fresh_signatures) == len(fresh_nodes) and len(
            current_signatures
        ) == len(nodes)
        assert set(fresh_signatures) == set(current_signatures), (
            "Fresh upload/replay scientific content differs"
        )
        remap = {
            fresh_id: current_signatures[signature]
            for signature, fresh_id in fresh_signatures.items()
        }
        scored = read(fresh_production)
        for item in scored["matches"] + scored["predictions"]:
            if item["node_id"]:
                item["node_id"] = remap[item["node_id"]]
        scored["integrity"] = integrity
        scored["evaluation_mode"] = (
            "ISOLATED_INCREMENTAL_GROUPING_REPLAY_CHECKED_AGAINST_FRESH_ORDINARY_UPLOAD"
        )
        scored["scoring_origin"] = (
            "FROZEN_MODEL_KEY_COMPARISON_NOT_CURRENT_HUMAN_ADJUDICATION"
        )
        scored["fresh_upload_reference"] = {
            "path": str(fresh_production),
            "sha256": digest(fresh_production),
        }
        scored["replay_base"] = {
            "path": str(old_production),
            "sha256": digest(old_production),
        }
        write_new(current_production, scored)
        fps = fingerprint_map(root, destination_db)
        old_fps = fingerprint_map(root, old_db)
        changed_ids = {item["node_id"] for item in updated}
        for node_id in set(old_nodes) - changed_ids:
            assert nodes[node_id] == old_nodes[node_id], node_id
            assert fps[node_id] == old_fps[node_id], node_id
        bound = [b for b in audit["equivalence_bindings"] if b["paper"] == letter]
        for binding in bound:
            assert (
                nodes[binding["current_node_id"]]["version"]
                == binding["current_node_version"]
            )
            assert (
                fps[binding["current_node_id"]]
                == binding["current_evidence_fingerprint"]
            )
        for decision in audit["decisions"]:
            if decision["paper"] == letter and decision["decision"] == "ACCEPT":
                assert (
                    nodes[decision["current_node_id"]]["version"]
                    == decision["current_node_version"]
                )
                assert (
                    fps[decision["current_node_id"]]
                    == decision["current_evidence_fingerprint"]
                )
        old_keys = {p["key"] for p in read(old_production)["predictions"]}
        new_keys = {p["key"] for p in scored["predictions"]}
        changes[letter] = {
            "updated_processes": updated,
            "added_process_ids": added,
            "source_rows_preserved": True,
            "unchanged_nodes_and_fingerprints": len(old_nodes) - len(changed_ids),
            "existing_E0_bindings_preserved_without_rebinding": len(bound),
            "new_window_prediction_keys": sorted(new_keys - old_keys),
            "removed_window_prediction_keys": sorted(old_keys - new_keys),
            "fresh_upload_content_equivalent": True,
            "metrics": scored["metrics"],
            "integrity": integrity,
        }
        new_inputs[letter] = {
            **pin,
            "production_path": str(current_production),
            "production_sha256": digest(current_production),
            "database": str(destination_db),
            "pipeline_version": "source-graph-v6",
            "revision_report_path": str(output / "revision.json"),
        }
        current_snapshots[letter] = (nodes, anchors, fps, scored)
    nodes, anchors, fps, scored = current_snapshots["A"]
    fabrication = nodes["796f256a-90e7-5843-b1ef-f78416790de6"]
    assert fabrication["version"] == 2 and "Electrical" not in fabrication["text"]
    optical = next(
        n
        for n in nodes.values()
        if n["type"] == "PROCESS" and "PL and Raman spectra" in n["text"]
    )
    electrical = next(
        n
        for n in nodes.values()
        if n["type"] == "PROCESS"
        and "The sheet resistance of pristine graphene" in n["text"]
    )
    groups = []
    for role, node in (
        ("FABRICATION", fabrication),
        ("OPTICAL_CHARACTERIZATION", optical),
        ("ELECTRICAL_CHARACTERIZATION_AND_SAMPLE_PREPARATION", electrical),
    ):
        prediction = next(
            (p for p in scored["predictions"] if p["node_id"] == node["id"]), None
        )
        groups.append(
            {
                "role": role,
                "node": node,
                "source_anchors": [anchors[k] for k in node["provenance"]],
                "evidence_fingerprint": fps[node["id"]],
                "prediction_key": prediction["key"] if prediction else None,
                "inside_frozen_precision_window": prediction is not None,
                "decision": None,
            }
        )
    revision = {
        "revision_id": "A2a-grouping-revision-20261011-1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_by_decision_id": audit["decisions"][-1]["decision_id"],
        "user_response_verbatim": audit["decisions"][-1]["user_response_verbatim"],
        "base_inputs": old_inputs,
        "revised_inputs": new_inputs,
        "changes": changes,
        "A2a_review_groups": groups,
        "human_decision": None,
        "scientific_validity": "NOT_ASSESSED",
        "application_reviews_created": 0,
        "canonical_graph_modified": False,
        "historical_ledger_sha256": audit["historical_ledger_sha256"],
        "validation": {
            "backend_tests": {"passed": 40},
            "frontend_tests": {"passed": 8},
            "ruff": "PASS",
            "mypy": "PASS",
            "browser": browser,
            "public_browser": public_browser,
            "reconciliation_guards": {"passed": 7},
        },
        "limitations": [
            "Incremental evaluation DB copies retain unchanged scientific-object identities and generators; new/changed PROCESS use v5 extractor.",
            "Fresh upload references are independently generated v6 graphs with different UUIDs; they are not human-reviewed.",
            "All additional objects outside the three displayed A2a groups remain unreviewed.",
            "No precision credit is created by a grouping repair; current human evaluation waits for explicit decisions.",
        ],
    }
    assert (
        digest(Path(audit["historical_ledger_path"]))
        == audit["historical_ledger_sha256"]
    )
    write_new(output / "revision.json", revision)
    card = "# A2a 修订1：制作与表征分组（待审核）\n\n"
    card += "用户原话：`revise，进行分组边界，表征和制作进行分组`。旧对象 v1 的 REVISE 已保存。本次修订仍是草稿，三个组都未被 ACCEPT。\n\n"
    card += "所有对象均为 PROCESS / SEMANTIC / AI_INTERPRETATION / CANDIDATE；均来自原始 PDF 第8页。单句 METHOD 候选及原始源块未改写。以下分组不推导统一顺序，也不声称完整执行配方。\n\n"
    names = {
        "FABRICATION": "制作与材料处理",
        "OPTICAL_CHARACTERIZATION": "光学表征",
        "ELECTRICAL_CHARACTERIZATION_AND_SAMPLE_PREPARATION": "电学表征及其测试样品制备",
    }
    for group in groups:
        node = group["node"]
        card += f"## {names[group['role']]}\n\nID `{node['id']}`，version {node['version']}，fingerprint `{group['evidence_fingerprint']}`。\n\n```text\n{node['text']}\n```\n\n"
        for anchor in group["source_anchors"]:
            card += f"Source anchor `{anchor['id']}`，page {anchor['page_number']}，字符 [{anchor['start_char']}, {anchor['end_char']})，bbox `{anchor['bbox']}`。源块证据精度仍为 TEXT_BLOCK。\n\n"
    evidence_dir = root / ".runtime/gate-a-reconciliation-20261011/review-a2a"
    card += f"[原始PDF 第8页]({(root / 'backend/data/documents' / (audit['current_inputs']['A']['source_hash'] + '.pdf')).as_posix()})\n\n"
    for name, caption in (
        ("exfoliation-context.png", "机械剥离和干法转移"),
        ("transfer-oxidation-context.png", "转移、去残留、氧化与光学表征"),
        ("electrical-contact-context.png", "片电阻表征和电接触制备"),
    ):
        card += f"![{caption}]({(evidence_dir / name).as_posix()})\n\n"
    card += "修订差异：制作组保留剥离、PC转移、氯仿去残留和氧化；移出的电接触原句保留在明确用于片电阻表征的组中；厚度光学核对、PL/Raman及PL mapping单列光学表征组。制作组旧ID保留并升至v2，另两个组是新候选；新对象没有旧 ACCEPT。\n\n"
    card += "技术建议：ACCEPT 本次三个组的来源归属与分组边界。需要用户判断制作/表征是否已分清、测量样品限定是否准确、原始条件/数值/单位是否忠实。本建议不是人工决定。请回复 A2a ACCEPT / REVISE / REJECT；不包含其他制作/表征候选或科学有效性。\n\n"
    card += "40项后端测试、8项前端测试、Ruff/mypy及公开PDF/两篇原始PDF浏览器旅程通过（包括PROCESS每个证据锚点跳转、反向选择和刷新）。原冻结模型比较报告保留；本次新模型键比较A16/22、B17/18，当前人工指标未计算，Gate A仍FAIL、Gate B未开始。\n"
    card_path = root / "evals/reviews/dual-paper/A2a-REVISION-1-REVIEW.md"
    with card_path.open("x", encoding="utf-8") as stream:
        stream.write(card)
    pending = copy.deepcopy(audit["current_item_snapshot"])
    pending.update(
        {
            "decision": None,
            "revision_id": revision["revision_id"],
            "revision_number": 1,
            "revision_requested_by": revision["requested_by_decision_id"],
            "current_node": fabrication,
            "current_source_anchors": groups[0]["source_anchors"],
            "current_prediction_key": groups[0]["prediction_key"],
            "current_evidence_fingerprint": fps[fabrication["id"]],
            "pipeline_version": "source-graph-v6",
            "review_groups": groups,
            "review_card_path": str(card_path),
            "review_card_sha256": digest(card_path),
            "technical_recommendation": {
                "origin": "MODEL_RECOMMENDATION_NOT_HUMAN_DECISION",
                "recommendation": "ACCEPT",
                "scope": "Only the three displayed source-attributed groups and their boundary; no scientific validity.",
            },
            "changes": [
                "Fabrication and characterization are separate groups.",
                "Electrical contacts remain with the stated graphene sheet-resistance measurement samples.",
                "Optical thickness, spectra and mapping are retained as a separate characterization group.",
            ],
        }
    )
    audit.setdefault("revision_history", []).append(
        {
            "revision_id": revision["revision_id"],
            "previous_audit_sha256": old_audit_hash,
            "report_path": str(output / "revision.json"),
            "report_sha256": digest(output / "revision.json"),
            "old_inputs": old_inputs,
            "new_inputs": new_inputs,
            "human_decision": None,
        }
    )
    audit["current_inputs"] = new_inputs
    audit["current_item_snapshot"] = pending
    audit["cursor"] = {
        "item": "A2a",
        "status": "AWAITING_EXPLICIT_USER_DECISION_ON_REVISION",
    }
    audit["updated_at_utc"] = revision["created_at_utc"]
    assert digest(audit_path) == old_audit_hash
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    implementation = {
        name: digest(root / name)
        for name in (
            "backend/papergraph/extraction.py",
            "backend/papergraph/models.py",
            "backend/papergraph/worker.py",
            "backend/scripts/run_source_gate_e2e.py",
            "backend/tests/test_production_corrections.py",
            "frontend/src/App.tsx",
            "evals/reviews/dual-paper/apply_grouping_revision.py",
        )
    }
    write_new(
        output / "manifest.json",
        {
            "scope": "A2a_GROUPING_REVISION_DRAFT_NOT_ACCEPTED",
            "revision_sha256": digest(output / "revision.json"),
            "review_card_sha256": digest(card_path),
            "implementation_sha256": implementation,
            "historical_ledger_sha256": audit["historical_ledger_sha256"],
            "original_proposal_manifest_sha256": audit["proposal_manifest_sha256"],
        },
    )
    audit["current_revision_manifest_path"] = str(output / "manifest.json")
    audit["current_revision_manifest_sha256"] = digest(output / "manifest.json")
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "cursor": audit["cursor"],
                "A2a_revision_groups": len(groups),
                "existing_E0_bindings_preserved": 35,
                "A1_ACCEPT_unchanged": True,
                "human_metrics": audit["current_human_metrics"],
                "changes": {
                    letter: {
                        key: value
                        for key, value in change.items()
                        if key not in ("metrics", "integrity")
                    }
                    for letter, change in changes.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    apply(args.root.resolve(), args.runtime.resolve(), args.output.resolve())
