from gesture_control.core.pinch_detector import PinchConfig, PinchDetector, PinchPhase


def test_pinch_click_fires_only_on_release_after_minimum_hold():
    detector = PinchDetector(PinchConfig(enter_threshold=0.04, exit_threshold=0.07, min_click_hold_seconds=0.08))

    assert detector.update(0.03, 1.0).click_release is False
    assert detector.update(0.05, 1.04).click_release is False
    assert detector.update(0.08, 1.10).click_release is True


def test_short_pinch_is_discarded():
    detector = PinchDetector(PinchConfig(enter_threshold=0.04, exit_threshold=0.07, min_click_hold_seconds=0.08))

    detector.update(0.03, 1.0)
    event = detector.update(0.08, 1.03)

    assert event.click_release is False


def test_drag_never_also_clicks():
    detector = PinchDetector(PinchConfig(enter_threshold=0.04, exit_threshold=0.07, drag_hold_seconds=0.6))

    detector.update(0.03, 1.0)
    drag_start = detector.update(0.03, 1.7)
    release = detector.update(0.08, 1.8)

    assert drag_start.drag_start is True
    assert release.drag_release is True
    assert release.click_release is False
    assert release.phase == PinchPhase.OPEN
