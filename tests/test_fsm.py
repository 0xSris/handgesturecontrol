from gesture_control.actions import ControlMode
from gesture_control.core.gesture_fsm import GestureFSM, GestureState


def test_locked_unlocks_only_after_stable_open_palm():
    fsm = GestureFSM(debounce_frames={"open_palm": 3}, default_frames=3)

    assert fsm.update("open_palm").action_allowed is False
    assert fsm.update("open_palm").action_allowed is False
    event = fsm.update("open_palm")

    assert event.state == GestureState.UNLOCKED
    assert event.action_allowed is True


def test_mode_cycle_only_when_unlocked():
    fsm = GestureFSM(debounce_frames={"three_fingers": 1, "open_palm": 1}, default_frames=1)

    locked_event = fsm.update("three_fingers")
    assert locked_event.cycle_mode is False

    fsm.update("open_palm")
    unlocked_event = fsm.update("three_fingers")

    assert unlocked_event.cycle_mode is True


def test_state_maps_to_current_mode_action_state():
    fsm = GestureFSM(debounce_frames={"open_palm": 1, "point": 1}, default_frames=1)
    fsm.update("open_palm")
    fsm.set_mode(ControlMode.MEDIA)

    event = fsm.update("point")

    assert event.state == GestureState.MEDIA_FIRE
