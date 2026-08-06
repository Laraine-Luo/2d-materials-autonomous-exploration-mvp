import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DemoTest(unittest.TestCase):
    def test_complete_reproducible_loop(self):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_demo.py")], cwd=ROOT, check=True, capture_output=True, text=True)
        summary = json.loads((ROOT / "artifacts" / "summary.json").read_text())
        self.assertEqual({x["policy"] for x in summary}, {"random", "static_topn", "iterative"})
        self.assertTrue(all(x["queries"] == 20 for x in summary))
        self.assertTrue(all(x["all_selected_stable"] for x in summary))
        for policy in ("random", "static_topn", "iterative"):
            lines = (ROOT / "artifacts" / f"exploration_log_{policy}.csv").read_text().splitlines()
            self.assertEqual(len(lines), 21)


if __name__ == "__main__":
    unittest.main()

