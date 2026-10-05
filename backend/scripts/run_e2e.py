"""Run the real public-PDF browser journey against fresh migrated storage."""

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RESULTS = ROOT / "test-results"
FIXTURE = ROOT / "evals" / "private" / "dropout.pdf"


def run() -> None:
    if not FIXTURE.exists():
        raise RuntimeError("Download the public fixture with evals/download_fixture.py first")
    RESULTS.mkdir(exist_ok=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="e2e-", dir=RESULTS) as temporary:
        env = dict(os.environ)
        env["PAPERGRAPH_DATABASE_URL"] = f"sqlite:///{Path(temporary) / 'test.db'}"
        env["PAPERGRAPH_STORAGE_DIR"] = str(Path(temporary) / "documents")
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True
        )
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        with (RESULTS / "server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "papergraph.api:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--no-access-log",
                ],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=log,
                creationflags=flags,
            )
            worker = subprocess.Popen(
                [sys.executable, "-m", "papergraph.worker"],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=log,
                creationflags=flags,
            )
            try:
                for _ in range(100):
                    try:
                        if httpx.get(f"{base}/api/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("API did not start")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    page = browser.new_page(viewport={"width": 1536, "height": 1100})
                    errors: list[str] = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base)
                    expect(page.get_by_role("heading", name="Read the structure.")).to_be_visible()
                    page.get_by_label("Upload PDF").set_input_files(str(FIXTURE))
                    expect(page.get_by_test_id("graph-canvas")).to_be_visible(timeout=60000)
                    papers = httpx.get(f"{base}/api/papers").json()
                    assert len(papers) == 1 and papers[0]["page_count"] == 30
                    paper_id = papers[0]["id"]
                    graph = httpx.get(f"{base}/api/papers/{paper_id}/graph?limit=40").json()
                    integrity = httpx.get(f"{base}/api/papers/{paper_id}/integrity").json()
                    assert (
                        integrity["structurally_valid"]
                        and integrity["scientific_validity"] == "NOT_ASSESSED"
                    )
                    method = next(
                        n
                        for n in graph["nodes"]
                        if n["type"] == "METHOD" and "Dropout is a technique" in n["text"]
                    )
                    page.locator(".graph-node-list summary").click()
                    page.locator(f'[data-node-id="{method["id"]}"]').click()
                    inspector = page.get_by_role("complementary", name="Scientific inspector")
                    expect(inspector.get_by_text("CANDIDATE", exact=True)).to_be_visible()
                    evidence = inspector.locator("button.evidence").first
                    evidence.click()
                    expect(page.get_by_label("PDF page")).to_have_value("1")
                    expect(page.get_by_test_id("source-highlight")).to_be_visible()
                    page.wait_for_function("""() => {
                      const highlight = document.querySelector('.source-highlight');
                      const pane = document.querySelector('.pdf-scroll');
                      if (!highlight || !pane) return false;
                      const a = highlight.getBoundingClientRect(), b = pane.getBoundingClientRect();
                      return a.top < b.bottom && a.bottom > b.top;
                    }""")
                    highlight_box = page.get_by_test_id("source-highlight").bounding_box()
                    pane_box = page.locator(".pdf-scroll").bounding_box()
                    assert highlight_box and pane_box
                    assert (
                        highlight_box["y"] < pane_box["y"] + pane_box["height"]
                        and highlight_box["y"] + highlight_box["height"] > pane_box["y"]
                    ), "Evidence highlight must intersect the source viewport"
                    image = page.get_by_alt_text("Original PDF page 1")
                    expect(image).to_be_visible()
                    assert image.evaluate("image => image.complete && image.naturalWidth > 0")
                    source_text = page.locator(".source-span.active")
                    expect(source_text).to_be_visible()
                    source_text.click()
                    expect(inspector.locator(".node-text")).to_contain_text("Dropout")
                    page.get_by_label("Next page").click()
                    expect(page.get_by_label("PDF page")).to_have_value("2")
                    evidence.click()
                    expect(page.get_by_label("PDF page")).to_have_value("1")
                    page.reload()
                    expect(page.get_by_test_id("graph-canvas")).to_be_visible()
                    expect(page.get_by_test_id("source-highlight")).to_be_visible()
                    page.wait_for_function("""() => {
                      const a = document.querySelector('.source-highlight')?.getBoundingClientRect();
                      const b = document.querySelector('.pdf-scroll')?.getBoundingClientRect();
                      return a && b && a.top < b.bottom && a.bottom > b.top;
                    }""")
                    expect(
                        page.get_by_role("complementary", name="Scientific inspector").locator(
                            ".node-text"
                        )
                    ).to_contain_text("Dropout")
                    page.screenshot(path=str(RESULTS / "workspace-dark.png"))
                    page.get_by_label("Toggle theme").click()
                    page.screenshot(path=str(RESULTS / "workspace-light.png"))
                    page.get_by_label("Search paper and graph").fill("Dropout is a technique")
                    page.get_by_role("button", name="Search", exact=True).click()
                    expect(page.locator(".search-results")).to_be_visible()
                    page.locator(".search-results > button").first.click()
                    expect(page.get_by_test_id("source-highlight")).to_be_visible()
                    page.get_by_role("button", name="Learning", exact=True).click()
                    expect(
                        page.get_by_role("heading", name="Prerequisites have not been analyzed")
                    ).to_be_visible()
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.get_by_role("button", name="Knowledge", exact=True).click()
                    expect(page.get_by_test_id("graph-canvas")).to_be_visible()
                    page.screenshot(path=str(RESULTS / "workspace-mobile.png"), full_page=True)
                    assert not page.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth"
                    ), "Mobile layout overflows"
                    assert not errors, errors
                    browser.close()
                    print(
                        "E2E passed: public PDF upload, candidate graph, evidence bbox, PDF page, reverse source selection, refresh, search, empty learning projection, themes and mobile."
                    )
            finally:
                for process in [worker, server]:
                    process.terminate()
                    process.wait(timeout=15)
                # Windows can briefly retain a file handle after process exit.
                if os.name == "nt":
                    time.sleep(0.3)


if __name__ == "__main__":
    run()
