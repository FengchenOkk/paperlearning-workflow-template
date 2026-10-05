from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import select

from papergraph.models import AnchorRow, JobRow, NodeRow, VerificationRow
from papergraph.worker import run_once


def upload_and_process(client: TestClient, content: bytes) -> dict:
    result = client.post(
        "/api/papers", files={"file": ("../../paper.pdf", content, "application/pdf")}
    )
    assert result.status_code == 202
    payload = result.json()
    app = client.app
    assert run_once(app.state.database, app.state.storage, app.state.settings)
    return payload


def test_upload_graph_evidence_restart_and_dedup(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    paper_id = payload["paper"]["id"]
    assert client.get(f"/api/jobs/{payload['job']['id']}").json()["status"] == "READY"
    document = client.get(f"/api/papers/{paper_id}/document").json()
    assert len(document["pages"]) == 2
    graph = client.get(f"/api/papers/{paper_id}/graph").json()
    methods = [n for n in graph["nodes"] if n["type"] == "METHOD"]
    assert len(methods) == 1 and methods[0]["verification_status"] == "CANDIDATE"
    bundle = client.get(f"/api/nodes/{methods[0]['id']}/evidence").json()
    anchor = bundle["evidence"][0]["anchor"]
    assert anchor["page_number"] == 1
    assert methods[0]["text"] in anchor["text"]
    image = client.get(f"/api/papers/{paper_id}/pages/1/image")
    assert image.headers["content-type"] == "image/png" and image.content.startswith(b"\x89PNG")
    source_nodes = client.get(f"/api/anchors/{anchor['id']}/nodes").json()
    assert any(n["id"] == methods[0]["id"] for n in source_nodes)
    duplicate = client.post("/api/papers", files={"file": ("renamed.pdf", synthetic_pdf)}).json()
    assert duplicate["deduplicated"] and duplicate["paper"]["id"] == paper_id
    assert not run_once(
        client.app.state.database, client.app.state.storage, client.app.state.settings
    )
    # A new API process/session reads the same durable database.
    from papergraph.api import create_app

    with TestClient(create_app(client.app.state.settings)) as restarted:
        assert restarted.get(f"/api/papers/{paper_id}/graph").json() == graph


def test_no_fake_learning_paths_and_limits(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    paper_id = payload["paper"]["id"]
    assert client.get(f"/api/papers/{paper_id}/graph?view=learning").json()["nodes"] == []
    limited = client.get(f"/api/papers/{paper_id}/graph?limit=1").json()
    assert len(limited["nodes"]) == 1 and limited["truncated"]
    nodes = client.get(f"/api/papers/{paper_id}/graph").json()["nodes"]
    candidate = next(n for n in nodes if n["type"] == "METHOD")
    path = client.get(
        f"/api/nodes/{candidate['id']}/paths",
        params={"target": paper_id, "relation": "PREREQUISITE_OF"},
    ).json()
    assert not path["found"]
    search = client.get(f"/api/papers/{paper_id}/search?q=measuring").json()
    assert search and search[0]["node_id"] == candidate["id"]
    assert client.get(f"/api/papers/{paper_id}/search?q=%25_").json() == []


def test_verification_audit_stale_and_no_overwrite(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    paper = payload["paper"]
    graph = client.get(f"/api/papers/{paper['id']}/graph").json()
    node = next(n for n in graph["nodes"] if n["type"] == "METHOD")
    review = {
        "decision": "VERIFIED",
        "reviewer": "test-reviewer",
        "reason": "Test audit action only, not a real scientific acceptance.",
        "source_hash": paper["source_hash"],
        "expected_version": 1,
    }
    updated = client.post(f"/api/nodes/{node['id']}/verification", json=review)
    assert updated.status_code == 200 and updated.json()["version"] == 2
    assert client.post(f"/api/nodes/{node['id']}/verification", json=review).status_code == 409
    with client.app.state.database.session() as session:
        audit = session.scalar(select(VerificationRow))
        assert audit and audit.reviewer == "test-reviewer"
    client.post("/api/papers", files={"file": ("same.pdf", synthetic_pdf)})
    assert client.get(f"/api/nodes/{node['id']}").json()["verification_status"] == "VERIFIED"


def test_source_and_evidence_integrity(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    paper_id = payload["paper"]["id"]
    with client.app.state.database.session() as session:
        for anchor in session.scalars(select(AnchorRow)):
            assert anchor.text and anchor.end_char == len(anchor.text)
            assert anchor.source_hash == payload["paper"]["source_hash"]
        for node in session.scalars(
            select(NodeRow).where(NodeRow.paper_id == paper_id, NodeRow.type != "PAPER")
        ):
            assert node.provenance and node.verification_status == "CANDIDATE"
    document = client.get(f"/api/papers/{paper_id}/document").json()
    anchor = document["pages"][0]["spans"][0]["anchor_id"]
    invalid = {
        "type": "METHOD",
        "layer": "SEMANTIC",
        "label": "Fabricated method",
        "text": "This text does not exist in the source.",
        "anchor_ids": [anchor],
        "epistemic_status": "PAPER_EXPLICIT",
        "uncertainty_reason": "Test invalid attribution",
    }
    assert client.post(f"/api/papers/{paper_id}/nodes", json=invalid).status_code == 409
    invalid["confidence"] = 2
    assert client.post(f"/api/papers/{paper_id}/nodes", json=invalid).status_code == 422


def test_invalid_empty_scanned_and_recovery(client: TestClient, synthetic_pdf: bytes):
    assert client.post("/api/papers", files={"file": ("x.pdf", b"not pdf")}).status_code == 422
    bad = client.post("/api/papers", files={"file": ("x.pdf", b"%PDF-not-a-document")}).json()
    run_once(client.app.state.database, client.app.state.storage, client.app.state.settings)
    assert client.get(f"/api/jobs/{bad['job']['id']}").json()["status"] == "FAILED"
    assert client.post(f"/api/jobs/{bad['job']['id']}/retry").status_code == 200
    run_once(client.app.state.database, client.app.state.storage, client.app.state.settings)
    with pymupdf.open() as doc:
        doc.new_page()
        empty = upload_and_process(client, bytes(doc.tobytes()))
    assert client.get(f"/api/jobs/{empty['job']['id']}").json()["status"] == "PARTIAL"
    queued = client.post("/api/papers", files={"file": ("recover.pdf", synthetic_pdf)}).json()
    with client.app.state.database.session() as session:
        row = session.get(JobRow, queued["job"]["id"])
        row.status, row.lease_until, row.lease_token = "PARSING", 0, "expired-worker"
    assert run_once(client.app.state.database, client.app.state.storage, client.app.state.settings)
    assert client.get(f"/api/jobs/{queued['job']['id']}").json()["status"] == "READY"


def test_real_public_paper_gold(client: TestClient):
    path = Path(__file__).resolve().parents[2] / "evals" / "private" / "dropout.pdf"
    if not path.exists():
        import pytest

        pytest.skip("Run evals/download_fixture.py to enable the public-paper golden test")
    payload = upload_and_process(client, path.read_bytes())
    paper_id = payload["paper"]["id"]
    document = client.get(f"/api/papers/{paper_id}/document").json()
    assert len(document["pages"]) == 30
    assert (
        client.get(f"/api/papers/{paper_id}").json()["title"]
        == "Dropout: A Simple Way to Prevent Neural Networks from Overfitting"
    )
    first = "\n".join(s["text"] for s in document["pages"][0]["spans"])
    assert "Dropout is a technique for addressing this problem." in first
    graph = client.get(f"/api/papers/{paper_id}/graph?limit=500").json()
    method = next(
        n for n in graph["nodes"] if n["type"] == "METHOD" and "Dropout is a technique" in n["text"]
    )
    evidence = client.get(f"/api/nodes/{method['id']}/evidence").json()["evidence"][0]["anchor"]
    assert evidence["page_number"] == 1 and method["text"] in evidence["text"]
    x0, y0, x1, y1 = evidence["bbox"]
    assert 0 <= x0 < x1 <= document["pages"][0]["width"]
    assert 0 <= y0 < y1 <= document["pages"][0]["height"]
