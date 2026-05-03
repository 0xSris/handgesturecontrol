from __future__ import annotations

from dataclasses import dataclass
from math import hypot

CURSOR_ALPHA = 0.3  # Smooths fingertip motion without making cursor unusably delayed.
DEAD_ZONE_RADIUS = 0.04  # Neutral hand radius where tiny tremor is ignored.
BASE_SPEED = 1.35  # Matches the original cursor sensitivity default.
ACCELERATION_EXPONENT = 1.5  # Precision at low velocity, range at high velocity.
EDGE_SLOW_ZONE = 0.05  # Last 5 percent of the screen gets slower for controllable edges.


@dataclass(frozen=True)
class CursorConfig:
    alpha: float = CURSOR_ALPHA
    dead_zone_radius: float = DEAD_ZONE_RADIUS
    base_speed: float = BASE_SPEED
    acceleration_exponent: float = ACCELERATION_EXPONENT
    neutral_position: tuple[float, float] = (0.5, 0.5)


class CursorEngine:
    def __init__(self, config: CursorConfig | None = None) -> None:
        self.config = config or CursorConfig()
        self._previous_hand: tuple[float, float] | None = None
        self._cursor: tuple[float, float] | None = None

    def reset(self) -> None:
        self._previous_hand = None
        self._cursor = None

    def update(self, index_position: tuple[float, float]) -> tuple[float, float]:
        raw_x, raw_y = index_position
        if self._cursor is None:
            self._cursor = (raw_x, raw_y)
            self._previous_hand = index_position
            return self._cursor

        neutral_x, neutral_y = self.config.neutral_position
        if hypot(raw_x - neutral_x, raw_y - neutral_y) < self.config.dead_zone_radius:
            self._previous_hand = index_position
            return self._cursor

        prev_x, prev_y = self._previous_hand if self._previous_hand is not None else index_position
        velocity = hypot(raw_x - prev_x, raw_y - prev_y)
        speed = self.config.base_speed * (velocity ** self.config.acceleration_exponent)
        speed = max(speed, 0.02)

        cursor_x, cursor_y = self._cursor
        target_x = 0.5 + (raw_x - 0.5) * self.config.base_speed
        target_y = 0.5 + (raw_y - 0.5) * self.config.base_speed
        alpha = min(max(self.config.alpha, 0.0), 1.0)
        next_x = cursor_x + alpha * speed * (target_x - cursor_x)
        next_y = cursor_y + alpha * speed * (target_y - cursor_y)

        next_x, next_y = self._apply_soft_edges(next_x, next_y, cursor_x, cursor_y)
        self._cursor = (min(max(next_x, 0.0), 1.0), min(max(next_y, 0.0), 1.0))
        self._previous_hand = index_position
        return self._cursor

    def _apply_soft_edges(self, x: float, y: float, old_x: float, old_y: float) -> tuple[float, float]:
        if x < EDGE_SLOW_ZONE or x > 1.0 - EDGE_SLOW_ZONE:
            x = old_x + 0.5 * (x - old_x)
        if y < EDGE_SLOW_ZONE or y > 1.0 - EDGE_SLOW_ZONE:
            y = old_y + 0.5 * (y - old_y)
        return x, y
