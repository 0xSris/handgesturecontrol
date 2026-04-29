import json
from pathlib import Path

from gesture_control.calibration import CalibrationSession, percentile
from gesture_control.config import RuntimeConfig
from gesture_control.gestures import GestureResult


def gesture(pinch):
    return GestureResult(
        name="point",
        confidence=0.9,
        fingers_up=(False, True, False, False, False),
        pinch_distance=pinch,
        middle_pinch_distance=0.1,
        index_position=(0.5, 0.5),
        palm_position=(0.5, 0.5),
    )


def test_percentile_uses_sorted_values():
    assert percentile([0.4, 0.1, 0.2], 0.0) == 0.1
    assert percentile([0.4, 0.1, 0.2], 1.0) == 0.4


def test_calibration_saves_profile():
    output = Path("tmp/test_calibration_profile.json")
    output.parent.mkdir(exist_ok=True)
    if output.exists():
        output.unlink()

    session = CalibrationSession(str(output), target_samples=2)
    config = RuntimeConfig(cursor_sensitivity=1.8, shortcuts={"point": ("ctrl", "l")})

    session.update(gesture(0.03), config)
    session.update(gesture(0.04), config)
    session.update(gesture(0.20), config)
    status = session.update(gesture(0.24), config)

    assert status.complete is True
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["cursor_sensitivity"] == 1.8
    assert data["volume_min_pinch"] > 0
    assert data["volume_max_pinch"] > data["volume_min_pinch"]
    assert data["shortcuts"]["point"] == ["ctrl", "l"]
