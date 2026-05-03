from __future__ import annotations

from dataclasses import dataclass
from math import exp, pi

import numpy as np

DEFAULT_MIN_CUTOFF = 1.0  # Balanced jitter reduction for 30 FPS webcam input.
DEFAULT_BETA = 0.1  # Small velocity response boost without making landmarks jumpy.
DEFAULT_D_CUTOFF = 1.0  # Standard One Euro derivative cutoff from the original method.


def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2.0 * pi * cutoff)
    return 1.0 / (1.0 + tau / max(dt, 1e-6))


@dataclass
class LowPassFilter:
    value: float | None = None

    def apply(self, value: float, alpha: float) -> float:
        if self.value is None:
            self.value = value
            return value
        self.value = alpha * value + (1.0 - alpha) * self.value
        return self.value

    def reset(self) -> None:
        self.value = None


class OneEuroFilter:
    """One Euro filter for one scalar signal."""

    def __init__(
        self,
        min_cutoff: float = DEFAULT_MIN_CUTOFF,
        beta: float = DEFAULT_BETA,
        d_cutoff: float = DEFAULT_D_CUTOFF,
    ) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x = LowPassFilter()
        self._dx = LowPassFilter()
        self._last_raw: float | None = None
        self.last_derivative = 0.0
        self.last_cutoff = min_cutoff

    def reset(self) -> None:
        self._x.reset()
        self._dx.reset()
        self._last_raw = None
        self.last_derivative = 0.0
        self.last_cutoff = self.min_cutoff

    def apply(self, value: float, dt: float) -> float:
        derivative = 0.0 if self._last_raw is None else (value - self._last_raw) / max(dt, 1e-6)
        self._last_raw = value
        filtered_derivative = self._dx.apply(derivative, _alpha(self.d_cutoff, dt))
        cutoff = self.min_cutoff + self.beta * abs(filtered_derivative)
        self.last_derivative = filtered_derivative
        self.last_cutoff = cutoff
        return self._x.apply(value, _alpha(cutoff, dt))


class OneEuroLandmarkFilter:
    """Applies independent One Euro filters to 21 MediaPipe landmarks."""

    def __init__(
        self,
        landmark_count: int = 21,
        min_cutoff: float = DEFAULT_MIN_CUTOFF,
        beta: float = DEFAULT_BETA,
    ) -> None:
        self.landmark_count = landmark_count
        self.min_cutoff = min_cutoff
        self.beta = beta
        self._filters = [
            [OneEuroFilter(min_cutoff=min_cutoff, beta=beta) for _ in range(3)]
            for _ in range(landmark_count)
        ]
        self.last_values: np.ndarray | None = None

    def reset(self) -> None:
        for row in self._filters:
            for axis_filter in row:
                axis_filter.reset()
        self.last_values = None

    def update(self, landmarks: np.ndarray, dt: float) -> np.ndarray:
        if landmarks.shape != (self.landmark_count, 3):
            raise ValueError(f"Expected landmark array shape {(self.landmark_count, 3)}, got {landmarks.shape}")
        output = np.empty_like(landmarks, dtype=float)
        for index in range(self.landmark_count):
            for axis in range(3):
                output[index, axis] = self._filters[index][axis].apply(float(landmarks[index, axis]), dt)
        self.last_values = output
        return output
