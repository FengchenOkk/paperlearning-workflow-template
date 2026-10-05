import hashlib
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from papergraph.models import (
    AnchorRow,
    ClaimRow,
    EquationRow,
    FigureRow,
    NodeRow,
    SpanRow,
    VerificationRow,
)

from .test_journey import upload_and_process


def entities(client: TestClient, content: bytes):
    payload = upload_and_process(client, content)
    paper = payload["paper"]
    graph = client.get(f"/api/papers/{paper['id']}/graph").json()
    return (
        paper,
        next(n for n in graph["nodes"] if n["type"] == "METHOD"),
        next(n for n in graph["nodes"] if n["type"] == "RESULT"),
    )


def review(
    client: TestClient, paper: dict, obj: dict, kind: str = "nodes", scientific: bool = False
):
    return client.post(
        f"/api/{kind}/{obj['id']}/verification",
        json={
            "decision": "VERIFIED",
            "reviewer": "isolated-test-reviewer",
            "reason": "Test-only scoped review; no real scientific acceptance.",
            "source_hash": paper["source_hash"],
            "expected_version": obj["version"],
            "scope": "SCIENTIFIC_VALIDITY" if scientific else "SOURCE_ATTRIBUTION",
            "scientific_basis": "Synthetic fixture assertion used solely to test review invariants."
            if scientific
            else None,
        },
    )


def test_claim_equation_figure_are_durable_canonical_subtypes(client: TestClient):
    with pymupdf.open() as doc:
        page = doc.new_page()
        for y, text in [
            (80, "We claim that the controlled test signal follows this relation."),
            (150, "x = y + 2 (1)"),
            (220, "Figure 1: A controlled parser fixture caption."),
        ]:
            page.insert_text((72, y), text, fontsize=11)
        payload = upload_and_process(client, bytes(doc.tobytes()))
    paper_id = payload["paper"]["id"]
    nodes = client.get(f"/api/papers/{paper_id}/graph").json()["nodes"]
    assert {n["type"] for n in nodes} >= {"CLAIM", "EQUATION", "FIGURE"}
    for kind, model in [("CLAIM", ClaimRow), ("EQUATION", EquationRow), ("FIGURE", FigureRow)]:
        node = next(n for n in nodes if n["type"] == kind)
        bundle = client.get(f"/api/nodes/{node['id']}/evidence").json()
        obj = bundle["scientific_object"]
        anchor = bundle["evidence"][0]["anchor"]
        assert obj["node_id"] == node["id"] and obj["source_anchor_id"] == anchor["id"]
        assert anchor["localization_precision"] == "TEXT_BLOCK"
        with client.app.state.database.session() as session:
            assert session.get(model, node["id"]) is not None
        if kind == "CLAIM":
            assert obj["support_strength"] == "NOT_ASSESSED" and obj["evidence_node_ids"] == []
        elif kind == "EQUATION":
            assert obj["original_expression"] == node["text"] and obj["equation_number"] == "1"
            assert (
                obj["latex"] is None
                and obj["symbols"] == []
                and obj["mathematical_meaning"] is None
            )
        else:
            assert obj["caption_explicit"] == node["text"] and obj["figure_number"] == "1"
            assert (
                obj["visual_anchor_id"] is None
                and obj["visual_observations"] == []
                and obj["interpretations"] == []
            )
    report = client.get(f"/api/papers/{paper_id}/integrity").json()
    assert report["structurally_valid"] and report["scientific_validity"] == "NOT_ASSESSED"


def test_ontology_rejects_wrong_layer_and_relation_endpoint(
    client: TestClient, synthetic_pdf: bytes
):
    paper, method, result = entities(client, synthetic_pdf)
    node = {
        "type": "CLAIM",
        "layer": "SEMANTIC",
        "label": "Wrong layer",
        "text": "Candidate only",
        "anchor_ids": method["provenance"],
        "uncertainty_reason": "Test incompatible ontology",
    }
    assert client.post(f"/api/papers/{paper['id']}/nodes", json=node).status_code == 422
    edge = {
        "source_node_id": method["id"],
        "target_node_id": result["id"],
        "relation_type": "ASSUMES",
        "anchor_ids": method["provenance"],
    }
    assert client.post(f"/api/papers/{paper['id']}/edges", json=edge).status_code == 409


def test_mixed_prerequisite_inverse_cycle_is_rejected(client: TestClient, synthetic_pdf: bytes):
    paper, method, result = entities(client, synthetic_pdf)
    edge = {
        "source_node_id": method["id"],
        "target_node_id": result["id"],
        "relation_type": "PREREQUISITE_OF",
        "anchor_ids": method["provenance"],
    }
    assert client.post(f"/api/papers/{paper['id']}/edges", json=edge).status_code == 201
    assert (
        client.post(
            f"/api/papers/{paper['id']}/edges", json={**edge, "relation_type": "DEPENDS_ON"}
        ).status_code
        == 409
    )
    # Correct inverse describes the same direction; it is not a cycle.
    assert (
        client.post(
            f"/api/papers/{paper['id']}/edges",
            json={
                **edge,
                "relation_type": "DEPENDS_ON",
                "source_node_id": result["id"],
                "target_node_id": method["id"],
            },
        ).status_code
        == 201
    )


def test_source_review_cannot_verify_scientific_relationship(
    client: TestClient, synthetic_pdf: bytes
):
    paper, method, result = entities(client, synthetic_pdf)
    assert review(client, paper, method).json()["verification_scope"] == "SOURCE_ATTRIBUTION"
    edge = client.post(
        f"/api/papers/{paper['id']}/edges",
        json={
            "source_node_id": method["id"],
            "target_node_id": result["id"],
            "relation_type": "SUPPORTS",
            "anchor_ids": method["provenance"],
        },
    ).json()
    assert review(client, paper, edge, "edges").status_code == 409
    missing_assessment = {
        "decision": "VERIFIED",
        "reviewer": "test",
        "reason": "Test missing assessment",
        "scope": "SCIENTIFIC_VALIDITY",
        "source_hash": paper["source_hash"],
        "expected_version": 1,
    }
    assert (
        client.post(f"/api/edges/{edge['id']}/verification", json=missing_assessment).status_code
        == 422
    )


def test_verified_path_requires_current_scientific_node_and_edge_reviews(
    client: TestClient, synthetic_pdf: bytes
):
    paper, method, result = entities(client, synthetic_pdf)
    edge = client.post(
        f"/api/papers/{paper['id']}/edges",
        json={
            "source_node_id": method["id"],
            "target_node_id": result["id"],
            "relation_type": "SUPPORTS",
            "anchor_ids": method["provenance"],
        },
    ).json()
    assert review(client, paper, edge, "edges", scientific=True).status_code == 200
    endpoint = f"/api/nodes/{method['id']}/paths?target={result['id']}&verified_only=true"
    assert not client.get(endpoint).json()["found"]
    assert review(client, paper, method, scientific=True).status_code == 200
    assert review(client, paper, result, scientific=True).status_code == 200
    assert client.get(f"/api/nodes/{result['id']}").json()["review_current"] is True
    assert client.get(endpoint).json()["found"]
    with client.app.state.database.session() as session:
        audit = session.scalar(
            select(VerificationRow).where(VerificationRow.object_id == edge["id"])
        )
        audit.evidence_fingerprint = "0" * 64
    assert not client.get(endpoint).json()["found"]
    report = client.get(f"/api/papers/{paper['id']}/integrity").json()
    assert not report["structurally_valid"]
    assert any(
        i["code"] == "CONFLICTING_VERIFICATION" and i["object_id"] == edge["id"]
        for i in report["issues"]
    )


def test_disputed_prerequisite_cannot_be_reactivated_into_cycle(
    client: TestClient, synthetic_pdf: bytes
):
    paper, method, result = entities(client, synthetic_pdf)
    draft = {
        "source_node_id": method["id"],
        "target_node_id": result["id"],
        "relation_type": "PREREQUISITE_OF",
        "anchor_ids": method["provenance"],
    }
    edge = client.post(f"/api/papers/{paper['id']}/edges", json=draft).json()
    disputed = client.post(
        f"/api/edges/{edge['id']}/verification",
        json={
            "decision": "DISPUTED",
            "reviewer": "test",
            "reason": "Test dispute breaks the candidate dependency",
            "source_hash": paper["source_hash"],
            "expected_version": 1,
        },
    ).json()
    assert (
        client.post(
            f"/api/papers/{paper['id']}/edges",
            json={**draft, "source_node_id": result["id"], "target_node_id": method["id"]},
        ).status_code
        == 201
    )
    assert review(client, paper, disputed, "edges", scientific=True).status_code == 409


def test_text_block_cannot_be_promoted_to_visual_figure_evidence(client: TestClient):
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 100), "Figure 1: A controlled parser fixture.")
        paper = upload_and_process(client, bytes(doc.tobytes()))["paper"]
    figure = next(
        n
        for n in client.get(f"/api/papers/{paper['id']}/graph").json()["nodes"]
        if n["type"] == "FIGURE"
    )
    with client.app.state.database.session() as session:
        session.get(FigureRow, figure["id"]).visual_anchor_id = figure["provenance"][0]
    assert client.get(f"/api/nodes/{figure['id']}/evidence").status_code == 409


@pytest.mark.parametrize("corruption", ["range", "geometry"])
def test_corrupt_anchor_fails_every_source_navigation_surface(
    client: TestClient, synthetic_pdf: bytes, corruption: str
):
    paper, method, _ = entities(client, synthetic_pdf)
    anchor_id = method["provenance"][0]
    with client.app.state.database.session() as session:
        anchor = session.get(AnchorRow, anchor_id)
        if corruption == "range":
            anchor.end_char += 100
        else:
            anchor.bbox = [-100, 0, 100, 10]
            session.get(SpanRow, anchor.span_id).bbox = anchor.bbox
    for url in [
        f"/api/anchors/{anchor_id}",
        f"/api/anchors/{anchor_id}/nodes",
        f"/api/nodes/{method['id']}/evidence",
        f"/api/papers/{paper['id']}/document",
        f"/api/papers/{paper['id']}/search?q=measuring",
    ]:
        assert client.get(url).status_code == 409, url
    assert any(
        i["code"] == "INVALID_ANCHOR"
        for i in client.get(f"/api/papers/{paper['id']}/integrity").json()["issues"]
    )


def test_integrity_detects_missing_subtype_duplicate_orphan_and_conflicting_audit(
    client: TestClient, synthetic_pdf: bytes
):
    paper, method, result = entities(client, synthetic_pdf)
    with client.app.state.database.session() as session:
        session.delete(session.get(ClaimRow, result["id"]))
        source = session.get(NodeRow, method["id"])
        session.add(
            NodeRow(
                paper_id=paper["id"],
                type=source.type,
                layer=source.layer,
                label=source.label,
                text=source.text,
                epistemic_status=source.epistemic_status,
                confidence=0.5,
                verification_status="CANDIDATE",
                uncertainty_reason="Duplicate test",
                provenance=source.provenance,
                created_by="test-only",
            )
        )
        session.add(
            VerificationRow(
                paper_id=paper["id"],
                object_id="missing",
                object_kind="node",
                reviewer="test",
                decision="VERIFIED",
                reason="Invalid test reference",
                source_hash=paper["source_hash"],
                object_version=1,
            )
        )
    response = client.get(f"/api/papers/{paper['id']}/integrity").json()
    assert not response["structurally_valid"]
    assert {i["code"] for i in response["issues"]} >= {
        "INVALID_NODE",
        "DUPLICATE_CANDIDATE",
        "ORPHAN_NODE",
        "INVALID_REVIEW_REFERENCE",
    }
    assert client.get(f"/api/nodes/{result['id']}/evidence").status_code == 409


def test_equation_derivation_and_figure_interpretation_channels_are_not_author_text(
    client: TestClient,
):
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "x = y + 2 (1)")
        page.insert_text((72, 180), "Figure 1: A controlled evidence fixture.")
        paper = upload_and_process(client, bytes(doc.tobytes()))["paper"]
    nodes = client.get(f"/api/papers/{paper['id']}/graph").json()["nodes"]
    equation, figure = (
        next(n for n in nodes if n["type"] == kind) for kind in ("EQUATION", "FIGURE")
    )
    with client.app.state.database.session() as session:
        row = session.get(EquationRow, equation["id"])
        row.mathematical_meaning = {
            "text": "A test reconstruction, not the author's derivation.",
            "epistemic_status": "AI_DERIVATION",
            "anchor_ids": equation["provenance"],
        }
    meaning = client.get(f"/api/nodes/{equation['id']}/evidence").json()["scientific_object"][
        "mathematical_meaning"
    ]
    assert meaning["epistemic_status"] == "AI_DERIVATION"
    with client.app.state.database.session() as session:
        session.get(FigureRow, figure["id"]).surrounding_text = [meaning]
    assert client.get(f"/api/nodes/{figure['id']}/evidence").status_code == 409


def test_second_real_paper_uses_same_pipeline(client: TestClient):
    path = Path(__file__).resolve().parents[2] / "evals/private/gw150914.pdf"
    if not path.exists():
        pytest.skip("Download the public gravitational-wave fixture first")
    import json

    manifest = json.loads((path.parents[1] / "gw150914.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]
    paper = upload_and_process(client, path.read_bytes())["paper"]
    document = client.get(f"/api/papers/{paper['id']}/document").json()
    assert len(document["pages"]) == manifest["page_count"]
    for gold in manifest["gold"]:
        text = "\n".join(s["text"] for s in document["pages"][gold["page_number"] - 1]["spans"])
        assert gold["text"] in text
    graph = client.get(f"/api/papers/{paper['id']}/graph?limit=500").json()
    figures = [n for n in graph["nodes"] if n["type"] == "FIGURE"]
    assert figures and all(n["verification_status"] == "CANDIDATE" for n in figures)
    assert all(e["relation_type"] == "CONTAINS" for e in graph["edges"])
    for node in figures:
        response = client.get(f"/api/nodes/{node['id']}/evidence").json()
        assert response["scientific_object"]["caption_explicit"] == node["text"]
        assert node["text"] in response["evidence"][0]["anchor"]["text"]
    assert client.get(f"/api/papers/{paper['id']}/integrity").json()["structurally_valid"]
