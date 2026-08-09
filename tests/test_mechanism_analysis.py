import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MechanismAnalysisTests(unittest.TestCase):
    def test_analysis_is_explicitly_nonconfirmatory(self):
        summary = json.loads((ROOT / "artifacts" / "formal_strategy_mechanism_analysis.json").read_text())
        self.assertEqual(summary["analysis_type"], "post_result_exploratory_mechanism_analysis")
        self.assertFalse(summary["confirmatory_or_causal_claim_allowed"])
        self.assertEqual(summary["query_rows"], 180)

    def test_selection_frequency_supports_reported_observation(self):
        with (ROOT / "artifacts" / "formal_material_selection_frequency.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        keyed = {(row["material_id"], row["policy"]): row for row in rows}
        self.assertEqual(keyed[("mp-1018809", "static_topn")]["selection_count_20"], "0")
        self.assertEqual(keyed[("mp-1018809", "iterative")]["selection_count_20"], "20")
        self.assertEqual(keyed[("mp-1025874", "static_topn")]["selection_count_20"], "20")
        self.assertEqual(keyed[("mp-1023939", "static_topn")]["selection_count_20"], "20")


if __name__ == "__main__":
    unittest.main()
