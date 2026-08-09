#!/usr/bin/env python3
"""Run the preregistered paired 20-seed formal strategy evaluation."""

from __future__ import annotations

import csv
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_CONFIG_PATH = ROOT / "config" / "formal_repeated_evaluation_v1.json"
OUTPUT_JSON = ROOT / "artifacts" / "formal_repeated_evaluation_summary.json"
OUTPUT_CSV = ROOT / "artifacts" / "formal_repeated_evaluation_runs.csv"

spec = importlib.util.spec_from_file_location("formal_loop", ROOT / "scripts" / "run_formal_closed_loop.py")
formal_loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formal_loop)


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def paired_bootstrap_ci(differences: list[float], resamples: int, seed: int, confidence: float) -> list[float]:
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        means.append(sum(sample) / len(sample))
    alpha = 1 - confidence
    return [round(percentile(means, alpha / 2), 6), round(percentile(means, 1 - alpha / 2), 6)]


def first_d2_budget(logs: list[dict]) -> int | None:
    for row in logs:
        if row["signal_level"] == "D2":
            return int(row["round"])
    return None


def main() -> int:
    eval_config = json.loads(EVAL_CONFIG_PATH.read_text(encoding="utf-8"))
    base_path = ROOT / eval_config["base_run_config"]
    base = json.loads(base_path.read_text(encoding="utf-8"))
    audited = formal_loop.load_rows(base)
    rows = [row for row in audited if row["stability_eligible"]]
    if len(rows) != base["eligible_passport_count_required"]:
        raise RuntimeError("Stable cohort changed after preregistration")
    initial = formal_loop.farthest_point_initial_indices(rows, base["initial_samples"])

    run_rows = []
    by_policy = {policy: [] for policy in base["policies"]}
    for seed in eval_config["seeds"]:
        config = dict(base)
        config["seed"] = seed
        for policy in base["policies"]:
            result, logs, _ = formal_loop.run_policy(rows, initial, policy, config)
            record = {
                "seed": seed,
                "policy": policy,
                "d2_hits": result["d2_hits"],
                "hit_rate": result["hit_rate"],
                "mean_absolute_error_ev": result["mean_absolute_error_ev"],
                "first_d2_budget": first_d2_budget(logs),
                "stability_violations": sum(
                    not next(r for r in rows if r["material_id"] == log["material_id"])["stability_eligible"]
                    for log in logs
                ),
                "queried_material_ids": "|".join(result["queried_material_ids"]),
                "unqueried_material_ids": "|".join(result["unqueried_material_ids"]),
            }
            run_rows.append(record)
            by_policy[policy].append(record)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(run_rows[0]))
        writer.writeheader()
        writer.writerows(run_rows)

    aggregates = {}
    for policy, records in by_policy.items():
        aggregates[policy] = {
            "mean_d2_hits": round(sum(r["d2_hits"] for r in records) / len(records), 6),
            "mean_hit_rate": round(sum(r["hit_rate"] for r in records) / len(records), 6),
            "mean_absolute_error_ev": round(sum(r["mean_absolute_error_ev"] for r in records) / len(records), 6),
            "mean_first_d2_budget": round(sum(r["first_d2_budget"] for r in records if r["first_d2_budget"] is not None) / sum(r["first_d2_budget"] is not None for r in records), 6),
            "total_stability_violations": sum(r["stability_violations"] for r in records),
        }

    comparisons = {}
    iterative = by_policy["iterative"]
    positive_all = True
    negative_any = False
    for offset, baseline in enumerate(("random", "static_topn")):
        paired = [i["d2_hits"] - b["d2_hits"] for i, b in zip(iterative, by_policy[baseline])]
        ci = paired_bootstrap_ci(
            paired,
            eval_config["paired_bootstrap_resamples"],
            eval_config["bootstrap_seed"] + offset,
            eval_config["confidence_level"],
        )
        mean_difference = sum(paired) / len(paired)
        required_gain = eval_config["minimum_relative_advantage"] * aggregates[baseline]["mean_d2_hits"]
        positive = mean_difference >= required_gain and ci[0] > 0
        negative = ci[1] < required_gain
        positive_all = positive_all and positive
        negative_any = negative_any or negative
        comparisons[f"iterative_minus_{baseline}"] = {
            "paired_mean_d2_difference": round(mean_difference, 6),
            "paired_bootstrap_95_ci": ci,
            "minimum_meaningful_gain_d2": round(required_gain, 6),
            "positive_advantage_gate_pass": positive,
            "minimum_advantage_excluded": negative,
        }

    if positive_all:
        classification = "D3_positive_strategy_signal_within_fixed_environment"
    elif negative_any:
        classification = "D3_negative_no_preregistered_advantage_within_fixed_environment"
    else:
        classification = "D2_repeated_evidence_inconclusive_for_strategy_advantage"
    summary = {
        "evaluation_id": eval_config["evaluation_id"],
        "status": "completed",
        "source_database": base["source_database"],
        "database_version": base["database_version"],
        "stable_cohort_size": len(rows),
        "seed_count": len(eval_config["seeds"]),
        "initial_material_ids": [rows[i]["material_id"] for i in initial],
        "query_budget_per_policy": base["query_budget"],
        "aggregate_results": aggregates,
        "paired_comparisons": comparisons,
        "discovery_signal_classification": classification,
        "scope_limit": eval_config["scope_limit"],
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
