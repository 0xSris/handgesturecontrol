from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Sequence

Point = tuple[float, float, float]

WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

FINGER_TIPS = (INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
FINGER_PIPS = (6, 10, 14, 18)


@dataclass(frozen=True)
class GestureResult:
    name: str
    confidence: float
    fingers_up: tuple[bool, bool, bool, bool, bool]
    pinch_distance: float
    middle_pinch_distance: float
    index_position: tuple[float, float]
    palm_position: tuple[float, float]


def classify_gesture(
    landmarks: Sequence[Point],
    handedness: str = "Right",
    pinch_threshold: float = 0.075,
    middle_pinch_threshold: float = 0.075,
) -> GestureResult:
    if len(landmarks) < 21:
        return GestureResult("unknown", 0.0, (False, False, False, False, False), 1.0, 1.0, (0.5, 0.5), (0.5, 0.5))

    fingers = fingers_are_up(landmarks, handedness)
    pinch = distance_2d(landmarks[THUMB_TIP], landmarks[INDEX_TIP])
    middle_pinch = distance_2d(landmarks[THUMB_TIP], landmarks[MIDDLE_TIP])
    index_position = point_2d(landmarks[INDEX_TIP])
    palm_position = point_2d(landmarks[INDEX_MCP])
    extended = sum(fingers)
    index, middle, ring, pinky = fingers[1:]

    if pinch < pinch_threshold and (index or extended > 0):
        return GestureResult("pinch", confidence_from_distance(pinch, pinch_threshold), fingers, pinch, middle_pinch, index_position, palm_position)

    if middle_pinch < middle_pinch_threshold and middle:
        return GestureResult("middle_pinch", confidence_from_distance(middle_pinch, middle_pinch_threshold), fingers, pinch, middle_pinch, index_position, palm_position)

    if extended == 5 or (index and middle and ring and pinky):
        return GestureResult("open_palm", 0.96, fingers, pinch, middle_pinch, index_position, palm_position)

    if extended == 0:
        return GestureResult("fist", 0.95, fingers, pinch, middle_pinch, index_position, palm_position)

    if index and not middle and not ring and not pinky:
        return GestureResult("point", 0.92, fingers, pinch, middle_pinch, index_position, palm_position)

    if index and middle and not ring and not pinky:
        return GestureResult("peace", 0.9, fingers, pinch, middle_pinch, index_position, palm_position)

    if index and middle and ring and not pinky:
        return GestureResult("three_fingers", 0.86, fingers, pinch, middle_pinch, index_position, palm_position)

    return GestureResult("unknown", 0.35, fingers, pinch, middle_pinch, index_position, palm_position)


def fingers_are_up(landmarks: Sequence[Point], handedness: str = "Right") -> tuple[bool, bool, bool, bool, bool]:
    thumb_up = thumb_is_open(landmarks, handedness)
    other_fingers = tuple(
        landmarks[tip][1] < landmarks[pip][1]
        for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)
    )
    return (thumb_up, *other_fingers)


def thumb_is_open(landmarks: Sequence[Point], handedness: str) -> bool:
    thumb_tip_x = landmarks[THUMB_TIP][0]
    thumb_ip_x = landmarks[3][0]
    if handedness.lower() == "left":
        return thumb_tip_x > thumb_ip_x
    return thumb_tip_x < thumb_ip_x


def distance_2d(a: Point, b: Point) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def point_2d(point: Point) -> tuple[float, float]:
    return (point[0], point[1])


def confidence_from_distance(value: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - (value / threshold)))
