from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlretrieve

from .config import RuntimeConfig
from .smoothing import LandmarkSmoother

Point = tuple[float, float, float]
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"


@dataclass(frozen=True)
class TrackedHand:
    landmarks: list[Point]
    handedness: str
    score: float
    raw_landmarks: Any


class HandTracker:
    def __init__(self, config: RuntimeConfig) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core.base_options import BaseOptions
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe is required for hand tracking. Install dependencies with "
                "`pip install -r requirements.txt`."
            ) from exc

        self._mp = mp
        self._vision = vision
        self._model_path = ensure_hand_landmarker_model()
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.max_num_hands,
            min_hand_detection_confidence=config.detection_confidence,
            min_hand_presence_confidence=config.detection_confidence,
            min_tracking_confidence=config.tracking_confidence,
        )
        self._hands = vision.HandLandmarker.create_from_options(options)
        self._smoother = LandmarkSmoother(config.smoothing_alpha)
        self._timestamp_ms = 0

    @property
    def connections(self) -> Any:
        return self._vision.HandLandmarksConnections.HAND_CONNECTIONS

    def close(self) -> None:
        self._hands.close()

    def process_rgb(self, rgb_frame: Any) -> TrackedHand | None:
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
        self._timestamp_ms += 1
        result = self._hands.detect_for_video(image, self._timestamp_ms)
        if not result.hand_landmarks:
            self._smoother.reset()
            return None

        hand_landmarks = result.hand_landmarks[0]
        handedness = "Right"
        score = 0.0
        if result.handedness:
            classification = result.handedness[0][0]
            handedness = classification.category_name
            score = classification.score

        points = [
            (landmark.x, landmark.y, landmark.z)
            for landmark in hand_landmarks
        ]
        return TrackedHand(
            landmarks=self._smoother.update(points),
            handedness=handedness,
            score=score,
            raw_landmarks=hand_landmarks,
        )


def ensure_hand_landmarker_model() -> Path:
    if MODEL_PATH.exists():
        return MODEL_PATH

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        urlretrieve(MODEL_URL, MODEL_PATH)
    except (OSError, URLError) as exc:
        raise RuntimeError(
            "MediaPipe Tasks requires the hand_landmarker.task model. "
            f"Could not download it automatically from {MODEL_URL}. "
            f"Download it manually and save it to {MODEL_PATH}."
        ) from exc

    return MODEL_PATH
