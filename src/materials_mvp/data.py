from __future__ import annotations

import csv
import math
import random
from pathlib import Path

FEATURES = (
    "atomic_number_mean",
    "electronegativity_mean",
    "atomic_radius_mean",
    "layer_thickness",
    "symmetry_index",
)


def generate_sample_data(path: Path, n: int = 160, seed: int = 2026) -> None:
    """Create deterministic synthetic data for software validation only."""
    rng = random.Random(seed)
    prototypes = ["1H", "1T", "Td", "hex", "ortho"]
    elements = ["Mo", "W", "Ti", "V", "Sn", "Ga", "In", "Bi"]
    anions = ["S2", "Se2", "Te2", "O2", "N2"]
    rows = []
    for i in range(n):
        proto_i = i % len(prototypes)
        z = rng.uniform(18, 72)
        en = rng.uniform(1.35, 2.65)
        radius = rng.uniform(0.95, 1.75)
        thickness = rng.uniform(2.6, 7.8)
        symmetry = rng.uniform(0.05, 1.0)
        formation = -0.72 + 0.006 * (z - 40) + 0.16 * (radius - 1.3) + rng.gauss(0, 0.14)
        energy_above_hull = max(0.0, 0.18 + 0.28 * formation + rng.gauss(0, 0.035))
        is_stable = energy_above_hull <= 0.02
        if i % 13 == 0:
            dimensionality_status = "uncertain_2d"
        elif i % 17 == 0:
            dimensionality_status = "non_2d"
        else:
            dimensionality_status = "confirmed_2d"
        nonlinear = 0.35 * math.sin(z / 8.0) + 0.22 * (proto_i == 0) - 0.18 * (proto_i == 1)
        band_gap = 2.35 - 0.018 * z + 0.72 * (en - 1.8) - 0.12 * (thickness - 4.5) + 0.3 * symmetry + nonlinear + rng.gauss(0, 0.18)
        band_gap = max(0.0, min(4.5, band_gap))
        rows.append({
            "material_id": f"demo-2d-{i:04d}",
            "formula": elements[i % len(elements)] + anions[(i * 3) % len(anions)],
            "prototype": prototypes[proto_i],
            "atomic_number_mean": f"{z:.5f}",
            "electronegativity_mean": f"{en:.5f}",
            "atomic_radius_mean": f"{radius:.5f}",
            "layer_thickness": f"{thickness:.5f}",
            "symmetry_index": f"{symmetry:.5f}",
            "formation_energy_ev_atom": f"{formation:.5f}",
            "energy_above_hull_ev_atom": f"{energy_above_hull:.5f}",
            "is_stable": str(is_stable),
            "dimensionality_status": dimensionality_status,
            "band_gap_ev": f"{band_gap:.5f}",
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_materials(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for name in FEATURES + ("formation_energy_ev_atom", "energy_above_hull_ev_atom", "band_gap_ev"):
            row[name] = float(row[name])
        row["is_stable"] = row["is_stable"].lower() == "true"
    return rows
