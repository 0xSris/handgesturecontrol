from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Iterable, Sequence, TypeVar

import numpy as np

from .one_euro_filter import DEFAULT_BETA, DEFAULT_MIN_CUTOFF, OneEuroLandmarkFilter

T = TypeVar("T")
Point = tuple[float, float, float]


@dataclass
class LandmarkSmoother:
    """One Euro landmark smoothing followed by a light EMA compatibility layer."""

    alpha: float = 0.45
    min_cutoff: float = DEFAULT_MIN_CUTOFF
    beta: float = DEFAULT_BETA
    _previous: list[Point] | None = None
    _one_euro: OneEuroLandmarkFilter | None = None

    def reset(self) -> None:
        self._previous = None
        if self._one_euro is not None:
            self._one_euro.reset()

    def update(self, landmarks: Sequence[Point], dt: float = 1.0 / 30.0) -> list[Point]:
        current = np.asarray(list(landmarks), dtype=float)
        if current.shape != (21, 3):
            return [tuple(point) for point in current.tolist()]

        if self._one_euro is None:
            self._one_euro = OneEuroLandmarkFilter(min_cutoff=self.min_cutoff, beta=self.beta)

        filtered = [tuple(point) for point in self._one_euro.update(current, dt).tolist()]
        if self._previous is None or len(self._previous) != len(filtered):
            self._previous = filtered
            return filtered

        alpha = min(max(self.alpha, 0.0), 1.0)
        smoothed = [
            (
                alpha * x + (1.0 - alpha) * px,
                alpha * y + (1.0 - alpha) * py,
                alpha * z + (1.0 - alpha) * pz,
            )
            for (x, y, z), (px, py, pz) in zip(filtered, self._previous)
        ]
        self._previous = smoothed
        return smoothed


class LabelSmoother:
    """Majority-vote smoothing to avoid flickering gesture labels."""

    def __init__(self, size: int = 7) -> None:
        self._labels: Deque[str] = deque(maxlen=max(1, size))

    def reset(self) -> None:
        self._labels.clear()

    def update(self, label: str) -> str:
        self._labels.append(label)
        return majority_vote(self._labels)


def majority_vote(values: Iterable[T]) -> T:
    counts = Counter(values)
    if not counts:
        raise ValueError("majority_vote requires at least one value")
    return counts.most_common(1)[0][0]
