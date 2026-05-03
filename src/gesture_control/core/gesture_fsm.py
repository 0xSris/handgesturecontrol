from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Mapping

from gesture_control.actions import ControlMode

FAST_GESTURE_FRAMES = 3
DESTRUCTIVE_GESTURE_FRAMES = 5


class GestureState(str, Enum):
    IDLE = "IDLE"
    UNLOCKED = "UNLOCKED"
    LOCKED = "LOCKED"
    CURSOR_HOVER = "CURSOR_HOVER"
    CURSOR_CLICK_DOWN = "CURSOR_CLICK_DOWN"
    CURSOR_DRAG = "CURSOR_DRAG"
    CURSOR_SCROLL = "CURSOR_SCROLL"
    VOLUME_ADJUST = "VOLUME_ADJUST"
    SHORTCUT_FIRE = "SHORTCUT_FIRE"
    MEDIA_FIRE = "MEDIA_FIRE"
    BROWSER_FIRE = "BROWSER_FIRE"
    PRESENTATION_FIRE = "PRESENTATION_FIRE"
    SHARE_FIRE = "SHARE_FIRE"


@dataclass(frozen=True)
class StableGesture:
    name: str
    stable: bool


@dataclass
class GestureDebouncer:
    frame_requirements: Mapping[str, int] = field(default_factory=dict)
    default_frames: int = FAST_GESTURE_FRAMES
    _buffers: dict[str, Deque[str]] = field(default_factory=dict)

    def update(self, gesture: str) -> StableGesture:
        needed = max(1, int(self.frame_requirements.get(gesture, self.default_frames)))
        buffer = self._buffers.setdefault(gesture, deque(maxlen=needed))
        if buffer.maxlen != needed:
            buffer = deque(maxlen=needed)
            self._buffers[gesture] = buffer
        buffer.append(gesture)
        for other, other_buffer in self._buffers.items():
            if other != gesture:
                other_buffer.clear()
        return StableGesture(gesture, len(buffer) == needed and all(item == gesture for item in buffer))

    def reset(self) -> None:
        for buffer in self._buffers.values():
            buffer.clear()


@dataclass(frozen=True)
class FSMEvent:
    state: GestureState
    mode: ControlMode
    gesture: str
    action_allowed: bool
    transition: tuple[GestureState, GestureState] | None = None
    cycle_mode: bool = False


class GestureFSM:
    def __init__(
        self,
        initial_mode: ControlMode = ControlMode.CURSOR,
        debounce_frames: Mapping[str, int] | None = None,
        default_frames: int = 1,
    ) -> None:
        self.state = GestureState.LOCKED
        self.mode = initial_mode
        self._debouncer = GestureDebouncer(debounce_frames or {}, default_frames)

    @property
    def active(self) -> bool:
        return self.state not in {GestureState.IDLE, GestureState.LOCKED}

    def force_lock(self) -> FSMEvent:
        previous = self.state
        self.state = GestureState.LOCKED
        return FSMEvent(self.state, self.mode, "lock", False, (previous, self.state) if previous != self.state else None)

    def force_unlock(self) -> FSMEvent:
        previous = self.state
        self.state = GestureState.UNLOCKED
        return FSMEvent(self.state, self.mode, "open_palm", True, (previous, self.state) if previous != self.state else None)

    def set_mode(self, mode: ControlMode) -> None:
        self.mode = mode

    def update(self, gesture: str, confidence: float = 1.0) -> FSMEvent:
        if gesture == "no_hand":
            previous = self.state
            self.state = GestureState.IDLE
            self._debouncer.reset()
            return FSMEvent(self.state, self.mode, gesture, False, (previous, self.state) if previous != self.state else None)

        stable = self._debouncer.update(gesture)
        if not stable.stable:
            return FSMEvent(self.state, self.mode, gesture, False)

        previous = self.state
        cycle_mode = False

        if self.state in {GestureState.IDLE, GestureState.LOCKED}:
            if gesture == "open_palm":
                self.state = GestureState.UNLOCKED
            return FSMEvent(self.state, self.mode, gesture, self.active, self._transition(previous), cycle_mode)

        if gesture == "fist":
            self.state = GestureState.LOCKED
            return FSMEvent(self.state, self.mode, gesture, False, self._transition(previous))

        if gesture == "three_fingers":
            cycle_mode = True
            self.state = GestureState.UNLOCKED
            return FSMEvent(self.state, self.mode, gesture, True, self._transition(previous), cycle_mode)

        self.state = self._action_state_for(gesture)
        return FSMEvent(self.state, self.mode, gesture, True, self._transition(previous), cycle_mode)

    def _transition(self, previous: GestureState) -> tuple[GestureState, GestureState] | None:
        if previous == self.state:
            return None
        return (previous, self.state)

    def _action_state_for(self, gesture: str) -> GestureState:
        if self.mode == ControlMode.CURSOR:
            if gesture == "pinch":
                return GestureState.CURSOR_CLICK_DOWN
            if gesture == "peace":
                return GestureState.CURSOR_SCROLL
            return GestureState.CURSOR_HOVER
        if self.mode == ControlMode.VOLUME:
            return GestureState.VOLUME_ADJUST
        if self.mode == ControlMode.SHORTCUTS:
            return GestureState.SHORTCUT_FIRE
        if self.mode == ControlMode.MEDIA:
            return GestureState.MEDIA_FIRE
        if self.mode == ControlMode.BROWSER:
            return GestureState.BROWSER_FIRE
        if self.mode == ControlMode.PRESENTATION:
            return GestureState.PRESENTATION_FIRE
        return GestureState.SHARE_FIRE
