import pymupdf
from fastapi.testclient import TestClient

from papergraph.extraction import extract
from papergraph.parser import MuPDFParser, ParsedBlock, join_fragments
from papergraph.text_search import relevance
from scripts.evaluate_source_gate import quantity_matches
from tests.test_journey import upload_and_process


def test_superscript_survives_source_graph_evidence(client: TestClient):
    with pymupdf.open() as doc:
        p = doc.new_page()
        p.insert_text((72, 60), "Source typography regression", fontsize=18)
        prefix = "We show that the measured ratio exceeds 10"
        p.insert_text((72, 130), prefix, fontsize=11)
        x = 72 + pymupdf.get_text_length(prefix, fontsize=11)
        p.insert_text((x, 126), "8", fontsize=7)
        p.insert_text((x + 4, 130), " under the stated conditions.", fontsize=11)
        content = bytes(doc.tobytes())
    paper_id = upload_and_process(client, content)["paper"]["id"]
    graph = client.get(f"/api/papers/{paper_id}/graph").json()
    result = next(n for n in graph["nodes"] if n["type"] == "RESULT")
    assert "10⁸" in result["text"] and "108" not in result["text"]
    evidence = client.get(f"/api/nodes/{result['id']}/evidence").json()
    assert result["text"] in evidence["evidence"][0]["anchor"]["text"]
    assert result["verification_status"] == "CANDIDATE"
    quantity = {"value": "10^8", "unit": "dimensionless"}
    assert quantity_matches(result["text"], quantity)
    assert not quantity_matches("The ratio exceeds 108.", quantity)
    resistance = {"value": "42", "unit": "ohm micrometres"}
    assert not quantity_matches("The resistance is 142 ohm micrometres.", resistance)
    assert not quantity_matches("The resistance is -42 ohm micrometres.", resistance)
    assert quantity_matches("The resistance is 42 ohm micrometres.", resistance)


def test_fragment_grouping_keeps_equation_and_two_caption_columns():
    blocks = [
        ParsedBlock("R\nh", (125, 592, 163, 608), "paragraph", 0, 9),
        ParsedBlock("q\nn\n= 2", (147, 598, 185, 615), "paragraph", 1, 9),
        ParsedBlock("π\n(1)\n2D", (130, 592, 294, 615), "paragraph", 2, 9),
        ParsedBlock(
            "Fig. 2 | Caption starting in left column.", (40, 696, 294, 745), "paragraph", 3, 8
        ),
        ParsedBlock(
            "The caption continues here in the second column, with source measurements.",
            (306, 697, 562, 745),
            "paragraph",
            4,
            8,
        ),
        ParsedBlock("Body text must remain separate.", (306, 760, 562, 790), "paragraph", 5, 9),
    ]
    joined = join_fragments(blocks)
    assert len(joined) == 3
    equation = next(b for b in joined if "(1)" in b.text)
    assert equation.bbox == (125, 592, 294, 615)
    assert extract(equation.text, False)[0].type == "EQUATION"
    figure = next(b for b in joined if b.text.startswith("Fig."))
    assert "second column" in figure.text and "Body text" not in figure.text
    assert extract(figure.text, False)[0].type == "FIGURE"


def test_search_line_wrap_ligature_and_multiterm_without_rewriting_source(client: TestClient):
    assert relevance("The ratio is 10⁸.", "10^8")
    assert not relevance("The ratio is 108.", "10^8")
    assert relevance("The energy is 10⁻⁴ eV.", "10^-4 eV")
    assert not relevance("The energy is 10⁴ eV.", "10^-4 eV")
    assert relevance(
        "The electro-\nstatic response has efﬁcient tuning.", "efficient electrostatic"
    )
    assert not relevance("An efficient response.", "efficient electrostatic")
    assert not relevance("A measurement.", "%_")
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 60), "Retrieval regression", fontsize=18)
        page.insert_text(
            (72, 130), "We propose an electro-\nstatic technique for efficient tuning.", fontsize=11
        )
        content = bytes(doc.tobytes())
    paper_id = upload_and_process(client, content)["paper"]["id"]
    hits = client.get(
        f"/api/papers/{paper_id}/search", params={"q": "efficient electrostatic"}
    ).json()
    assert hits and hits[0]["kind"] == "METHOD" and "electro-\nstatic" in hits[0]["text"]
    anchor = client.get(f"/api/anchors/{hits[0]['anchor_id']}/nodes").json()
    assert any(n["id"] == hits[0]["node_id"] for n in anchor)


def test_caption_definitions_and_limitations_keep_individual_source_sentences():
    text = "Fig. 4 A caption. The ratio is defined as the signal divided by noise. b Another panel. This could lead to uncertainties in the estimate. c. Further panel text."
    candidates = extract(text, False)
    definition = next(n for n in candidates if n.type == "DEFINITION")
    limitation = next(n for n in candidates if n.type == "LIMITATION")
    assert definition.text == "The ratio is defined as the signal divided by noise."
    assert limitation.text == "This could lead to uncertainties in the estimate."
    assert all(n.text in text and n.epistemic_status != "AI_INTERPRETATION" for n in candidates)


def test_extended_caption_indices_are_not_fabricated_equation_numbers():
    text = "Extended Data Fig. 5 | Device measurements with a crystal index (0112)\nand voltage V = 0.1 V. The curves are measured data."
    candidates = extract(text, False)
    assert candidates[0].type == "FIGURE"
    assert not any(n.type == "EQUATION" for n in candidates)
    assert not extract("A sample index (0112)\nwas measured at V = 0.1 V.", False)


def test_chart_labels_and_footer_do_not_become_sections():
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 60), "Actual section title", fontname="hebo", fontsize=14)
        page.insert_text(
            (72, 130), "This body paragraph establishes the dominant prose font size.", fontsize=11
        )
        page.insert_text((72, 250), "Chart label", fontname="hebo", fontsize=8)
        page.insert_text((72, 830), "Footer pagination", fontname="hebo", fontsize=11)
        parsed = next(MuPDFParser().pages(bytes(doc.tobytes()), 10))
    headings = [b.text for b in parsed.blocks if b.kind == "heading"]
    assert headings == ["Actual section title"]
