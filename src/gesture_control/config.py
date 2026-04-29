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
    gesture_history: int = 7
    action_confidence: float = 0.45
    enable_actions: bool = False
    cursor_sensitivity: float = 1.35
    cursor_dead_zone: float = 0.006
    action_cooldown_seconds: float = 0.65
    drag_hold_seconds: float = 0.45
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

    return data
