import unittest

from materials_mvp.promotion import promotion_decision


class PromotionTests(unittest.TestCase):
    def test_web_index_record_cannot_be_promoted(self):
        passed, reasons = promotion_decision({
            "source_database": "Materials Project",
            "source_surface": "Materials Explorer",
            "material_id": "mp-1434",
        })
        self.assertFalse(passed)
        self.assertIn("source_surface_not_official_api", reasons)

    def test_fully_audited_api_record_can_be_promoted(self):
        record = {
            "source_database": "Materials Project",
            "source_surface": "official API",
            "api_identity_match": "pass",
            "database_version_frozen": "pass",
            "dimensionality_review": "confirmed_2d",
            "calculation_method_review": "pass",
            "material_id": "mp-1434",
            "formula": "MoS2",
            "chemical_system": "Mo-S",
            "structure": {"sites": []},
            "band_gap_ev": 1.38,
            "formation_energy_ev_atom": -0.966,
            "energy_above_hull_ev_atom": 0.0,
            "is_stable_mp_flag": True,
        }
        passed, reasons = promotion_decision(record)
        self.assertTrue(passed)
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
