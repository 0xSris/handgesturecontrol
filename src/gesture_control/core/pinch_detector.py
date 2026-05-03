from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PINCH_ENTER_THRESHOLD = 0.04  # Empirical normalized thumb-index distance for intentional contact.
PINCH_EXIT_THRESHOLD = 0.07  # Wider release boundary prevents oscillation flicker.
MIN_CLICK_HOLD_SECONDS = 0.08  # Ignores accidental fingertip brushes.
CLICK_COOLDOWN_SECONDS = 0.30  # Prevents double-click bursts after one release.
DRAG_HOLD_SECONDS = 0.60  # Long enough to separate dragging from normal clicking.


class PinchPhase(str, Enum):
    OPEN = "open"
    PINCHED = "pinched"
    DRAGGING = "dragging"
    COOLDOWN = "cooldown"


@dataclass(frozen=True)
class PinchConfig:
    enter_threshold: float = PINCH_ENTER_THRESHOLD
    exit_threshold: float = PINCH_EXIT_THRESHOLD
    min_click_hold_seconds: float = MIN_CLICK_HOLD_SECONDS
    click_cooldown_seconds: float = CLICK_COOLDOWN_SECONDS
    drag_hold_seconds: float = DRAG_HOLD_SECONDS


@dataclass(frozen=True)
class PinchEvent:
    click_release: bool = False
    drag_start: bool = False
    drag_release: bool = False
    phase: PinchPhase = PinchPhase.OPEN


class PinchDetector:
    def __init__(self, config: PinchConfig | None = None) -> None:
        self.config = config or PinchConfig()
        self.phase = PinchPhase.OPEN
        self._pinch_started_at: float | None = None
        self._cooldown_until = 0.0

    def reset(self) -> PinchEvent:
        drag_release = self.phase == PinchPhase.DRAGGING
        self.phase = PinchPhase.OPEN
        self._pinch_started_at = None
        return PinchEvent(drag_release=drag_release, phase=self.phase)

    def update(self, distance: float, now: float) -> PinchEvent:
        if now < self._cooldown_until:
            self.phase = PinchPhase.COOLDOWN
            return PinchEvent(phase=self.phase)

        if self.phase == PinchPhase.COOLDOWN:
            self.phase = PinchPhase.OPEN

        if self.phase == PinchPhase.OPEN:
            if distance <= self.config.enter_threshold:
                self.phase = PinchPhase.PINCHED
                self._pinch_started_at = now
            return PinchEvent(phase=self.phase)

        started_at = self._pinch_started_at if self._pinch_started_at is not None else now
        held_for = now - started_at

        if self.phase == PinchPhase.PINCHED and held_for >= self.config.drag_hold_seconds:
            self.phase = PinchPhase.DRAGGING
            return PinchEvent(drag_start=True, phase=self.phase)

        if distance >= self.config.exit_threshold:
            if self.phase == PinchPhase.DRAGGING:
                self.phase = PinchPhase.OPEN
                self._pinch_started_at = None
                self._cooldown_until = now + self.config.click_cooldown_seconds
                return PinchEvent(drag_release=True, phase=self.phase)

            should_click = held_for >= self.config.min_click_hold_seconds
            self.phase = PinchPhase.OPEN
            self._pinch_started_at = None
            if should_click:
                self._cooldown_until = now + self.config.click_cooldown_seconds
            return PinchEvent(click_release=should_click, phase=self.phase)

        return PinchEvent(phase=self.phase)
