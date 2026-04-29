from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import RuntimeConfig
from .gestures import GestureResult


@dataclass(frozen=True)
class CalibrationStatus:
    active: bool
    complete: bool
    phase: str
    instruction: str
    progress: float
    output_path: str | None = None


@dataclass
class CalibrationSession:
    output_path: str
    target_samples: int = 60
    closed_samples: list[float] = field(default_factory=list)
    open_samples: list[float] = field(default_factory=list)
    saved: bool = False

    @property
    def status(self) -> CalibrationStatus:
        if self.saved:
            return CalibrationStatus(
                active=False,
                complete=True,
                phase="saved",
                instruction="Calibration profile saved",
                progress=1.0,
                output_path=self.output_path,
            )

        if len(self.closed_samples) < self.target_samples:
            return CalibrationStatus(
                active=True,
                complete=False,
                phase="closed",
                instruction="Touch thumb and index together",
                progress=len(self.closed_samples) / self.target_samples,
                output_path=self.output_path,
            )

        return CalibrationStatus(
            active=True,
            complete=False,
            phase="open",
            instruction="Spread thumb and index apart",
            progress=len(self.open_samples) / self.target_samples,
            output_path=self.output_path,
        )

    def update(self, gesture: GestureResult, base: RuntimeConfig | None = None) -> CalibrationStatus:
        if self.saved:
            return self.status

        if len(self.closed_samples) < self.target_samples:
            self.closed_samples.append(gesture.pinch_distance)
            return self.status

        if len(self.open_samples) < self.target_samples:
            self.open_samples.append(gesture.pinch_distance)

        if len(self.open_samples) >= self.target_samples:
            self.save(base)

        return self.status

    def profile_values(self, base: RuntimeConfig) -> dict[str, object]:
        closed = percentile(self.closed_samples, 0.2)
        opened = percentile(self.open_samples, 0.8)
        if opened <= closed:
            opened = closed + 0.12

        return {
            "cursor_sensitivity": base.cursor_sensitivity,
            "cursor_dead_zone": base.cursor_dead_zone,
            "action_cooldown_seconds": base.action_cooldown_seconds,
            "drag_hold_seconds": base.drag_hold_seconds,
            "volume_min_pinch": round(max(closed * 1.15, 0.01), 4),
            "volume_max_pinch": round(max(opened * 0.95, closed + 0.08), 4),
            "shortcuts": {key: list(value) for key, value in base.shortcuts.items()},
        }

    def save(self, base: RuntimeConfig | None = None) -> None:
        base_config = base or RuntimeConfig()
        path = Path(self.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self.profile_values(base_config), file, indent=2)
            file.write("\n")
        self.saved = True


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * min(max(ratio, 0.0), 1.0))
    return ordered[index]
