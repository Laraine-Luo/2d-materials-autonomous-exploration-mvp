from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from materials_mvp.data import generate_sample_data, load_materials
from materials_mvp.environment import ExplorationEnvironment, save_summary


def main() -> None:
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    data_path = ROOT / config["dataset_path"]
    if not data_path.exists():
        generate_sample_data(data_path)
    rows = load_materials(data_path)
    summaries = []
    for policy in ("random", "static_topn", "iterative"):
        env = ExplorationEnvironment(rows, config, policy)
        summaries.append(env.run())
        env.save_log(ROOT / "artifacts" / f"exploration_log_{policy}.csv")
    save_summary(summaries, ROOT / "artifacts" / "summary.json")
    print("policy        queries  hits  hit_rate  MAE(eV)  stable")
    for item in summaries:
        print(f"{item['policy']:<13} {item['queries']:>7} {item['target_hits']:>5} {item['hit_rate']:>9.2%} {item['mean_absolute_error_ev']:>8.3f}  {item['all_selected_stable']}")
    print("\nEvidence written to artifacts/summary.json and artifacts/exploration_log_*.csv")


if __name__ == "__main__":
    main()

