import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MX2CrossFormulaValidationTests(unittest.TestCase):
    def test_preregistered_protocol_keeps_primary_policy_fixed(self):
        config = json.loads((ROOT / "config" / "mx2_cross_formula_validation_v1.json").read_text())
        self.assertEqual(config["policies"]["iterative_w035"]["confirmatory_role"], "primary_policy")
        self.assertEqual(config["policies"]["iterative_w015"]["confirmatory_role"], "diagnostic_ablation_only")
        self.assertEqual(config["query_budget"], 8)
        self.assertEqual(len(config["seeds"]), 20)

    def test_cross_formula_result_preserves_label_and_budget_boundary(self):
        summary = json.loads((ROOT / "artifacts" / "mx2_cross_formula_validation_summary.json").read_text())
        self.assertEqual(summary["validation_pool_size"], 24)
        self.assertEqual(summary["validation_training_eligible_count"], 0)
        self.assertEqual(summary["unrevealed_per_run"], 16)
        self.assertTrue(summary["anti_cherry_pick_rule_respected"])
        self.assertEqual(
            summary["discovery_signal_classification"],
            "D3_negative_no_preregistered_cross_formula_advantage"
        )
        self.assertTrue(summary["primary_comparisons"]["iterative_w035_minus_random"]["positive_advantage_gate_pass"])
        self.assertTrue(summary["primary_comparisons"]["iterative_w035_minus_static_topn"]["minimum_advantage_excluded"])

    def test_every_run_uses_eight_queries_without_stability_violation(self):
        with (ROOT / "artifacts" / "mx2_cross_formula_seed_policy_results.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 100)
        self.assertTrue(all(row["unrevealed_count"] == "16" for row in rows))
        self.assertTrue(all(row["stability_violations"] == "0" for row in rows))


if __name__ == "__main__":
    unittest.main()
