import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryIndexTests(unittest.TestCase):
    def test_all_12_index_records_are_quarantined(self):
        path = ROOT / "data/materials_project_manual_probe/mos2_formula_index_12.csv"
        with path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["source_database"] == "Materials Project" for row in rows))
        self.assertTrue(all(row["training_eligible"] == "False" for row in rows))
        self.assertEqual(len({row["material_id"] for row in rows}), 12)

    def test_mp1434_passport_is_promoted_only_after_review(self):
        passport = json.loads(
            (ROOT / "artifacts/mp-1434-evidence-passport.json").read_text(encoding="utf-8")
        )
        self.assertEqual(passport["exploration_status_discovery_level"], "D0")
        self.assertTrue(passport["exploration_status_training_eligible"])
        self.assertEqual(passport["official_api_evidence"]["status"], "received")
        self.assertEqual(passport["manual_audit"]["dimensionality_review"], "confirmed_2d")
        self.assertEqual(passport["manual_audit"]["calculation_method_review"], "pass")
        self.assertEqual(passport["manual_audit"]["reviewer"], "project_owner_user")


if __name__ == "__main__":
    unittest.main()
