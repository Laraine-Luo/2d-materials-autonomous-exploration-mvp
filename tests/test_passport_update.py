import unittest

from materials_mvp.passport import apply_api_record


class PassportUpdateTests(unittest.TestCase):
    def test_api_data_does_not_bypass_manual_review(self):
        passport = {
            "material_id": "mp-1434",
            "formula": "MoS2",
            "chemical_system": "Mo-S",
            "source_database": "Materials Project",
            "manual_audit": {"dimensionality_review": "pending", "calculation_method_review": "pending"},
            "exploration_status_training_eligible": False,
            "exploration_status_discovery_level": "D0",
            "promotion_decision": "blocked",
        }
        record = {
            "material_id": "mp-1434", "source_database_version": "v1",
            "structure": {"sites": []}, "band_gap_ev": 1.38,
            "formation_energy_ev_atom": -0.966, "energy_above_hull_ev_atom": 0.0,
            "is_stable_mp_flag": True, "source_calculation_method": "R2SCAN",
            "origins_task_id": "task-1",
        }
        updated, change = apply_api_record(passport, record, "v1")
        self.assertFalse(updated["exploration_status_training_eligible"])
        self.assertEqual(updated["promotion_decision"], "blocked")
        self.assertIn("dimensionality_not_confirmed", change["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
