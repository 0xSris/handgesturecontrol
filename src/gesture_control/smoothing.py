from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Iterable, Sequence, TypeVar

T = TypeVar("T")
Point = tuple[float, float, float]


@dataclass
class LandmarkSmoother:
    """Exponential moving average for normalized hand landmarks."""

    alpha: float = 0.45
    _previous: list[Point] | None = None

    def reset(self) -> None:
        self._previous = None

    def update(self, landmarks: Sequence[Point]) -> list[Point]:
        current = list(landmarks)
        if self._previous is None or len(self._previous) != len(current):
            self._previous = current
            return current

        alpha = min(max(self.alpha, 0.0), 1.0)
        smoothed = [
            (
                alpha * x + (1.0 - alpha) * px,
                alpha * y + (1.0 - alpha) * py,
                alpha * z + (1.0 - alpha) * pz,
            )
            for (x, y, z), (px, py, pz) in zip(current, self._previous)
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
