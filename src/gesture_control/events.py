from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .actions import ActionStatus


@dataclass(frozen=True)
class GestureEvent:
    timestamp: str
    gesture: str
    action: str
    mode: str
    active: bool


class EventLogger:
    def __init__(self, output_path: str | None) -> None:
        self.output_path = output_path
        self._file = None
        self._writer = None
        self._last_action = ""

    def log_if_changed(self, gesture: str, status: ActionStatus) -> None:
        if self.output_path is None:
            return
        if status.last_action == self._last_action or status.last_action in {"move cursor", "preview"}:
            return

        self._last_action = status.last_action
        self._ensure_open()
        self._writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "gesture": gesture,
                "action": status.last_action,
                "mode": status.mode.value,
                "active": status.active,
            }
        )
        self._file.flush()

    def log_warning(self, message: str) -> None:
        if self.output_path is None:
            return
        self._ensure_open()
        self._writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "gesture": "performance",
                "action": f"WARNING: {message}",
                "mode": "system",
                "active": False,
            }
        )
        self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None

    def _ensure_open(self) -> None:
        if self._writer is not None:
            return
        path = Path(self.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=["timestamp", "gesture", "action", "mode", "active"])
        self._writer.writeheader()
