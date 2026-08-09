from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from .data import FEATURES
from .model import BootstrapRidge
from .signal import classify_queried_candidate


class ExplorationEnvironment:
    def __init__(self, rows: list[dict], config: dict, policy: str):
        self.rows = rows
        self.config = config
        self.policy = policy
        rng = random.Random(config["seed"])
        stable = [
            i for i, r in enumerate(rows)
            if r["dimensionality_status"] == config["dimensionality_training_status"]
            and self._passes_stability(r)
        ]
        rng.shuffle(stable)
        self.known = stable[: config["initial_samples"]]
        self.pool = stable[config["initial_samples"] :]
        self.budget_used = 0
        self.logs: list[dict] = []
        self.initial_model = self._fit_model()

    def _passes_stability(self, row: dict) -> bool:
        primary = row["formation_energy_ev_atom"] <= self.config["stability_max_formation_energy_ev_atom"]
        hull_support = row["energy_above_hull_ev_atom"] <= self.config["stability_max_energy_above_hull_ev_atom"]
        return primary and (hull_support or row["is_stable"])

    def _x(self, index: int) -> list[float]:
        return [self.rows[index][name] for name in FEATURES]

    def _fit_model(self) -> BootstrapRidge:
        return BootstrapRidge(
            alpha=self.config["ridge_alpha"],
            n_models=self.config["bootstrap_models"],
            seed=self.config["seed"],
        ).fit([self._x(i) for i in self.known], [self.rows[i]["band_gap_ev"] for i in self.known])

    def _target_score(self, prediction: float) -> float:
        low, high = self.config["target_band_gap_min_ev"], self.config["target_band_gap_max_ev"]
        if low <= prediction <= high:
            return 1.0
        return 1.0 / (1.0 + min(abs(prediction - low), abs(prediction - high)))

    def select(self, model: BootstrapRidge, rng: random.Random) -> tuple[int, float, float, str]:
        candidates = [(i, *model.predict_one(self._x(i))) for i in self.pool]
        if self.policy == "random":
            i, pred, unc = rng.choice(candidates)
            return i, pred, unc, "uniform random stable candidate"
        if self.policy == "static_topn":
            i, pred, unc = max(candidates, key=lambda item: self._target_score(item[1]))
            return i, pred, unc, "highest target score from frozen initial model"
        max_unc = max(item[2] for item in candidates) or 1.0
        weight = self.config["uncertainty_weight"]
        i, pred, unc = max(candidates, key=lambda item: (1 - weight) * self._target_score(item[1]) + weight * item[2] / max_unc)
        return i, pred, unc, "target score plus uncertainty; model retrained after feedback"

    def run(self) -> dict:
        rng = random.Random(self.config["seed"] + {"random": 1, "static_topn": 2, "iterative": 3}[self.policy])
        frozen = self.initial_model
        while self.pool and self.budget_used < self.config["query_budget"]:
            model = frozen if self.policy == "static_topn" else self._fit_model()
            index, prediction, uncertainty, reason = self.select(model, rng)
            row = self.rows[index]
            self.pool.remove(index)
            self.known.append(index)
            self.budget_used += 1
            hit = self.config["target_band_gap_min_ev"] <= row["band_gap_ev"] <= self.config["target_band_gap_max_ev"]
            signal = classify_queried_candidate(
                row, self.config, prediction, uncertainty, self.budget_used
            )
            self.logs.append({
                "round": self.budget_used,
                "policy": self.policy,
                "material_id": row["material_id"],
                "formula": row["formula"],
                "predicted_band_gap_ev": round(prediction, 5),
                "uncertainty_ev": round(uncertainty, 5),
                "true_band_gap_ev": row["band_gap_ev"],
                "formation_energy_ev_atom": row["formation_energy_ev_atom"],
                "energy_above_hull_ev_atom": row["energy_above_hull_ev_atom"],
                "is_stable_mp_flag": row["is_stable"],
                "dimensionality_status": row["dimensionality_status"],
                "stable": self._passes_stability(row),
                "target_hit": hit,
                "exploration_status_query_state": "queried",
                "exploration_status_training_eligible": True,
                "exploration_status_discovery_level": signal.level,
                "signal_types": "|".join(signal.signal_types),
                "signal_rule_version": signal.rule_version,
                "exploration_status_manual_review_required": signal.requires_manual_review,
                "exploration_status_budget_position": self.budget_used,
                "absolute_error_ev": round(abs(prediction - row["band_gap_ev"]), 5),
                "selection_reason": reason,
                "budget_used": self.budget_used,
                "budget_total": self.config["query_budget"],
            })
        hits = sum(1 for item in self.logs if item["target_hit"])
        return {
            "policy": self.policy,
            "queries": self.budget_used,
            "target_hits": hits,
            "hit_rate": round(hits / max(1, self.budget_used), 4),
            "mean_absolute_error_ev": round(sum(item["absolute_error_ev"] for item in self.logs) / max(1, len(self.logs)), 4),
            "all_selected_stable": all(item["stable"] for item in self.logs),
        }

    def save_log(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.logs[0]))
            writer.writeheader()
            writer.writerows(self.logs)


def build_dimensionality_audit(rows: list[dict], config: dict) -> tuple[list[dict], dict]:
    confirmed = [r for r in rows if r["dimensionality_status"] == config["dimensionality_training_status"]]
    mean_gap = sum(r["band_gap_ev"] for r in confirmed) / max(1, len(confirmed))
    excluded = []
    for row in rows:
        if row["dimensionality_status"] == config["dimensionality_training_status"]:
            continue
        excluded.append({
            "material_id": row["material_id"],
            "formula": row["formula"],
            "dimensionality_status": row["dimensionality_status"],
            "training_eligible": False,
            "manual_review_required": row["dimensionality_status"] == "uncertain_2d",
            "band_gap_ev": row["band_gap_ev"],
            "band_gap_deviation_from_confirmed_mean_ev": round(row["band_gap_ev"] - mean_gap, 5),
            "formation_energy_ev_atom": row["formation_energy_ev_atom"],
            "energy_above_hull_ev_atom": row["energy_above_hull_ev_atom"],
            "is_stable_mp_flag": row["is_stable"],
            "exclusion_reason": "awaiting manual 2D review" if row["dimensionality_status"] == "uncertain_2d" else "classified as non-2D",
        })
    summary = {
        "confirmed_2d_count": len(confirmed),
        "uncertain_2d_count": sum(r["dimensionality_status"] == "uncertain_2d" for r in rows),
        "non_2d_count": sum(r["dimensionality_status"] == "non_2d" for r in rows),
        "excluded_from_training_count": len(excluded),
        "uncertain_policy": "audit and include in deviation statistics; exclude from training until manual confirmation",
    }
    return excluded, summary


def save_audit(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_summary(summary: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
