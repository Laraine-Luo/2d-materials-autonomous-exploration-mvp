import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MX2IndexTests(unittest.TestCase):
    def test_validation_scope_is_frozen_and_mos2_is_development_only(self):
        config = json.loads((ROOT / "config" / "mp_mx2_validation_index_v1.json").read_text())
        self.assertEqual(len(config["chemical_scope"]["formula_queries"]), 6)
        self.assertEqual(config["cohort_roles"]["MoS2"], "development_and_drift_control_only")
        for formula in ("MoSe2", "MoTe2", "WS2", "WSe2", "WTe2"):
            self.assertEqual(config["cohort_roles"][formula], "independent_validation_candidate_source")

    def test_failed_probe_does_not_claim_records(self):
        audit = json.loads((ROOT / "artifacts" / "mp_mx2_validation_index_audit.json").read_text())
        if audit["status"] == "failed":
            self.assertEqual(audit["records_returned"], 0)
            self.assertFalse((ROOT / "artifacts" / "mp_mx2_validation_index.csv").exists())
        else:
            self.assertEqual(audit["records_returned"], 44)
            self.assertEqual(audit["unique_material_ids"], 44)
            self.assertEqual(audit["combined_stability_prefilter_pass_count"], 32)
            self.assertTrue((ROOT / "artifacts" / "mp_mx2_validation_index.csv").exists())
        self.assertFalse(audit["credential_recorded"])

    def test_structure_queue_is_label_blind_and_identity_exact(self):
        queue = json.loads((ROOT / "config" / "mp_mx2_structure_audit_queue_v1.json").read_text())
        freeze = json.loads((ROOT / "artifacts" / "mp_mx2_structure_queue_freeze_audit.json").read_text())
        response = json.loads((ROOT / "artifacts" / "mp_mx2_structure_response_audit.json").read_text())
        self.assertEqual(queue["record_count"], 25)
        self.assertFalse(queue["band_gap_used_for_selection"])
        self.assertFalse(freeze["band_gap_used_for_selection"])
        self.assertTrue(response["identity_exact_match"])
        self.assertEqual(response["structures_returned"], 25)
        self.assertEqual(response["origins_returned"], 25)

    def test_combined_review_is_proposal_only(self):
        proposal = json.loads((ROOT / "artifacts" / "mp_mx2_combined_review_proposal.json").read_text())
        self.assertTrue(proposal["proposal_only"])
        self.assertFalse(proposal["automatic_approval"])
        self.assertEqual(proposal["recommended_confirmed_2d_count"], 25)
        self.assertEqual(proposal["recommended_method_pass_count"], 24)
        self.assertEqual(proposal["method_attention_count"], 1)
        self.assertTrue(all(not row["training_eligible"] for row in proposal["records"]))


if __name__ == "__main__":
    unittest.main()
