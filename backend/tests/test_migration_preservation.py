from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, Table, select

from papergraph.database import Database
from papergraph.integrity import report
from papergraph.models import ClaimRow, NodeRow
from papergraph.repository import node_contract

from .test_scientific_foundation import entities, review


def test_additive_migration_preserves_old_graph_source_and_review(
    client: TestClient, synthetic_pdf: bytes, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paper, method, result = entities(client, synthetic_pdf)
    assert review(client, paper, method).status_code == 200
    # Reconstruct an actual v1 schema with v1 rows, then upgrade without resets.
    url = f"sqlite:///{tmp_path / 'v1.db'}"
    monkeypatch.setenv("PAPERGRAPH_DATABASE_URL", url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    command.upgrade(cfg, "10f9a4e1b6e1")
    old = Database(url)
    snapshots = {}
    names = [
        "papers",
        "paper_pages",
        "source_spans",
        "source_anchors",
        "knowledge_nodes",
        "knowledge_edges",
        "evidence",
        "jobs",
        "verification_records",
    ]
    with client.app.state.database.engine.connect() as source, old.engine.begin() as target:
        for name in names:
            source_table = Table(name, MetaData(), autoload_with=source)
            target_table = Table(name, MetaData(), autoload_with=target)
            rows = [
                {column.name: row[column.name] for column in target_table.columns}
                for row in source.execute(select(source_table)).mappings()
            ]
            snapshots[name] = rows
            if rows:
                target.execute(target_table.insert(), rows)
    command.upgrade(cfg, "head")
    with old.engine.connect() as connection:
        for name in names:
            table = Table(name, MetaData(), autoload_with=connection)
            rows = {r["id"]: r for r in connection.execute(select(table)).mappings()}
            for before in snapshots[name]:
                assert all(rows[before["id"]][field] == value for field, value in before.items())
    with old.session() as session:
        assert session.get(ClaimRow, result["id"]).support_strength == "NOT_ASSESSED"
        preserved = session.get(NodeRow, method["id"])
        assert preserved.verification_status == "VERIFIED" and preserved.verification_scope is None
        assert node_contract(session, preserved).review_current is False
        findings = report(session, paper["id"])
        assert any(i.code == "CONFLICTING_VERIFICATION" for i in findings.issues)
    old.engine.dispose()
