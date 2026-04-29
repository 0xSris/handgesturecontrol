from gesture_control.actions import ActionStatus, ControlMode
from gesture_control.events import EventLogger
from pathlib import Path


def test_event_logger_writes_changed_actions():
    output = Path("tmp/test_events.csv")
    output.parent.mkdir(exist_ok=True)
    if output.exists():
        output.unlink()
    logger = EventLogger(str(output))

    logger.log_if_changed(
        "peace",
        ActionStatus(True, True, ControlMode.MEDIA, "media play/pause"),
    )
    logger.log_if_changed(
        "peace",
        ActionStatus(True, True, ControlMode.MEDIA, "media play/pause"),
    )
    logger.log_if_changed(
        "point",
        ActionStatus(True, True, ControlMode.MEDIA, "media next"),
    )
    logger.close()

    rows = output.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == "timestamp,gesture,action,mode,active"
    assert len(rows) == 3
    assert "media play/pause" in rows[1]
    assert "media next" in rows[2]
