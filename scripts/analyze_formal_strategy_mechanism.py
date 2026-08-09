#!/usr/bin/env python3
"""Post-result exploratory diagnostics for the repeated formal evaluation."""

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / "config" / "formal_run_v1.json"
EVAL_CONFIG = ROOT / "config" / "formal_repeated_evaluation_v1.json"
DETAIL_OUTPUT = ROOT / "artifacts" / "formal_repeated_query_details.csv"
FREQUENCY_OUTPUT = ROOT / "artifacts" / "formal_material_selection_frequency.csv"
ROUND_OUTPUT = ROOT / "artifacts" / "formal_round_policy_summary.csv"
FEATURE_OUTPUT = ROOT / "artifacts" / "formal_stable_cohort_features.csv"
SUMMARY_OUTPUT = ROOT / "artifacts" / "formal_strategy_mechanism_analysis.json"

spec = importlib.util.spec_from_file_location("formal_loop_diagnostics", ROOT / "scripts" / "run_formal_closed_loop.py")
formal_loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formal_loop)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    evaluation = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    rows = [row for row in formal_loop.load_rows(base) if row["stability_eligible"]]
    initial = formal_loop.farthest_point_initial_indices(rows, base["initial_samples"])
    initial_ids = {rows[i]["material_id"] for i in initial}
    policies = base["policies"]

    details = []
    holds = defaultdict(Counter)
    for seed in evaluation["seeds"]:
        config = dict(base)
        config["seed"] = seed
        for policy in policies:
            result, logs, _ = formal_loop.run_policy(rows, initial, policy, config)
            for material_id in result["unqueried_material_ids"]:
                holds[policy][material_id] += 1
            for log in logs:
                details.append({"seed": seed, **log})
    write_csv(DETAIL_OUTPUT, details)

    frequency_rows = []
    for row in rows:
        material_id = row["material_id"]
        for policy in policies:
            selected = [d for d in details if d["policy"] == policy and d["material_id"] == material_id]
            frequency_rows.append({
                "material_id": material_id,
                "policy": policy,
                "is_initial_label": material_id in initial_ids,
                "true_band_gap_ev": row["band_gap_ev"],
                "target_hit": base["target_band_gap_min_ev"] <= row["band_gap_ev"] <= base["target_band_gap_max_ev"],
                "selection_count_20": len(selected),
                "first_round_selection_count_20": sum(int(d["round"]) == 1 for d in selected),
                "holdout_count_20": holds[policy][material_id],
                "mean_selection_round": round(mean([float(d["round"]) for d in selected]), 6) if selected else "",
                "mean_predicted_band_gap_ev": round(mean([float(d["predicted_band_gap_ev"]) for d in selected]), 6) if selected else "",
                "mean_uncertainty_ev": round(mean([float(d["uncertainty_ev"]) for d in selected]), 6) if selected else "",
                "mean_absolute_error_ev": round(mean([float(d["absolute_error_ev"]) for d in selected]), 6) if selected else "",
            })
    write_csv(FREQUENCY_OUTPUT, frequency_rows)

    round_rows = []
    for policy in policies:
        for round_number in range(1, base["query_budget"] + 1):
            subset = [d for d in details if d["policy"] == policy and int(d["round"]) == round_number]
            round_rows.append({
                "policy": policy,
                "round": round_number,
                "query_count": len(subset),
                "d2_rate": round(mean([d["signal_level"] == "D2" for d in subset]), 6),
                "target_hit_rate": round(mean([bool(d["target_hit"]) for d in subset]), 6),
                "mean_uncertainty_ev": round(mean([float(d["uncertainty_ev"]) for d in subset]), 6),
                "mean_absolute_error_ev": round(mean([float(d["absolute_error_ev"]) for d in subset]), 6),
            })
    write_csv(ROUND_OUTPUT, round_rows)

    feature_rows = []
    for row in rows:
        feature_rows.append({
            "material_id": row["material_id"],
            "is_initial_label": row["material_id"] in initial_ids,
            **{name: row[name] for name in base["feature_names"]},
            "band_gap_ev": row["band_gap_ev"],
            "target_hit": base["target_band_gap_min_ev"] <= row["band_gap_ev"] <= base["target_band_gap_max_ev"],
            "formation_energy_ev_atom": row["formation_energy_ev_atom"],
            "energy_above_hull_ev_atom": row["energy_above_hull_ev_atom"],
        })
    write_csv(FEATURE_OUTPUT, feature_rows)

    queried = {
        policy: [d for d in details if d["policy"] == policy]
        for policy in policies
    }
    static_target = mean([bool(d["target_hit"]) for d in queried["static_topn"]])
    iterative_target = mean([bool(d["target_hit"]) for d in queried["iterative"]])
    static_uncertainty = mean([float(d["uncertainty_ev"]) for d in queried["static_topn"]])
    iterative_uncertainty = mean([float(d["uncertainty_ev"]) for d in queried["iterative"]])
    static_unique_sequences = len({tuple(d["material_id"] for d in queried["static_topn"] if d["seed"] == seed) for seed in evaluation["seeds"]})
    iterative_unique_sequences = len({tuple(d["material_id"] for d in queried["iterative"] if d["seed"] == seed) for seed in evaluation["seeds"]})
    summary = {
        "analysis_type": "post_result_exploratory_mechanism_analysis",
        "confirmatory_or_causal_claim_allowed": False,
        "seed_count": len(evaluation["seeds"]),
        "query_rows": len(details),
        "initial_material_ids": sorted(initial_ids),
        "observations": {
            "static_topn_target_rate": round(static_target, 6),
            "iterative_target_rate": round(iterative_target, 6),
            "static_topn_mean_selected_uncertainty_ev": round(static_uncertainty, 6),
            "iterative_mean_selected_uncertainty_ev": round(iterative_uncertainty, 6),
            "static_topn_unique_query_sequences": static_unique_sequences,
            "iterative_unique_query_sequences": iterative_unique_sequences,
        },
        "hypotheses_for_future_preregistration": [
            "the frozen initial model already ranks the two target candidates effectively in this cohort",
            "the uncertainty term redirects iterative queries toward below-target candidates",
            "three feedback steps in a four-candidate pool are too few for retraining to recover the exploration cost",
            "the five structural features and bootstrap spread are insufficiently calibrated for this target",
        ],
        "claim_limit": "observational explanation inside one fixed seven-record MP MoS2 cohort; no causal or general strategy claim",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
