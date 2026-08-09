import unittest

from materials_mvp.signal import assess_strategy_signal, classify_queried_candidate


CONFIG = {
    "target_band_gap_min_ev": 1.5,
    "target_band_gap_max_ev": 2.5,
    "stability_max_formation_energy_ev_atom": -0.2,
    "stability_max_energy_above_hull_ev_atom": 0.1,
    "dimensionality_training_status": "confirmed_2d",
}


class SignalTests(unittest.TestCase):
    def test_audited_stable_target_is_d2(self):
        row = {
            "material_id": "mp-test",
            "band_gap_ev": 2.0,
            "formation_energy_ev_atom": -0.5,
            "energy_above_hull_ev_atom": 0.02,
            "is_stable": True,
            "dimensionality_status": "confirmed_2d",
        }
        event = classify_queried_candidate(row, CONFIG, 1.9, 0.2, 1)
        self.assertEqual(event.level, "D2")
        self.assertFalse(event.requires_manual_review)

    def test_uncertain_2d_target_stays_d1(self):
        row = {
            "material_id": "mp-review",
            "band_gap_ev": 2.0,
            "formation_energy_ev_atom": -0.5,
            "energy_above_hull_ev_atom": 0.02,
            "is_stable": True,
            "dimensionality_status": "uncertain_2d",
        }
        event = classify_queried_candidate(row, CONFIG, 1.9, 0.2, 1)
        self.assertEqual(event.level, "D1")
        self.assertTrue(event.requires_manual_review)

    def test_margin_alone_cannot_assign_d3(self):
        result = assess_strategy_signal([15] * 20, [10] * 20, [11] * 20)
        self.assertTrue(result["numerical_margin_pass"])
        self.assertFalse(result["d3_assignable"])


if __name__ == "__main__":
    unittest.main()
