from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from papergraph.models import AnchorRow, NodeRow
from papergraph.parser import MuPDFParser, display_box
from papergraph.storage import DocumentStorage
from papergraph.worker import run_once

from .test_journey import upload_and_process


def test_candidate_edges_provenance_and_cycle(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    paper_id = payload["paper"]["id"]
    graph = client.get(f"/api/papers/{paper_id}/graph").json()
    source = next(n for n in graph["nodes"] if n["type"] == "METHOD")
    target = next(n for n in graph["nodes"] if n["type"] == "RESULT")
    draft = {
        "source_node_id": source["id"],
        "target_node_id": target["id"],
        "relation_type": "PREREQUISITE_OF",
        "anchor_ids": source["provenance"],
    }
    created = client.post(f"/api/papers/{paper_id}/edges", json=draft)
    assert created.status_code == 201 and created.json()["verification_status"] == "CANDIDATE"
    reverse = {**draft, "source_node_id": target["id"], "target_node_id": source["id"]}
    assert client.post(f"/api/papers/{paper_id}/edges", json=reverse).status_code == 409
    unsupported = {**draft, "anchor_ids": []}
    assert client.post(f"/api/papers/{paper_id}/edges", json=unsupported).status_code == 422
    fabricated = {**draft, "anchor_ids": [str(uuid4())]}
    assert client.post(f"/api/papers/{paper_id}/edges", json=fabricated).status_code == 409
    path = client.get(
        f"/api/nodes/{source['id']}/paths",
        params={"target": target["id"], "relation": "PREREQUISITE_OF"},
    ).json()
    assert path["found"] and path["node_ids"] == [source["id"], target["id"]]
    assert not client.get(
        f"/api/nodes/{source['id']}/paths", params={"target": target["id"], "verified_only": True}
    ).json()["found"]


def test_foreign_paper_anchors_and_stale_source(client: TestClient, synthetic_pdf: bytes):
    first = upload_and_process(client, synthetic_pdf)
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 70), "We propose a different method for a second fixture.")
        other = upload_and_process(client, bytes(doc.tobytes()))
    anchor = client.get(f"/api/papers/{other['paper']['id']}/document").json()["pages"][0]["spans"][
        0
    ]["anchor_id"]
    draft = {
        "type": "THEORY",
        "layer": "SEMANTIC",
        "label": "Candidate",
        "text": "An annotation",
        "anchor_ids": [anchor],
        "uncertainty_reason": "Not scientifically verified",
    }
    assert client.post(f"/api/papers/{first['paper']['id']}/nodes", json=draft).status_code == 409
    graph = client.get(f"/api/papers/{first['paper']['id']}/graph").json()
    node = next(n for n in graph["nodes"] if n["type"] == "METHOD")
    review = {
        "decision": "VERIFIED",
        "reviewer": "test",
        "reason": "Test stale source rejection",
        "source_hash": "0" * 64,
        "expected_version": 1,
    }
    assert client.post(f"/api/nodes/{node['id']}/verification", json=review).status_code == 409


def test_corrupt_anchor_text_and_storage_rejected(client: TestClient, synthetic_pdf: bytes):
    payload = upload_and_process(client, synthetic_pdf)
    with client.app.state.database.session() as session:
        node = session.scalar(select(NodeRow).where(NodeRow.type == "METHOD"))
        node_id = node.id
        anchor = session.get(AnchorRow, node.provenance[0])
        anchor.end_char += 99
    assert client.get(f"/api/nodes/{node_id}/evidence").status_code == 409
    path = client.app.state.storage.path(payload["paper"]["source_hash"])
    path.write_bytes(b"tampered")
    assert client.get(f"/api/papers/{payload['paper']['id']}/pdf").status_code == 409


def test_rotation_coordinates_encryption_and_page_limit(synthetic_pdf: bytes):
    with pymupdf.open(stream=synthetic_pdf, filetype="pdf") as doc:
        doc[0].set_rotation(90)
        rotated = bytes(doc.tobytes())
        encrypted = bytes(
            doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
        )
    pages = list(MuPDFParser().pages(rotated, 10))
    first = pages[0]
    x0, y0, x1, y1 = first.blocks[0].bbox
    assert display_box(rotated, 1, first.blocks[0].bbox) == pytest.approx(
        (first.width - y1, x0, first.width - y0, x1)
    )
    with pytest.raises(ValueError, match="ENCRYPTED_PDF"):
        list(MuPDFParser().pages(encrypted, 10))
    with pytest.raises(ValueError, match="PAGE_LIMIT_EXCEEDED"):
        list(MuPDFParser().pages(synthetic_pdf, 1))


def test_upload_size_limit_and_worker_does_not_claim_completion(
    client: TestClient, synthetic_pdf: bytes
):
    from papergraph.api import create_app

    settings = replace(client.app.state.settings, max_upload_bytes=8)
    with TestClient(create_app(settings)) as small:
        assert (
            small.post("/api/papers", files={"file": ("large.pdf", synthetic_pdf)}).status_code
            == 413
        )
    payload = client.post("/api/papers", files={"file": ("x.pdf", synthetic_pdf)}).json()
    assert client.get(f"/api/jobs/{payload['job']['id']}").json()["status"] == "UPLOADED"
    assert client.get(f"/api/papers/{payload['paper']['id']}/graph").json()["nodes"] == []
    assert run_once(client.app.state.database, client.app.state.storage, client.app.state.settings)


def test_storage_rejects_traversal(tmp_path: Path):
    storage = DocumentStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.path("../../private.pdf")


def test_local_mutations_reject_cross_origin(client: TestClient, synthetic_pdf: bytes):
    blocked = client.post(
        "/api/papers",
        files={"file": ("x.pdf", synthetic_pdf)},
        headers={"Origin": "https://untrusted.example"},
    )
    assert blocked.status_code == 403
    assert client.get("/api/health", headers={"Host": "untrusted.example"}).status_code == 400
