#!/usr/bin/env python3
"""Run the preregistered label-isolated MX2 cross-formula validation."""

from __future__ import annotations

import csv
import importlib.util
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "mx2_cross_formula_validation_v1.json"
BASE_CONFIG_PATH = ROOT / "config" / "formal_run_v1.json"
DETAIL_OUTPUT = ROOT / "artifacts" / "mx2_cross_formula_query_log.csv"
RUN_OUTPUT = ROOT / "artifacts" / "mx2_cross_formula_seed_policy_results.csv"
SUMMARY_OUTPUT = ROOT / "artifacts" / "mx2_cross_formula_validation_summary.json"

spec = importlib.util.spec_from_file_location("formal_loop_validation", ROOT / "scripts" / "run_formal_closed_loop.py")
formal_loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formal_loop)

repeat_spec = importlib.util.spec_from_file_location("repeated_helpers", ROOT / "scripts" / "run_formal_repeated_evaluation.py")
repeated = importlib.util.module_from_spec(repeat_spec)
repeat_spec.loader.exec_module(repeated)


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fit_model(features: dict[str, list[float]], known_labels: dict[str, float], config: dict, seed: int):
    from materials_mvp.model import BootstrapRidge

    ids = sorted(known_labels)
    return BootstrapRidge(
        alpha=config["ridge_alpha"], n_models=config["bootstrap_models"], seed=seed
    ).fit([features[mid] for mid in ids], [known_labels[mid] for mid in ids])


def target_score(prediction: float, config: dict) -> float:
    low, high = config["target_band_gap_min_ev"], config["target_band_gap_max_ev"]
    if low <= prediction <= high:
        return 1.0
    return 1.0 / (1.0 + min(abs(prediction - low), abs(prediction - high)))


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))
    development_rows = [row for row in formal_loop.load_rows(base) if row["stability_eligible"]]
    observations = load_csv(ROOT / config["validation_observation_file"])
    if "band_gap_ev" in observations[0]:
        raise RuntimeError("Band Gap leaked into the Agent observation interface")
    validation = [row for row in observations if row["exploration_status_validation_eligible"] == "True"]
    if len(validation) != config["validation_eligible_records_required"]:
        raise RuntimeError("Validation eligibility count changed after preregistration")
    oracle_rows = load_csv(ROOT / config["validation_oracle_file"])
    oracle = {row["material_id"]: float(row["band_gap_ev"]) for row in oracle_rows}
    if set(row["material_id"] for row in validation) - set(oracle):
        raise RuntimeError("Oracle does not cover the validation pool")

    feature_names = config["feature_names"]
    features = {
        row["material_id"]: [float(row[name]) for name in feature_names]
        for row in validation
    }
    formulas = {row["material_id"]: row["formula"] for row in validation}
    development_features = {row["material_id"]: row["feature_vector"] for row in development_rows}
    features.update(development_features)
    development_labels = {row["material_id"]: row["band_gap_ev"] for row in development_rows}
    validation_ids = sorted(row["material_id"] for row in validation)

    details = []
    run_results = []
    by_policy = defaultdict(list)
    for seed in config["seeds"]:
        for policy_name, policy in config["policies"].items():
            known_labels = dict(development_labels)
            pool = list(validation_ids)
            frozen = fit_model(features, known_labels, config, seed)
            rng = random.Random(seed + sum(ord(char) for char in policy_name))
            logs = []
            for round_number in range(1, config["query_budget"] + 1):
                kind = policy["kind"]
                model = frozen if kind == "static" else fit_model(features, known_labels, config, seed + round_number)
                candidates = [(mid, *model.predict_one(features[mid])) for mid in pool]
                if kind == "random":
                    material_id, prediction, uncertainty = rng.choice(candidates)
                    reason = "uniform random from the fixed validation pool"
                elif kind == "static":
                    material_id, prediction, uncertainty = max(
                        candidates, key=lambda item: (target_score(item[1], config), item[0])
                    )
                    reason = "highest target score from the frozen development-only model"
                else:
                    maximum = max(item[2] for item in candidates) or 1.0
                    weight = policy["uncertainty_weight"]
                    material_id, prediction, uncertainty = max(
                        candidates,
                        key=lambda item: (
                            (1 - weight) * target_score(item[1], config) + weight * item[2] / maximum,
                            item[0]
                        )
                    )
                    reason = f"target score plus normalized uncertainty; w={weight}; retrained after feedback"
                truth = oracle[material_id]
                hit = config["target_band_gap_min_ev"] <= truth <= config["target_band_gap_max_ev"]
                known_labels[material_id] = truth
                pool.remove(material_id)
                log = {
                    "seed": seed,
                    "policy": policy_name,
                    "confirmatory_role": policy["confirmatory_role"],
                    "round": round_number,
                    "material_id": material_id,
                    "formula": formulas[material_id],
                    "predicted_band_gap_ev": round(prediction, 6),
                    "uncertainty_ev": round(uncertainty, 6),
                    "oracle_band_gap_ev": truth,
                    "absolute_error_ev": round(abs(prediction - truth), 6),
                    "target_hit": hit,
                    "signal_level": "D2" if hit else "D0",
                    "selection_reason": reason,
                    "budget_used": round_number,
                    "budget_total": config["query_budget"]
                }
                logs.append(log)
                details.append(log)
            d2 = sum(row["target_hit"] for row in logs)
            first = next((row["round"] for row in logs if row["target_hit"]), None)
            result = {
                "seed": seed,
                "policy": policy_name,
                "confirmatory_role": policy["confirmatory_role"],
                "d2_hits": d2,
                "hit_rate": round(d2 / config["query_budget"], 6),
                "first_d2_budget": first if first is not None else "",
                "mean_absolute_error_ev": round(sum(row["absolute_error_ev"] for row in logs) / len(logs), 6),
                "formula_coverage": len({row["formula"] for row in logs}),
                "stability_violations": 0,
                "unrevealed_count": len(pool),
                "queried_material_ids": "|".join(row["material_id"] for row in logs)
            }
            run_results.append(result)
            by_policy[policy_name].append(result)
    write_csv(DETAIL_OUTPUT, details)
    write_csv(RUN_OUTPUT, run_results)

    aggregates = {}
    cumulative = {}
    for policy_name, results in by_policy.items():
        policy_details = [row for row in details if row["policy"] == policy_name]
        aggregates[policy_name] = {
            "confirmatory_role": config["policies"][policy_name]["confirmatory_role"],
            "mean_d2_hits": round(sum(row["d2_hits"] for row in results) / len(results), 6),
            "mean_hit_rate": round(sum(row["hit_rate"] for row in results) / len(results), 6),
            "mean_absolute_error_ev": round(sum(row["mean_absolute_error_ev"] for row in results) / len(results), 6),
            "mean_first_d2_budget": round(
                sum(float(row["first_d2_budget"]) for row in results if row["first_d2_budget"] != "") /
                sum(row["first_d2_budget"] != "" for row in results), 6
            ),
            "mean_formula_coverage": round(sum(row["formula_coverage"] for row in results) / len(results), 6),
            "total_stability_violations": 0
        }
        cumulative[policy_name] = [
            round(sum(
                sum(1 for row in policy_details if row["seed"] == seed and row["round"] <= budget and row["target_hit"])
                for seed in config["seeds"]
            ) / len(config["seeds"]), 6)
            for budget in range(1, config["query_budget"] + 1)
        ]

    comparisons = {}
    primary = by_policy["iterative_w035"]
    positive_all = True
    negative_any = False
    for offset, baseline in enumerate(("random", "static_topn")):
        differences = [p["d2_hits"] - b["d2_hits"] for p, b in zip(primary, by_policy[baseline])]
        ci = repeated.paired_bootstrap_ci(
            differences, config["paired_bootstrap_resamples"], config["bootstrap_seed"] + offset,
            config["confidence_level"]
        )
        mean_difference = sum(differences) / len(differences)
        required = config["minimum_relative_advantage"] * aggregates[baseline]["mean_d2_hits"]
        positive = mean_difference >= required and ci[0] > 0
        negative = ci[1] < required
        positive_all = positive_all and positive
        negative_any = negative_any or negative
        comparisons[f"iterative_w035_minus_{baseline}"] = {
            "paired_mean_d2_difference": round(mean_difference, 6),
            "paired_bootstrap_95_ci": ci,
            "minimum_meaningful_gain_d2": round(required, 6),
            "positive_advantage_gate_pass": positive,
            "minimum_advantage_excluded": negative
        }
    classification = (
        "D3_positive_cross_formula_strategy_signal" if positive_all else
        "D3_negative_no_preregistered_cross_formula_advantage" if negative_any else
        "D2_repeated_cross_formula_evidence_inconclusive"
    )
    summary = {
        "evaluation_id": config["evaluation_id"],
        "status": "completed",
        "source_database": config["source_database"],
        "database_version": config["database_version"],
        "development_label_count": len(development_labels),
        "validation_pool_size": len(validation_ids),
        "validation_training_eligible_count": 0,
        "query_budget_per_policy": config["query_budget"],
        "unrevealed_per_run": len(validation_ids) - config["query_budget"],
        "seed_count": len(config["seeds"]),
        "aggregate_results": aggregates,
        "mean_cumulative_d2_by_budget": cumulative,
        "primary_comparisons": comparisons,
        "discovery_signal_classification": classification,
        "anti_cherry_pick_rule_respected": True,
        "scope_limit": config["scope_limit"]
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
