from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RecordingStatus:
    active: bool
    output_path: str | None = None
    frames_written: int = 0


class RecordingSession:
    def __init__(self, output_path: str | None, fps: float = 20.0) -> None:
        self.output_path = output_path
        self.fps = max(fps, 1.0)
        self._writer: Any = None
        self._frames_written = 0

    @property
    def status(self) -> RecordingStatus:
        return RecordingStatus(
            active=self.output_path is not None,
            output_path=self.output_path,
            frames_written=self._frames_written,
        )

    def write(self, cv2: Any, frame: Any) -> None:
        if self.output_path is None:
            return

        if self._writer is None:
            height, width = frame.shape[:2]
            path = Path(self.output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self._writer = cv2.VideoWriter(str(path), fourcc, self.fps, (width, height))
            if not self._writer.isOpened():
                raise RuntimeError(f"Could not open video writer for {path}.")

        self._writer.write(frame)
        self._frames_written += 1

    def close(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None


def save_snapshot(cv2: Any, frame: Any, directory: str) -> Path:
    path = next_snapshot_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise RuntimeError(f"Could not write snapshot to {path}.")
    return path


def next_snapshot_path(directory: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return Path(directory) / f"gesture_{stamp}.png"


def list_available_cameras(cv2: Any, limit: int = 5) -> list[int]:
    cameras = []
    for index in range(max(limit, 0)):
        capture = cv2.VideoCapture(index)
        try:
            if capture.isOpened():
                cameras.append(index)
        finally:
            capture.release()
    return cameras


def resolve_camera_index(cv2: Any, requested_index: int, probe_limit: int = 5) -> int:
    if requested_index >= 0:
        return requested_index

    cameras = list_available_cameras(cv2, probe_limit)
    if not cameras:
        raise RuntimeError(f"No camera found while probing indexes 0-{max(probe_limit - 1, 0)}.")
    return cameras[0]
