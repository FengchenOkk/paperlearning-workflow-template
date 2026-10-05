"""Browser journeys for explicit local PDF paths; gold is used only for assertions."""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from scripts.evaluate_source_gate import compact

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RESULTS = ROOT / "test-results" / "dual-paper"


def run(pdfs: list[Path], golds: list[Path]) -> None:
    for pdf, gold in zip(pdfs, golds, strict=True):
        assert (
            hashlib.sha256(pdf.read_bytes()).hexdigest()
            == json.loads(gold.read_bytes())["source_hash"]
        )
    RESULTS.mkdir(parents=True, exist_ok=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="journey-", dir=RESULTS) as temporary:
        env = dict(os.environ)
        env["PAPERGRAPH_DATABASE_URL"] = f"sqlite:///{Path(temporary) / 'graph.db'}"
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
                    raise RuntimeError("Local API did not start")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    page = browser.new_page(viewport={"width": 1536, "height": 1100})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base)
                    for index, (pdf, gold_path) in enumerate(zip(pdfs, golds, strict=True)):
                        gold = json.loads(gold_path.read_bytes())
                        page.get_by_label("Upload PDF").set_input_files(str(pdf))
                        expect(page.get_by_test_id("graph-canvas")).to_be_visible(timeout=60000)
                        paper = next(
                            p
                            for p in httpx.get(f"{base}/api/papers").json()
                            if p["source_hash"] == gold["source_hash"]
                        )
                        graph = httpx.get(f"{base}/api/papers/{paper['id']}/graph?limit=500").json()
                        # Wait for the new paper's worker, not the previous paper's canvas.
                        for _ in range(150):
                            if graph["total_nodes"]:
                                break
                            time.sleep(0.2)
                            graph = httpx.get(
                                f"{base}/api/papers/{paper['id']}/graph?limit=500"
                            ).json()
                        assert paper["source_hash"] == gold["source_hash"]
                        expect(page.get_by_test_id("graph-canvas")).to_be_visible(timeout=60000)
                        checked = []
                        targets = [x for x in gold["items"] if x["type"] in {"FIGURE", "EQUATION"}]
                        targets.insert(0, next(x for x in gold["items"] if x["type"] == "RESULT"))
                        inspector = page.get_by_role("complementary", name="Scientific inspector")
                        for item in targets:
                            node = next(
                                n
                                for n in graph["nodes"]
                                if n["type"] == item["type"]
                                and all(
                                    compact(c["text"]) in compact(n["text"])
                                    for c in item["components"]
                                )
                            )
                            details = page.locator(".graph-node-list")
                            if not details.get_attribute("open"):
                                details.locator("summary").click()
                            page.locator(f'[data-node-id="{node["id"]}"]').click()
                            expect(inspector.get_by_text("CANDIDATE", exact=True)).to_be_visible()
                            expect(inspector.locator(".eyebrow")).to_contain_text(item["type"])
                            expect(
                                inspector.get_by_text(
                                    node["epistemic_status"].replace("_", " "), exact=True
                                )
                            ).to_be_visible()
                            expect(inspector.locator(".node-text")).to_have_text(node["text"])
                            evidence = inspector.locator("button.evidence").first
                            evidence.click()
                            expect(page.get_by_label("PDF page")).to_have_value(str(item["page"]))
                            highlight = page.get_by_test_id("source-highlight")
                            expect(highlight).to_be_visible()
                            page.wait_for_function("""() => {
                                const h=document.querySelector('.source-highlight')?.getBoundingClientRect();
                                const p=document.querySelector('.pdf-scroll')?.getBoundingClientRect();
                                return h && p && h.top<p.bottom && h.bottom>p.top;
                            }""")
                            image = page.get_by_alt_text(f"Original PDF page {item['page']}")
                            expect(image).to_be_visible()
                            page.wait_for_function(
                                '(number) => {const image=document.querySelector(`img[alt="Original PDF page ${number}"]`); return image?.complete && image.naturalWidth>0;}',
                                arg=item["page"],
                            )
                            bundle = httpx.get(f"{base}/api/nodes/{node['id']}/evidence").json()
                            anchor = bundle["evidence"][0]["anchor"]
                            assert (
                                anchor["source_hash"] == gold["source_hash"]
                                and anchor["page_number"] == item["page"]
                            )
                            if item["type"] == "FIGURE":
                                assert (
                                    bundle["scientific_object"]["figure_number"] == item["number"]
                                )
                            elif item["type"] == "EQUATION":
                                assert (
                                    bundle["scientific_object"]["equation_number"] == item["number"]
                                )
                                assert bundle["scientific_object"]["latex"] is None
                            page.locator(".source-span.active").click()
                            expect(inspector.locator(".node-text")).to_have_text(node["text"])
                            page.reload()
                            expect(page.get_by_test_id("graph-canvas")).to_be_visible()
                            expect(inspector.locator(".node-text")).to_have_text(node["text"])
                            expect(page.get_by_label("PDF page")).to_have_value(str(item["page"]))
                            expect(highlight).to_be_visible()
                            checked.append(
                                {
                                    "gold_id": item["id"],
                                    "page": item["page"],
                                    "type": item["type"],
                                    "source_hash": anchor["source_hash"],
                                    "result": "PASS",
                                }
                            )
                        # Multiple terms in different positions; actual source fallback is acceptable.
                        query = " ".join(
                            compact(targets[0]["components"][0]["text"]).split()[0:3][::-1]
                        )
                        page.get_by_label("Search paper and graph").fill(query)
                        expected_hit = httpx.get(
                            f"{base}/api/papers/{paper['id']}/search", params={"q": query}
                        ).json()[0]
                        assert expected_hit["node_id"] is not None
                        expected_node = next(
                            n for n in graph["nodes"] if n["id"] == expected_hit["node_id"]
                        )
                        page.get_by_role("button", name="Search", exact=True).click()
                        expect(page.locator(".search-results")).to_be_visible()
                        page.locator(".search-results > button").first.click()
                        expect(inspector.locator(".node-text")).to_have_text(expected_node["text"])
                        expect(page.get_by_label("PDF page")).to_have_value(
                            str(expected_hit["page_number"])
                        )
                        selected_image = page.get_by_alt_text(
                            f"Original PDF page {expected_hit['page_number']}"
                        )
                        expect(selected_image).to_be_visible()
                        page.wait_for_function(
                            '(number) => {const image=document.querySelector(`img[alt="Original PDF page ${number}"]`); return image?.complete && image.naturalWidth>0;}',
                            arg=expected_hit["page_number"],
                        )
                        expect(highlight).to_be_visible()
                        page.screenshot(path=str(RESULTS / f"paper-{index + 1}.png"))
                        integrity = httpx.get(f"{base}/api/papers/{paper['id']}/integrity").json()
                        assert (
                            integrity["structurally_valid"]
                            and integrity["scientific_validity"] == "NOT_ASSESSED"
                        )
                        outcomes.append(
                            {
                                "source_hash": gold["source_hash"],
                                "journeys": checked,
                                "search": "PASS",
                                "integrity": "PASS",
                                "status": "PASS",
                            }
                        )
                    assert not errors, errors
                    browser.close()
            finally:
                for process in [worker, server]:
                    process.terminate()
                    process.wait(timeout=15)
                if os.name == "nt":
                    time.sleep(0.3)
    (RESULTS / "results.json").write_text(json.dumps(outcomes, indent=2) + "\n", encoding="utf-8")
    print(
        "Both real-paper browser journeys passed: graph, type/status, evidence, correct page/block, reverse, refresh and multi-term search."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-a", type=Path, required=True)
    parser.add_argument("--pdf-b", type=Path, required=True)
    args = parser.parse_args()
    run(
        [args.pdf_a, args.pdf_b],
        [ROOT / "evals/gold/paper-a/gold.json", ROOT / "evals/gold/paper-b/gold.json"],
    )
