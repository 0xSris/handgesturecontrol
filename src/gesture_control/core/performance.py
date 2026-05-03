from __future__ import annotations

import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Deque, Iterator

ROLLING_WINDOW = 30
STAGE_BUDGETS_MS = {
    "capture": 2.0,
    "mediapipe": 15.0,
    "smoothing": 3.0,
    "classification": 3.0,
    "action": 2.0,
    "websocket": 1.0,
}


@dataclass
class PerformanceMonitor:
    budgets_ms: dict[str, float] = field(default_factory=lambda: dict(STAGE_BUDGETS_MS))
    _samples: dict[str, Deque[float]] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=ROLLING_WINDOW)))

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record(name, (time.perf_counter() - start) * 1000.0)

    def record(self, name: str, elapsed_ms: float) -> None:
        self._samples[name].append(elapsed_ms)

    def averages(self) -> dict[str, float]:
        return {
            name: sum(values) / len(values)
            for name, values in self._samples.items()
            if values
        }

    def warnings(self) -> list[str]:
        warnings: list[str] = []
        for name, average in self.averages().items():
            budget = self.budgets_ms.get(name)
            if budget is not None and average > budget:
                warnings.append(f"{name} average {average:.2f}ms exceeds {budget:.2f}ms")
        return warnings
