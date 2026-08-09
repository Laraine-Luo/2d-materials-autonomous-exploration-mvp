#!/usr/bin/env python3
"""Run the preregistered MP 3+3+1 micro-loop on signed evidence passports."""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from materials_mvp.model import BootstrapRidge
from materials_mvp.signal import classify_queried_candidate

CONFIG_PATH = ROOT / "config" / "formal_run_v1.json"
PRIMARY = ROOT / "artifacts" / "mp-1434-evidence-passport.json"
PASSPORT_DIR = ROOT / "artifacts" / "mos2_passports"
DIM_AUDIT = ROOT / "artifacts" / "mos2_dimensionality_evidence_audit.json"
DATASET_OUTPUT = ROOT / "artifacts" / "formal_mp_dataset.csv"
SUMMARY_OUTPUT = ROOT / "artifacts" / "formal_closed_loop_summary.json"


def load_rows(config: dict) -> list[dict]:
    from pymatgen.core import Structure

    dim = json.loads(DIM_AUDIT.read_text(encoding="utf-8"))
    layers = {row["material_id"]: len(row["component_dimensions"]) for row in dim["records"]}
    paths = [PRIMARY] + sorted(PASSPORT_DIR.glob("*.json"))
    rows = []
    for path in paths:
        passport = json.loads(path.read_text(encoding="utf-8"))
        if not passport.get("exploration_status_training_eligible"):
            continue
        structure = Structure.from_dict(passport["structure"])
        lengths = list(structure.lattice.abc)
        feature_values = {
            "n_sites": float(len(structure)),
            "volume_per_atom_angstrom3": float(structure.volume / len(structure)),
            "density_g_cm3": float(structure.density),
            "lattice_anisotropy": float(max(lengths) / min(lengths)),
            "layer_component_count": float(layers[passport["material_id"]]),
        }
        row = {
            "material_id": passport["material_id"],
            "formula": passport["formula"],
            **feature_values,
            "feature_vector": [feature_values[name] for name in config["feature_names"]],
            "band_gap_ev": float(passport["band_gap_ev"]),
            "formation_energy_ev_atom": float(passport["formation_energy_ev_atom"]),
            "energy_above_hull_ev_atom": float(passport["energy_above_hull_ev_atom"]),
            "is_stable": bool(passport["is_stable_mp_flag"]),
            "dimensionality_status": passport["manual_audit"]["dimensionality_review"],
            "source_database_version": passport["source_database_version"],
            "source_calculation_method": passport["source_calculation_method"],
        }
        row["stability_eligible"] = (
            row["formation_energy_ev_atom"] <= config["stability_max_formation_energy_ev_atom"]
            and (
                row["energy_above_hull_ev_atom"] <= config["stability_max_energy_above_hull_ev_atom"]
                or row["is_stable"]
            )
        )
        rows.append(row)
    rows.sort(key=lambda row: row["material_id"])
    return rows


def standardized_vectors(rows: list[dict]) -> list[list[float]]:
    p = len(rows[0]["feature_vector"])
    means = [sum(row["feature_vector"][j] for row in rows) / len(rows) for j in range(p)]
    scales = []
    for j in range(p):
        variance = sum((row["feature_vector"][j] - means[j]) ** 2 for row in rows) / max(1, len(rows) - 1)
        scales.append(max(math.sqrt(variance), 1e-8))
    return [[(value - means[j]) / scales[j] for j, value in enumerate(row["feature_vector"])] for row in rows]


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def farthest_point_initial_indices(rows: list[dict], count: int) -> list[int]:
    vectors = standardized_vectors(rows)
    centroid = [sum(v[j] for v in vectors) / len(vectors) for j in range(len(vectors[0]))]
    first = max(range(len(rows)), key=lambda i: (distance(vectors[i], centroid), rows[i]["material_id"]))
    chosen = [first]
    while len(chosen) < count:
        remaining = [i for i in range(len(rows)) if i not in chosen]
        next_index = max(
            remaining,
            key=lambda i: (min(distance(vectors[i], vectors[j]) for j in chosen), rows[i]["material_id"]),
        )
        chosen.append(next_index)
    return chosen


def target_score(prediction: float, config: dict) -> float:
    low, high = config["target_band_gap_min_ev"], config["target_band_gap_max_ev"]
    if low <= prediction <= high:
        return 1.0
    return 1.0 / (1.0 + min(abs(prediction - low), abs(prediction - high)))


def fit_model(rows: list[dict], known: list[int], config: dict) -> BootstrapRidge:
    return BootstrapRidge(
        alpha=config["ridge_alpha"], n_models=config["bootstrap_models"], seed=config["seed"]
    ).fit([rows[i]["feature_vector"] for i in known], [rows[i]["band_gap_ev"] for i in known])


def run_policy(rows: list[dict], initial: list[int], policy: str, config: dict) -> tuple[dict, list[dict], list[int]]:
    known = list(initial)
    pool = [i for i in range(len(rows)) if i not in known]
    frozen = fit_model(rows, known, config)
    rng = random.Random(config["seed"] + {"random": 1, "static_topn": 2, "iterative": 3}[policy])
    logs = []
    while pool and len(logs) < config["query_budget"]:
        model = frozen if policy == "static_topn" else fit_model(rows, known, config)
        candidates = [(i, *model.predict_one(rows[i]["feature_vector"])) for i in pool]
        if policy == "random":
            index, prediction, uncertainty = rng.choice(candidates)
            reason = "uniform random from signed stable pool"
        elif policy == "static_topn":
            index, prediction, uncertainty = max(candidates, key=lambda x: (target_score(x[1], config), rows[x[0]]["material_id"]))
            reason = "highest target score from frozen initial model"
        else:
            max_uncertainty = max(x[2] for x in candidates) or 1.0
            weight = config["uncertainty_weight"]
            index, prediction, uncertainty = max(
                candidates,
                key=lambda x: (
                    (1 - weight) * target_score(x[1], config) + weight * x[2] / max_uncertainty,
                    rows[x[0]]["material_id"],
                ),
            )
            reason = "target score plus bootstrap uncertainty; retrained after feedback"
        row = rows[index]
        pool.remove(index)
        known.append(index)
        round_number = len(logs) + 1
        signal = classify_queried_candidate(row, config, prediction, uncertainty, round_number)
        hit = config["target_band_gap_min_ev"] <= row["band_gap_ev"] <= config["target_band_gap_max_ev"]
        logs.append({
            "round": round_number,
            "policy": policy,
            "material_id": row["material_id"],
            "predicted_band_gap_ev": round(prediction, 6),
            "uncertainty_ev": round(uncertainty, 6),
            "true_band_gap_ev": row["band_gap_ev"],
            "absolute_error_ev": round(abs(prediction - row["band_gap_ev"]), 6),
            "target_hit": hit,
            "formation_energy_ev_atom": row["formation_energy_ev_atom"],
            "energy_above_hull_ev_atom": row["energy_above_hull_ev_atom"],
            "is_stable_mp_flag": row["is_stable"],
            "dimensionality_status": row["dimensionality_status"],
            "selection_reason": reason,
            "signal_level": signal.level,
            "signal_types": "|".join(signal.signal_types),
            "signal_rule_version": signal.rule_version,
            "manual_review_required": signal.requires_manual_review,
            "budget_used": round_number,
            "budget_total": config["query_budget"],
        })
    hits = sum(row["target_hit"] for row in logs)
    result = {
        "policy": policy,
        "queries": len(logs),
        "d2_hits": sum(row["signal_level"] == "D2" for row in logs),
        "target_hits": hits,
        "hit_rate": round(hits / max(1, len(logs)), 4),
        "mean_absolute_error_ev": round(sum(row["absolute_error_ev"] for row in logs) / max(1, len(logs)), 4),
        "queried_material_ids": [row["material_id"] for row in logs],
        "unqueried_material_ids": [rows[i]["material_id"] for i in pool],
    }
    return result, logs, pool


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audited_rows = load_rows(config)
    dataset_rows = [{key: value for key, value in row.items() if key != "feature_vector"} for row in audited_rows]
    write_csv(DATASET_OUTPUT, dataset_rows)
    rows = [row for row in audited_rows if row["stability_eligible"]]
    if len(rows) < config["eligible_passport_count_required"]:
        blocked = {
            "run_id": config["run_id"],
            "status": "blocked_insufficient_stable_candidates",
            "signed_audited_records": len(audited_rows),
            "stable_exploration_records": len(rows),
            "required_stable_records": config["eligible_passport_count_required"],
            "excluded_by_stability": [row["material_id"] for row in audited_rows if not row["stability_eligible"]],
            "result_statement": (
                "The preregistered loop was not run: the fixed Formation Energy plus auxiliary "
                "stability rule left fewer candidates than the configured minimum."
            ),
        }
        SUMMARY_OUTPUT.write_text(json.dumps(blocked, ensure_ascii=False, indent=2), encoding="utf-8")
        print(blocked["result_statement"], file=sys.stderr)
        return 1
    initial = farthest_point_initial_indices(rows, config["initial_samples"])
    results = []
    for policy in config["policies"]:
        result, logs, _ = run_policy(rows, initial, policy, config)
        results.append(result)
        write_csv(ROOT / "artifacts" / f"formal_exploration_log_{policy}.csv", logs)
    summary = {
        "run_id": config["run_id"],
        "source_database": config["source_database"],
        "database_version": config["database_version"],
        "eligible_records": len(rows),
        "feature_names": config["feature_names"],
        "initial_selection": config["initial_selection"],
        "initial_material_ids": [rows[i]["material_id"] for i in initial],
        "query_budget_per_policy": config["query_budget"],
        "target_band_gap_interval_ev": [config["target_band_gap_min_ev"], config["target_band_gap_max_ev"]],
        "strategy_results": results,
        "d3_assignable": False,
        "claim_limit": config["claim_limit"],
        "result_statement": (
            "The preregistered Materials Project 3+3+1 micro-loop ran end to end on seven stable "
            "MoS2 records. Results are descriptive and cannot establish general strategy superiority."
        ),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("policy        queries  D2  hit_rate  MAE(eV)  remaining")
    for item in results:
        print(
            f"{item['policy']:<13} {item['queries']:>7} {item['d2_hits']:>3} "
            f"{item['hit_rate']:>9.2%} {item['mean_absolute_error_ev']:>8.3f} "
            f"{','.join(item['unqueried_material_ids'])}"
        )
    print("Formal evidence written to artifacts/formal_closed_loop_summary.json and formal_exploration_log_*.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
