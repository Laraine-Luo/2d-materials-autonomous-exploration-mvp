import importlib.util
import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_formal_closed_loop", ROOT / "scripts" / "run_formal_closed_loop.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FormalLoopTests(unittest.TestCase):
    def test_initial_diversity_selection_does_not_use_band_gap(self):
        rows = [
            {"material_id": f"mp-{i}", "feature_vector": [float(i), float(i % 2)], "band_gap_ev": float(i)}
            for i in range(6)
        ]
        chosen_before = MODULE.farthest_point_initial_indices(rows, 3)
        for row in rows:
            row["band_gap_ev"] = 100.0 - row["band_gap_ev"]
        chosen_after = MODULE.farthest_point_initial_indices(rows, 3)
        self.assertEqual(chosen_before, chosen_after)

    def test_current_3plus3plus1_budget_matches_stable_cohort(self):
        config = json.loads((ROOT / "config" / "formal_run_v1.json").read_text())
        with (ROOT / "artifacts" / "formal_mp_dataset.csv").open(newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row["stability_eligible"].lower() == "true"]
        self.assertEqual(len(rows), 7)
        self.assertEqual(config["initial_samples"], 3)
        self.assertEqual(config["query_budget"], 3)
        self.assertEqual(len(rows) - config["initial_samples"] - config["query_budget"], 1)

    def test_formal_run_completed_with_one_holdout_per_policy(self):
        summary = json.loads((ROOT / "artifacts" / "formal_closed_loop_summary.json").read_text())
        self.assertEqual(summary["run_id"], "mp-mos2-3plus3plus1-v1")
        self.assertEqual(summary["eligible_records"], 7)
        self.assertEqual(summary["query_budget_per_policy"], 3)
        for result in summary["strategy_results"]:
            self.assertEqual(result["queries"], 3)
            self.assertEqual(len(result["unqueried_material_ids"]), 1)


if __name__ == "__main__":
    unittest.main()
