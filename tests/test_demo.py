import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DemoTest(unittest.TestCase):
    def test_complete_reproducible_loop(self):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_demo.py")], cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads((ROOT / "artifacts" / "summary.json").read_text())
        summary = payload["strategy_results"]
        self.assertEqual({x["policy"] for x in summary}, {"random", "static_topn", "iterative"})
        self.assertTrue(all(x["queries"] == 20 for x in summary))
        self.assertTrue(all(x["all_selected_stable"] for x in summary))
        self.assertGreater(payload["dimensionality_audit"]["uncertain_2d_count"], 0)
        audit = (ROOT / "artifacts" / "dimensionality_audit.csv").read_text()
        self.assertIn("awaiting manual 2D review", audit)
        self.assertIn("band_gap_deviation_from_confirmed_mean_ev", audit)
        for policy in ("random", "static_topn", "iterative"):
            log_text = (ROOT / "artifacts" / f"exploration_log_{policy}.csv").read_text()
            lines = log_text.splitlines()
            self.assertEqual(len(lines), 21)
            self.assertNotIn("uncertain_2d", log_text)
            self.assertNotIn("non_2d", log_text)


if __name__ == "__main__":
    unittest.main()
