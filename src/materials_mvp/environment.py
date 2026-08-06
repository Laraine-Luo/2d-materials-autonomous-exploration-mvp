from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from .data import FEATURES
from .model import BootstrapRidge


class ExplorationEnvironment:
    def __init__(self, rows: list[dict], config: dict, policy: str):
        self.rows = rows
        self.config = config
        self.policy = policy
        rng = random.Random(config["seed"])
        stable = [i for i, r in enumerate(rows) if r["formation_energy_ev_atom"] <= config["stability_max_formation_energy_ev_atom"]]
        rng.shuffle(stable)
        self.known = stable[: config["initial_samples"]]
        self.pool = stable[config["initial_samples"] :]
        self.budget_used = 0
        self.logs: list[dict] = []
        self.initial_model = self._fit_model()

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
            self.logs.append({
                "round": self.budget_used,
                "policy": self.policy,
                "material_id": row["material_id"],
                "formula": row["formula"],
                "predicted_band_gap_ev": round(prediction, 5),
                "uncertainty_ev": round(uncertainty, 5),
                "true_band_gap_ev": row["band_gap_ev"],
                "formation_energy_ev_atom": row["formation_energy_ev_atom"],
                "stable": True,
                "target_hit": hit,
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


def save_summary(summary: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

