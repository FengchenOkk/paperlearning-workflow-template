import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import select

from papergraph.extraction import document_candidates, extract
from papergraph.models import SpanRow
from papergraph.notation import notation_text
from papergraph.parser import MuPDFParser, ParsedBlock, ParsedPage
from papergraph.schemas import SourceNotation
from tests.test_journey import upload_and_process


def test_overbar_and_scripts_are_observed_without_changing_source(client: TestClient):
    with pymupdf.open() as doc:
        p = doc.new_page()
        prefix = "We show that a sample with orientation (02"
        p.insert_text((72, 130), prefix + "35) is stable.", fontsize=11)
        x = 72 + pymupdf.get_text_length(prefix, fontsize=11)
        width = pymupdf.get_text_length("3", fontsize=11)
        p.draw_rect(pymupdf.Rect(x + 1, 121, x + width - 1, 121.4), color=None, fill=(0, 0, 0))
        p.insert_text((72, 200), "We show that Q", fontsize=11)
        x = 72 + pymupdf.get_text_length("We show that Q", fontsize=11)
        p.insert_text((x, 202.2), "out", fontsize=6.6)
        p.insert_text(
            (x + pymupdf.get_text_length("out", fontsize=6.6), 200),
            " remains stable at 42 V.",
            fontsize=11,
        )
        content = bytes(doc.tobytes())
    paper = upload_and_process(client, content)["paper"]
    graph = client.get(f"/api/papers/{paper['id']}/graph").json()
    results = [n for n in graph["nodes"] if n["type"] == "RESULT"]
    assert len(results) == 2
    for node in results:
        bundle = client.get(f"/api/nodes/{node['id']}/evidence").json()
        anchor = bundle["evidence"][0]["anchor"]
        notes = [SourceNotation.model_validate(n) for n in anchor["notation"]]
        display = notation_text(anchor["text"], notes)
        assert node["text"] in anchor["text"]
        assert node["verification_status"] == "CANDIDATE"
        if "orientation" in node["text"]:
            assert "(0235)" in node["text"] and "(023\u03055)" in display
            assert "5\u0305" not in display
        else:
            assert "Qout" in node["text"] and "Q_out" in display
            assert "42 V" in display
    assert client.get(f"/api/papers/{paper['id']}/integrity").json()["structurally_valid"]


def test_ambiguous_rule_is_not_invented_as_an_overbar():
    with pymupdf.open() as doc:
        p = doc.new_page()
        p.insert_text(
            (72, 130), "Measured orientation (235) and baseline are preserved.", fontsize=11
        )
        x = 72 + pymupdf.get_text_length("Measured orientation (", fontsize=11)
        p.draw_rect(pymupdf.Rect(x, 121, x + 12, 121.4), color=None, fill=(0, 0, 0))
        parsed = next(MuPDFParser().pages(bytes(doc.tobytes()), 10))
    block = next(b for b in parsed.blocks if "orientation" in b.text)
    assert not [n for n in block.notation if n.kind == "OVERBAR"]
    assert block.notation_issues


def test_headers_and_panel_labels_remain_source_without_section_nodes(client: TestClient):
    with pymupdf.open() as doc:
        for i in range(2):
            p = doc.new_page()
            p.insert_text((72, 35), "Article", fontsize=18)
            p.insert_text((72, 65), "Journal running header", fontsize=11)
            p.insert_text(
                (72, 160), "Methods" if i == 0 else "Results", fontname="hebo", fontsize=14
            )
            p.insert_text(
                (72, 220),
                "This body paragraph establishes the ordinary source font size.",
                fontsize=11,
            )
            p.insert_text((72, 340), "c d e", fontname="hebo", fontsize=18)
            p.insert_text((72, 830), "Journal issue footer", fontname="hebo", fontsize=11)
        content = bytes(doc.tobytes())
    paper_id = upload_and_process(client, content)["paper"]["id"]
    document = client.get(f"/api/papers/{paper_id}/document").json()
    spans = [s for p in document["pages"] for s in p["spans"]]
    assert len([s for s in spans if s["kind"] == "header"]) == 6
    assert all(s["section_titles"] == [] for s in spans if s["kind"] == "header")
    assert len([s for s in spans if s["kind"] == "panel_label"]) == 2
    sections = [
        n["text"]
        for n in client.get(f"/api/papers/{paper_id}/graph").json()["nodes"]
        if n["type"] == "SECTION"
    ]
    assert sections == ["Methods", "Results"]


def test_background_and_relationship_classification_is_domain_neutral():
    background = "Although legacy optical gating is capable of changing the signal, it suffers from stability issues."
    assert extract(background, False) == []
    own = "Our method suffers from a major limitation under long observation periods."
    assert extract(own, False)[0].type == "LIMITATION"
    relation = "We further extracted the thermal response as a function of sample pressure."
    candidate = extract(relation, False)[0]
    assert candidate.type == "RELATIONSHIP_ANALYSIS"
    assert candidate.text == relation
    assert candidate.epistemic_status == "AUTHOR_CLAIM"
    assert (
        extract("We employed a calibrated instrument to measure the thermal response.", False)[
            0
        ].type
        == "METHOD"
    )


def test_passive_methods_and_multi_anchor_compilation(client: TestClient):
    with pymupdf.open() as doc:
        p = doc.new_page()
        p.insert_text((72, 50), "A generic process study", fontsize=18)
        p.insert_text((72, 100), "Methods", fontname="hebo", fontsize=14)
        p.insert_text(
            (72, 150), "The layer was deposited on a clean substrate at 80 C.", fontsize=11
        )
        p.insert_text((72, 200), "The samples were transferred using a polymer stamp.", fontsize=11)
        p.insert_text((72, 300), "References", fontname="hebo", fontsize=14)
        p.insert_text((72, 350), "The film was deposited in another published study.", fontsize=11)
        content = bytes(doc.tobytes())
    paper_id = upload_and_process(client, content)["paper"]["id"]
    graph = client.get(f"/api/papers/{paper_id}/graph").json()
    methods = [n for n in graph["nodes"] if n["type"] == "METHOD"]
    assert len(methods) == 2
    process = next(n for n in graph["nodes"] if n["type"] == "PROCESS")
    assert process["epistemic_status"] == "AI_INTERPRETATION" and len(process["provenance"]) == 2
    bundle = client.get(f"/api/nodes/{process['id']}/evidence").json()
    assert len(bundle["evidence"]) == 2
    assert all(e["anchor"]["text"] in process["text"] for e in bundle["evidence"])
    assert client.get(f"/api/papers/{paper_id}/integrity").json()["structurally_valid"]


def test_notation_review_fingerprint(client: TestClient, synthetic_pdf: bytes):
    from tests.test_scientific_foundation import entities, review

    paper, method, _ = entities(client, synthetic_pdf)
    assert review(client, paper, method).status_code == 200
    assert client.get(f"/api/nodes/{method['id']}").json()["review_current"] is True
    with client.app.state.database.session() as session:
        span = session.scalar(select(SpanRow).where(SpanRow.text.contains(method["text"])))
        assert span is not None
        span.notation_issues = ["Unresolved typography; original page review required."]
    assert client.get(f"/api/nodes/{method['id']}").json()["review_current"] is False
    with client.app.state.database.session() as session:
        span = session.scalar(select(SpanRow).where(SpanRow.text.contains(method["text"])))
        assert span is not None
        span.notation = [
            {
                "start_char": 0,
                "end_char": 1,
                "raw": "?",
                "display": "?\u0305",
                "kind": "OVERBAR",
                "bbox": span.bbox,
                "basis": "PDF_DRAWING_AND_GLYPH",
            }
        ]
    assert client.get(f"/api/nodes/{method['id']}/evidence").status_code == 409


def test_process_excerpts_exclude_characterization_and_respect_possible_subsections():
    paragraphs = [
        "Methods",
        "The layer was deposited on a substrate at 80 C. The film was cleaned with a solvent bath at room temperature.",
        "Optical characterization",
        "The contacts were fabricated by deposition. Spectra were acquired at room temperature.",
        "The samples were transferred using a polymer stamp. The laser power was controlled to avoid damage.",
    ]
    page = ParsedPage(
        1,
        600,
        800,
        0,
        [
            ParsedBlock(
                t, (72, 50 + i * 70, 520, 100 + i * 70), "heading" if i == 0 else "paragraph", i
            )
            for i, t in enumerate(paragraphs)
        ],
    )
    result = document_candidates([page])
    processes = [c for candidates in result.values() for c in candidates if c.type == "PROCESS"]
    assert len(processes) == 2
    assert processes[0].source_blocks == ((1, 1),)
    assert processes[1].source_blocks == ((1, 3), (1, 4))
    assert "Spectra" not in processes[0].text and "laser" not in processes[0].text
    assert "Spectra" in processes[1].text and "laser" in processes[1].text
    assert "characterization and measurement-sample preparation" in processes[1].reason
    assert all(c.epistemic_status == "AI_INTERPRETATION" for c in processes)
    assert any("contacts" in c.text for c in result[(1, 3)] if c.type == "METHOD")
    continued = ParsedPage(
        1,
        600,
        800,
        0,
        [
            ParsedBlock("Methods", (72, 50, 520, 90), "heading", 0),
            ParsedBlock(
                "The specimens were fabricated using a pressure-controlled",
                (72, 120, 520, 170),
                "paragraph",
                1,
            ),
            ParsedBlock(
                "stamp at 90 C. Optical spectra were acquired separately.",
                (72, 200, 520, 260),
                "paragraph",
                2,
            ),
        ],
    )
    compilation = next(
        c
        for candidates in document_candidates([continued]).values()
        for c in candidates
        if c.type == "PROCESS"
    )
    assert compilation.text.endswith("pressure-controlled\nstamp at 90 C.")
    assert compilation.source_blocks == ((1, 1), (1, 2))
    assert "spectra" not in compilation.text


def test_measurement_sample_preparation_is_separate_from_device_fabrication(client: TestClient):
    fabrication = (
        "The film was deposited on a substrate at 85 C. "
        "The device was assembled with a polymer stamp at 160 C."
    )
    characterization = (
        "The resistance of reference specimens was characterized using a calibrated meter. "
        "Electrical contacts were fabricated on those specimens by metal deposition. "
        "The response was determined by sweeping the applied voltage."
    )
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 50), "Separate preparation and measurement", fontsize=18)
        page.insert_text((72, 100), "Methods", fontname="hebo", fontsize=14)
        page.insert_textbox(pymupdf.Rect(72, 150, 520, 250), fabrication, fontsize=11)
        page.insert_textbox(pymupdf.Rect(72, 300, 520, 440), characterization, fontsize=11)
        content = bytes(doc.tobytes())
    paper_id = upload_and_process(client, content)["paper"]["id"]
    graph = client.get(f"/api/papers/{paper_id}/graph").json()
    processes = [node for node in graph["nodes"] if node["type"] == "PROCESS"]
    assert len(processes) == 2
    preparation = next(
        node for node in processes if "polymer stamp" in " ".join(node["text"].split())
    )
    measurement = next(
        node for node in processes if "calibrated meter" in " ".join(node["text"].split())
    )
    assert "contacts" not in preparation["text"] and "reference specimens" not in " ".join(
        preparation["text"].split()
    )
    assert "contacts" in measurement["text"] and "sweeping" in measurement["text"]
    assert "85 C" in preparation["text"] and "160 C" in preparation["text"]
    for node in processes:
        assert node["epistemic_status"] == "AI_INTERPRETATION"
        assert node["verification_status"] == "CANDIDATE"
        bundle = client.get(f"/api/nodes/{node['id']}/evidence").json()
        assert len(bundle["evidence"]) == 1
        assert " ".join(node["text"].split()) == " ".join(
            bundle["evidence"][0]["anchor"]["text"].split()
        )
    assert client.get(f"/api/papers/{paper_id}/integrity").json()["structurally_valid"]
