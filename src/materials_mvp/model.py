from __future__ import annotations

import math
import random


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    aug = [matrix[i][:] + [vector[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        denom = aug[col][col]
        if abs(denom) < 1e-12:
            denom = 1e-12
        aug[col] = [v / denom for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(n + 1)]
    return [aug[i][-1] for i in range(n)]


class BootstrapRidge:
    def __init__(self, alpha: float = 0.1, n_models: int = 12, seed: int = 42):
        self.alpha = alpha
        self.n_models = n_models
        self.seed = seed
        self.models: list[tuple[list[float], list[float], list[float]]] = []

    @staticmethod
    def _standardize(x: list[list[float]]) -> tuple[list[float], list[float]]:
        p = len(x[0])
        means = [sum(row[j] for row in x) / len(x) for j in range(p)]
        scales = []
        for j in range(p):
            variance = sum((row[j] - means[j]) ** 2 for row in x) / max(1, len(x) - 1)
            scales.append(max(math.sqrt(variance), 1e-8))
        return means, scales

    def _fit_one(self, x: list[list[float]], y: list[float]) -> tuple[list[float], list[float], list[float]]:
        means, scales = self._standardize(x)
        design = [[1.0] + [(v - means[j]) / scales[j] for j, v in enumerate(row)] for row in x]
        p = len(design[0])
        gram = [[sum(row[a] * row[b] for row in design) for b in range(p)] for a in range(p)]
        for j in range(1, p):
            gram[j][j] += self.alpha
        rhs = [sum(row[j] * target for row, target in zip(design, y)) for j in range(p)]
        return _solve(gram, rhs), means, scales

    def fit(self, x: list[list[float]], y: list[float]) -> "BootstrapRidge":
        rng = random.Random(self.seed + len(x))
        self.models = []
        for _ in range(self.n_models):
            indices = [rng.randrange(len(x)) for _ in range(len(x))]
            self.models.append(self._fit_one([x[i] for i in indices], [y[i] for i in indices]))
        return self

    def predict_one(self, row: list[float]) -> tuple[float, float]:
        predictions = []
        for weights, means, scales in self.models:
            design = [1.0] + [(v - means[j]) / scales[j] for j, v in enumerate(row)]
            predictions.append(sum(a * b for a, b in zip(weights, design)))
        mean = sum(predictions) / len(predictions)
        variance = sum((v - mean) ** 2 for v in predictions) / max(1, len(predictions) - 1)
        return mean, math.sqrt(variance)

