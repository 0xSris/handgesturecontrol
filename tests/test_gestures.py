from gesture_control.gestures import classify_gesture, fingers_are_up
from gesture_control.smoothing import LabelSmoother, majority_vote


def hand_with_states(thumb_open=False, index=False, middle=False, ring=False, pinky=False):
    points = [(0.5, 0.8, 0.0) for _ in range(21)]
    points[3] = (0.45, 0.65, 0.0)
    points[4] = (0.35 if thumb_open else 0.48, 0.65, 0.0)

    for tip, pip, is_up in ((8, 6, index), (12, 10, middle), (16, 14, ring), (20, 18, pinky)):
        points[pip] = (points[pip][0], 0.55, 0.0)
        points[tip] = (points[tip][0], 0.35 if is_up else 0.7, 0.0)
    return points


def test_finger_state_detection():
    landmarks = hand_with_states(thumb_open=True, index=True, middle=False, ring=False, pinky=True)
    assert fingers_are_up(landmarks, "Right") == (True, True, False, False, True)


def test_open_palm_classification():
    result = classify_gesture(hand_with_states(True, True, True, True, True), "Right")
    assert result.name == "open_palm"


def test_open_palm_classification_all_fingers_even_if_thumb_is_unclear():
    result = classify_gesture(hand_with_states(False, True, True, True, True), "Right")
    assert result.name == "open_palm"


def test_fist_classification():
    result = classify_gesture(hand_with_states(False, False, False, False, False), "Right")
    assert result.name == "fist"


def test_point_classification():
    result = classify_gesture(hand_with_states(False, True, False, False, False), "Right")
    assert result.name == "point"


def test_pinch_classification_when_index_tip_is_curled():
    landmarks = hand_with_states(True, False, False, False, False)
    landmarks[3] = (0.55, 0.65, 0.0)
    landmarks[4] = (0.5, 0.65, 0.0)
    landmarks[8] = (0.52, 0.65, 0.0)
    result = classify_gesture(landmarks, "Right")
    assert result.name == "pinch"


def test_middle_pinch_classification():
    landmarks = hand_with_states(False, True, True, False, False)
    landmarks[4] = (0.5, 0.35, 0.0)
    landmarks[8] = (0.7, 0.35, 0.0)
    landmarks[12] = (0.52, 0.35, 0.0)
    result = classify_gesture(landmarks, "Right")
    assert result.name == "middle_pinch"


def test_label_smoothing_majority_vote():
    smoother = LabelSmoother(size=5)
    for label in ("point", "point", "unknown", "point", "fist"):
        stable = smoother.update(label)
    assert stable == "point"
    assert majority_vote(["a", "b", "a"]) == "a"
