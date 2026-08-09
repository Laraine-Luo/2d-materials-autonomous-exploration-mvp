"""Pre-registered discovery-signal rules for the MVP.

This module classifies evidence. It does not train models, choose candidates,
change dimensionality review status, or claim experimental/new-material discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

SIGNAL_RULE_VERSION = "0.2.0"


@dataclass(frozen=True)
class SignalEvent:
    rule_version: str
    level: str
    signal_types: tuple[str, ...]
    material_id: str
    round: int
    rationale: tuple[str, ...]
    requires_manual_review: bool

    def to_dict(self) -> dict:
        result = asdict(self)
        result["signal_types"] = list(self.signal_types)
        result["rationale"] = list(self.rationale)
        return result


def target_hit(band_gap_ev: float, config: dict) -> bool:
    return config["target_band_gap_min_ev"] <= band_gap_ev <= config["target_band_gap_max_ev"]


def stability_pass(row: dict, config: dict) -> bool:
    primary = row["formation_energy_ev_atom"] <= config["stability_max_formation_energy_ev_atom"]
    auxiliary = (
        row["energy_above_hull_ev_atom"] <= config["stability_max_energy_above_hull_ev_atom"]
        or row["is_stable"]
    )
    return primary and auxiliary


def high_confidence_anomaly(prediction_ev: float, truth_ev: float, uncertainty_ev: float) -> bool:
    return abs(prediction_ev - truth_ev) > max(0.6, 2.0 * uncertainty_ev)


def classify_queried_candidate(row: dict, config: dict, prediction_ev: float, uncertainty_ev: float, round_number: int) -> SignalEvent:
    """Classify one post-query record as D0, D1, or D2 plus anomaly flags.

    D3 requires repeated-run/held-out evidence and D4 requires external
    validation; neither can be assigned by this single-record function.
    """
    types: list[str] = []
    reasons: list[str] = ["query-feedback event recorded"]
    level = "D0"
    hit = target_hit(row["band_gap_ev"], config)
    if hit:
        level = "D1"
        types.append("target_hit")
        reasons.append("database band gap is inside the pre-registered interval")

    audited = row["dimensionality_status"] == config["dimensionality_training_status"]
    stable = stability_pass(row, config)
    traceable = bool(row.get("material_id"))
    if hit and audited and stable and traceable:
        level = "D2"
        types.append("audited_candidate_signal")
        reasons.append("identity, dimensionality and MVP stability checks passed")

    if high_confidence_anomaly(prediction_ev, row["band_gap_ev"], uncertainty_ev):
        types.append("high_confidence_model_anomaly")
        reasons.append("prediction error exceeds max(0.6 eV, 2×uncertainty)")

    if not types:
        types.append("technical_event_only")
    return SignalEvent(
        rule_version=SIGNAL_RULE_VERSION,
        level=level,
        signal_types=tuple(types),
        material_id=row["material_id"],
        round=round_number,
        rationale=tuple(reasons),
        requires_manual_review=("high_confidence_model_anomaly" in types or not audited),
    )


def assess_strategy_signal(iterative_hits: list[int], random_hits: list[int], static_hits: list[int], minimum_seeds: int = 20, relative_margin: float = 0.10) -> dict:
    """Check the numerical D3 gate; paired confidence analysis remains required."""
    if not (len(iterative_hits) == len(random_hits) == len(static_hits)):
        raise ValueError("All strategies must use identical seed counts")
    means = {
        "iterative": sum(iterative_hits) / max(1, len(iterative_hits)),
        "random": sum(random_hits) / max(1, len(random_hits)),
        "static_topn": sum(static_hits) / max(1, len(static_hits)),
    }
    margin_pass = (
        len(iterative_hits) >= minimum_seeds
        and means["iterative"] >= (1 + relative_margin) * means["random"]
        and means["iterative"] >= (1 + relative_margin) * means["static_topn"]
    )
    return {
        "seed_count": len(iterative_hits),
        "mean_d2_hits": means,
        "numerical_margin_pass": margin_pass,
        "d3_assignable": False,
        "missing_requirement": "paired 95% confidence interval excluding zero",
    }


def problem_revision_flags(summary: dict) -> list[str]:
    flags = []
    total = summary.get("total_records", 0)
    uncertain = summary.get("uncertain_2d_count", 0)
    if total and uncertain / total > 0.20:
        flags.append("more_than_20_percent_dimensionality_uncertain")
    if summary.get("random_hit_rate", 0) >= 0.50:
        flags.append("random_baseline_hit_rate_too_high")
    if summary.get("stability_conflict_rate", 0) >= 0.20:
        flags.append("stability_signals_frequently_conflict")
    return flags
