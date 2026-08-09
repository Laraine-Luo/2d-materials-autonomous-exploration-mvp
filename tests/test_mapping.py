import json
import unittest
from pathlib import Path

from materials_mvp.mapping import load_mapping_list, map_materials_project_record, scientific_pool_eligibility


ROOT = Path(__file__).resolve().parents[1]


class MappingTests(unittest.TestCase):
    def test_mapping_names_are_unique_and_status_prefixed(self):
        mappings = load_mapping_list(ROOT / "config/materials_project_mapping_list.json")
        states = [x for x in mappings if x["group"] == "exploration_state"]
        self.assertTrue(states)
        self.assertTrue(all(x["mapped_name"].startswith("exploration_status_") for x in states))

    def test_mp_record_mapping(self):
        mappings = load_mapping_list(ROOT / "config/materials_project_mapping_list.json")
        raw = {"material_id": "mp-1434", "formula_pretty": "MoS2", "band_gap": 1.38}
        mapped = map_materials_project_record(raw, mappings)
        self.assertEqual(mapped["material_id"], "mp-1434")
        self.assertEqual(mapped["formula"], "MoS2")
        self.assertEqual(mapped["source_database"], "Materials Project")

    def test_non_mp_record_is_ineligible(self):
        eligible, reasons = scientific_pool_eligibility(
            {"source_database": "synthetic", "material_id": "demo"}, "v1", "R2SCAN"
        )
        self.assertFalse(eligible)
        self.assertIn("source_is_not_materials_project", reasons)


if __name__ == "__main__":
    unittest.main()
