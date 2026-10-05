from pathlib import Path

import pymupdf
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from papergraph.api import create_app
from papergraph.config import Settings


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("PAPERGRAPH_DATABASE_URL", url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    command.upgrade(cfg, "head")
    app = create_app(Settings(database_url=url, storage_dir=tmp_path / "documents"))
    with TestClient(app) as test_client:
        yield test_client
    app.state.database.engine.dispose()


@pytest.fixture
def synthetic_pdf() -> bytes:
    # Synthetic parser fixture; never used as a public-paper scientific demonstration.
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 60), "A controlled parser test", fontsize=18)
        page.insert_text((72, 120), "We propose a method for measuring a test signal.", fontsize=11)
        second = doc.new_page()
        second.insert_text((72, 80), "Results", fontsize=16)
        second.insert_text(
            (72, 130), "We show that the synthetic signal is measured in this fixture.", fontsize=11
        )
        return bytes(doc.tobytes())
