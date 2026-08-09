import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MX2ReviewDecisionTests(unittest.TestCase):
    def test_signed_decision_grants_validation_not_training(self):
        audit = json.loads((ROOT / "artifacts" / "mp_mx2_human_review_decision_audit.json").read_text())
        self.assertEqual(audit["actor"], "project_owner_user")
        self.assertEqual(audit["approved_validation_candidate_count"], 24)
        self.assertEqual(audit["quarantined_material_ids"], ["mp-1120746"])
        self.assertEqual(audit["training_eligible_count"], 0)
        self.assertTrue(all(not row["after"]["training_eligible"] for row in audit["transitions"]))

    def test_agent_observation_interface_has_no_band_gap(self):
        with (ROOT / "artifacts" / "mx2_validation_agent_observations.csv").open() as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        self.assertNotIn("band_gap_ev", reader.fieldnames)
        self.assertEqual(len(rows), 25)
        self.assertEqual(sum(row["exploration_status_validation_eligible"] == "True" for row in rows), 24)
        for row in rows:
            float(row["density_g_cm3"])

    def test_public_passports_use_label_commitments(self):
        paths = sorted((ROOT / "artifacts" / "mx2_validation_passports").glob("*.json"))
        self.assertEqual(len(paths), 25)
        for path in paths:
            passport = json.loads(path.read_text())
            self.assertNotIn("band_gap_ev", passport)
            self.assertEqual(len(passport["band_gap_oracle_commitment_sha256"]), 64)
            self.assertFalse(passport["exploration_status_training_eligible"])


if __name__ == "__main__":
    unittest.main()
