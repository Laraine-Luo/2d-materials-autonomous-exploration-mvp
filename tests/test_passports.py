import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PassportTests(unittest.TestCase):
    def test_reviewed_passports_match_signed_decision(self):
        passports = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in (ROOT / "artifacts/mos2_passports").glob("*.json")
        ]
        self.assertEqual(len(passports), 11)
        # mp-1434 is stored separately; among these 11 passports, 8 are promoted.
        self.assertEqual(sum(p["exploration_status_training_eligible"] for p in passports), 8)
        self.assertEqual(sum(p["promotion_decision"] == "blocked" for p in passports), 3)
        self.assertTrue(all(p["exploration_status_discovery_level"] == "D0" for p in passports))
        self.assertTrue(all(p.get("manual_audit", {}).get("reviewer") == "project_owner_user" for p in passports))


if __name__ == "__main__":
    unittest.main()
