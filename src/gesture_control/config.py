from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeConfig:
    camera_index: int = 0
    frame_width: int = 960
    frame_height: int = 540
    display_width: int = 960
    display_height: int = 540
    ui_scale: float = 0.62
    mirror: bool = True
    draw_landmarks: bool = True
    detection_confidence: float = 0.65
    tracking_confidence: float = 0.65
    max_num_hands: int = 1
    smoothing_alpha: float = 0.45
    smoothing: dict[str, Any] = field(
        default_factory=lambda: {
            "min_cutoff": 1.0,
            "beta": 0.1,
            "cursor_alpha": 0.72,
            "dead_zone_radius": 0.004,
            "base_speed": 2.1,
            "acceleration_exponent": 1.0,
        }
    )
    gesture_debounce: dict[str, int] = field(
        default_factory=lambda: {
            "point": 1,
            "peace": 1,
            "pinch": 1,
            "thumbs_up": 1,
            "three_fingers": 1,
            "open_palm": 1,
            "fist": 1,
        }
    )
    gesture_history: int = 7
    action_confidence: float = 0.45
    enable_actions: bool = False
    cursor_sensitivity: float = 1.35
    cursor_dead_zone: float = 0.006
    action_cooldown_seconds: float = 0.65
    drag_hold_seconds: float = 0.45
    pinch: dict[str, Any] = field(
        default_factory=lambda: {
            "enter_threshold": 0.085,
            "exit_threshold": 0.12,
            "min_click_hold_seconds": 0.08,
            "click_cooldown_seconds": 0.30,
            "drag_hold_seconds": 0.60,
        }
    )
    pinch_enter_threshold: float = 0.085
    pinch_exit_threshold: float = 0.12
    min_click_hold_seconds: float = 0.08
    click_cooldown_seconds: float = 0.30
    lock_hold_seconds: float = 0.8
    volume_min_pinch: float = 0.035
    volume_max_pinch: float = 0.24
    pinch_threshold: float = 0.075
    middle_pinch_threshold: float = 0.075
    calibration_output: str | None = None
    calibration_samples: int = 60
    record_output: str | None = None
    record_fps: float = 20.0
    snapshot_dir: str = "captures"
    event_log: str | None = None
    share_path: str | None = None
    share_port: int = 8765
    share_url: str | None = None
    browser_home_url: str = "https://www.google.com"
    show_debug: bool = False
    enable_extension: bool = False
    extension: dict[str, Any] = field(default_factory=lambda: {"host": "127.0.0.1", "port": 7433, "broadcast_interval_ms": 100})
    list_cameras: bool = False
    camera_probe_limit: int = 5
    shortcuts: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "point": ("alt", "tab"),
            "peace": ("playpause",),
            "pinch": ("win", "shift", "s"),
        }
    )


def load_profile(path: str | None) -> dict[str, Any]:
    if not path:
        return {}

    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Gesture profile not found: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Gesture profile must be a JSON object.")

    if "shortcuts" in data:
        shortcuts = data["shortcuts"]
        if not isinstance(shortcuts, dict):
            raise ValueError("Profile 'shortcuts' must be a JSON object.")
        data["shortcuts"] = {
            str(gesture): tuple(str(key) for key in keys)
            for gesture, keys in shortcuts.items()
            if isinstance(keys, list)
        }

    if "smoothing" in data:
        smoothing = data["smoothing"]
        if not isinstance(smoothing, dict):
            raise ValueError("Profile 'smoothing' must be a JSON object.")
        data["smoothing"] = smoothing
        if "cursor_alpha" in smoothing:
            data["smoothing_alpha"] = float(smoothing["cursor_alpha"])
        if "dead_zone_radius" in smoothing:
            data["cursor_dead_zone"] = float(smoothing["dead_zone_radius"])
        if "base_speed" in smoothing:
            data["cursor_sensitivity"] = float(smoothing["base_speed"])

    if "pinch" in data:
        pinch = data["pinch"]
        if not isinstance(pinch, dict):
            raise ValueError("Profile 'pinch' must be a JSON object.")
        mapping = {
            "enter_threshold": "pinch_enter_threshold",
            "exit_threshold": "pinch_exit_threshold",
            "min_click_hold_seconds": "min_click_hold_seconds",
            "click_cooldown_seconds": "click_cooldown_seconds",
            "drag_hold_seconds": "drag_hold_seconds",
        }
        for source, target in mapping.items():
            if source in pinch:
                data[target] = float(pinch[source])

    if "gesture_debounce" in data:
        debounce = data["gesture_debounce"]
        if not isinstance(debounce, dict):
            raise ValueError("Profile 'gesture_debounce' must be a JSON object.")
        data["gesture_debounce"] = {str(key): int(value) for key, value in debounce.items()}

    if "extension" in data and not isinstance(data["extension"], dict):
        raise ValueError("Profile 'extension' must be a JSON object.")

    return data
