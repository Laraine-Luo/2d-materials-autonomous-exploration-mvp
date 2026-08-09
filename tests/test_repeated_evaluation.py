import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_formal_repeated_evaluation", ROOT / "scripts" / "run_formal_repeated_evaluation.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepeatedEvaluationTests(unittest.TestCase):
    def test_percentile_bootstrap_is_deterministic(self):
        first = MODULE.paired_bootstrap_ci([1, 0, -1, 1], 1000, 77, 0.95)
        second = MODULE.paired_bootstrap_ci([1, 0, -1, 1], 1000, 77, 0.95)
        self.assertEqual(first, second)

    def test_preregistered_repeated_result_is_scoped_negative_d3(self):
        summary = json.loads((ROOT / "artifacts" / "formal_repeated_evaluation_summary.json").read_text())
        self.assertEqual(summary["seed_count"], 20)
        self.assertEqual(
            summary["discovery_signal_classification"],
            "D3_negative_no_preregistered_advantage_within_fixed_environment",
        )
        self.assertTrue(
            summary["paired_comparisons"]["iterative_minus_random"]["positive_advantage_gate_pass"]
        )
        self.assertTrue(
            summary["paired_comparisons"]["iterative_minus_static_topn"]["minimum_advantage_excluded"]
        )
        self.assertTrue(
            all(item["total_stability_violations"] == 0 for item in summary["aggregate_results"].values())
        )


if __name__ == "__main__":
    unittest.main()
