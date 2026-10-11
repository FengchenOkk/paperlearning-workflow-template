import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

from reconcile_current_review import compare, find_old


class ReconciliationGuards(unittest.TestCase):
    def setUp(self):
        self.quote = "We show that the measured response is 42 mV without degradation."
        self.anchor = {
            "id": "old-anchor",
            "source_hash": "source-one",
            "page_number": 2,
            "start_char": 0,
            "end_char": len(self.quote),
            "text": self.quote,
            "bbox": [10, 20, 30, 40],
            "section_titles": [],
            "notation": [],
        }
        self.node = {
            "id": "old-node",
            "paper_id": "old-paper",
            "version": 1,
            "type": "RESULT",
            "layer": "ARGUMENT",
            "text": self.quote,
            "epistemic_status": "AUTHOR_CLAIM",
            "provenance": ["old-anchor"],
        }

    def test_exact_match(self):
        category, proof, _, _ = compare(
            self.node, self.node, [self.anchor], [self.anchor]
        )
        self.assertEqual(category, "EXACT_MATCH")
        self.assertTrue(proof["quantities_units_qualifiers_all_characters_preserved"])

    def test_fresh_identity_is_metadata_not_acceptance(self):
        fresh = self.node | {"id": "new-node", "paper_id": "new-paper"}
        category, _, changes, _ = compare(
            self.node, fresh, [self.anchor], [self.anchor]
        )
        self.assertEqual(category, "NONMATERIAL_METADATA_CHANGE")
        self.assertEqual(changes, [])

    def test_only_observed_literal_heading_may_be_removed(self):
        old = self.node | {"text": "Summary\n" + self.quote}
        observed = self.anchor | {
            "section_titles": ["Summary"],
            "text": "Summary\n" + self.quote,
        }
        self.assertEqual(
            compare(old, self.node, [observed], [observed])[0],
            "NONMATERIAL_METADATA_CHANGE",
        )
        self.assertEqual(
            compare(old, self.node, [self.anchor], [self.anchor])[0],
            "MATERIAL_CONTENT_OR_TYPE_CHANGE",
        )

    def test_quantities_units_signs_and_qualifiers_are_not_erased(self):
        for changed in [
            self.quote.replace("42", "43"),
            self.quote.replace("mV", "V"),
            self.quote.replace("42", "−42"),
            self.quote.replace("without", "with"),
        ]:
            category, proof, _, _ = compare(
                self.node, self.node | {"text": changed}, [self.anchor], [self.anchor]
            )
            self.assertEqual(category, "MATERIAL_CONTENT_OR_TYPE_CHANGE")
            self.assertFalse(
                proof["quantities_units_qualifiers_all_characters_preserved"]
            )

    def test_type_and_source_version_require_material_check(self):
        self.assertEqual(
            compare(
                self.node, self.node | {"type": "METHOD"}, [self.anchor], [self.anchor]
            )[0],
            "MATERIAL_CONTENT_OR_TYPE_CHANGE",
        )
        self.assertEqual(
            compare(
                self.node,
                self.node,
                [self.anchor],
                [self.anchor | {"source_hash": "other"}],
            )[0],
            "MATERIAL_CONTENT_OR_TYPE_CHANGE",
        )

    def test_ambiguous_match_is_not_greedily_assigned(self):
        duplicate = self.node | {"id": "second-old-node"}
        possible = find_old(
            self.node,
            [self.anchor],
            [self.node, duplicate],
            {self.anchor["id"]: self.anchor},
        )
        self.assertEqual(len(possible), 2)

    def test_notation_outside_statement_does_not_change_raw_identity(self):
        source = self.anchor | {
            "text": self.quote + " A separate equation remains unknown.",
            "end_char": len(self.quote) + 36,
        }
        changed = source | {
            "notation_issues": ["Unresolved equation in this source block"]
        }
        category, proof, _, _ = compare(self.node, self.node, [source], [changed])
        self.assertEqual(category, "NONMATERIAL_METADATA_CHANGE")
        self.assertTrue(proof["source_typography_uncertainty"])
        self.assertIn("not accepted", proof["equivalence_scope"])


if __name__ == "__main__":
    unittest.main()
