from gesture_control.actions import AutomationBackend, ControlMode, GestureActionEngine
from gesture_control.config import RuntimeConfig
from gesture_control.gestures import GestureResult


class FakeBackend(AutomationBackend):
    def __init__(self):
        self.calls = []

    def move_cursor(self, x, y):
        self.calls.append(("move_cursor", round(x, 3), round(y, 3)))

    def click(self):
        self.calls.append(("click",))

    def right_click(self):
        self.calls.append(("right_click",))

    def mouse_down(self):
        self.calls.append(("mouse_down",))

    def mouse_up(self):
        self.calls.append(("mouse_up",))

    def scroll(self, clicks):
        self.calls.append(("scroll", clicks))

    def press(self, key):
        self.calls.append(("press", key))

    def hotkey(self, *keys):
        self.calls.append(("hotkey", keys))

    def set_volume(self, percent):
        self.calls.append(("set_volume", percent))

    def open_url(self, url):
        self.calls.append(("open_url", url))

    def copy_text(self, text):
        self.calls.append(("copy_text", text))


def gesture(name, pinch=0.08, index_position=(0.6, 0.4), fingers_up=(False, True, False, False, False)):
    return GestureResult(
        name=name,
        confidence=0.9,
        fingers_up=fingers_up,
        pinch_distance=pinch,
        middle_pinch_distance=0.08,
        index_position=index_position,
        palm_position=(0.5, 0.5),
    )


class FakeClock:
    def __init__(self):
        self.now = 1.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_actions_lock_until_open_palm():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True), backend)

    engine.update("point", gesture("point"))
    assert backend.calls == []

    status = engine.update("open_palm", gesture("open_palm"))
    assert status.active is True

    engine.update("point", gesture("point"))
    assert backend.calls[0][0] == "move_cursor"


def test_fist_locks_actions_again():
    backend = FakeBackend()
    clock = FakeClock()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, lock_hold_seconds=0.5), backend, clock)

    engine.update("open_palm", gesture("open_palm"))
    status = engine.update("fist", gesture("fist"))
    assert status.active is True
    assert status.last_action == "hold fist to lock"

    clock.advance(0.6)
    engine.update("fist", gesture("fist"))
    engine.update("point", gesture("point"))

    assert backend.calls == []
    assert engine.status.active is False


def test_three_fingers_cycles_mode():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    assert engine.status.mode == ControlMode.CURSOR
    engine.update("three_fingers", gesture("three_fingers"))
    assert engine.status.mode == ControlMode.VOLUME
    engine.update("three_fingers", gesture("three_fingers"))
    assert engine.status.mode == ControlMode.SHORTCUTS


def test_volume_mode_maps_pinch_to_percent():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.update("open_palm", gesture("open_palm"))
    engine.update("three_fingers", gesture("three_fingers"))
    engine.update("pinch", gesture("pinch", pinch=0.24))

    assert ("set_volume", 100) in backend.calls


def test_volume_mode_uses_pinch_distance_even_when_label_is_point():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.update("open_palm", gesture("open_palm"))
    engine.update("three_fingers", gesture("three_fingers"))
    engine.update("point", gesture("point", pinch=0.24))

    assert ("set_volume", 100) in backend.calls


def test_volume_mode_keeps_working_when_index_is_not_extended():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.update("open_palm", gesture("open_palm"))
    engine.update("three_fingers", gesture("three_fingers"))
    engine.update("pinch", gesture("pinch", pinch=0.24, fingers_up=(False, False, False, False, False)))

    assert ("set_volume", 100) in backend.calls


def test_short_pinch_clicks_on_release():
    backend = FakeBackend()
    clock = FakeClock()
    engine = GestureActionEngine(
        RuntimeConfig(enable_actions=True, action_cooldown_seconds=0, drag_hold_seconds=0.5),
        backend,
        clock,
    )

    engine.update("open_palm", gesture("open_palm"))
    engine.update("pinch", gesture("pinch"))
    clock.advance(0.2)
    engine.update("point", gesture("point"))

    assert ("click",) in backend.calls
    assert ("mouse_down",) not in backend.calls


def test_long_pinch_drags_until_release():
    backend = FakeBackend()
    clock = FakeClock()
    engine = GestureActionEngine(
        RuntimeConfig(enable_actions=True, action_cooldown_seconds=0, drag_hold_seconds=0.5),
        backend,
        clock,
    )

    engine.update("open_palm", gesture("open_palm"))
    engine.update("pinch", gesture("pinch"))
    clock.advance(0.6)
    status = engine.update("pinch", gesture("pinch"))
    assert status.dragging is True
    engine.update("point", gesture("point"))

    assert ("mouse_down",) in backend.calls
    assert ("mouse_up",) in backend.calls


def test_middle_pinch_right_clicks():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.update("open_palm", gesture("open_palm"))
    engine.update("middle_pinch", gesture("middle_pinch"))

    assert ("right_click",) in backend.calls


def test_shortcut_mode_uses_custom_profile_mapping():
    backend = FakeBackend()
    engine = GestureActionEngine(
        RuntimeConfig(
            enable_actions=True,
            action_cooldown_seconds=0,
            shortcuts={"peace": ("ctrl", "l")},
        ),
        backend,
    )

    engine.update("three_fingers", gesture("three_fingers"))
    engine.update("three_fingers", gesture("three_fingers"))
    engine.update("open_palm", gesture("open_palm"))
    engine.update("peace", gesture("peace"))

    assert ("hotkey", ("ctrl", "l")) in backend.calls


def test_keyboard_controls_lock_unlock_and_force_modes():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True), backend)

    engine.handle_keyboard(ord("u"))
    assert engine.status.active is True

    engine.handle_keyboard(ord("v"))
    assert engine.status.mode == ControlMode.VOLUME

    engine.handle_keyboard(ord("x"))
    assert engine.status.mode == ControlMode.SHORTCUTS

    engine.handle_keyboard(ord("m"))
    assert engine.status.mode == ControlMode.MEDIA

    engine.handle_keyboard(ord("b"))
    assert engine.status.mode == ControlMode.BROWSER

    engine.handle_keyboard(ord("p"))
    assert engine.status.mode == ControlMode.PRESENTATION

    engine.handle_keyboard(ord("h"))
    assert engine.status.mode == ControlMode.SHARE

    engine.handle_keyboard(ord("c"))
    assert engine.status.mode == ControlMode.CURSOR

    engine.handle_keyboard(ord("l"))
    assert engine.status.active is False


def test_media_mode_controls_playback():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.handle_keyboard(ord("u"))
    engine.handle_keyboard(ord("m"))
    engine.update("peace", gesture("peace"))
    engine.update("point", gesture("point"))

    assert ("press", "playpause") in backend.calls
    assert ("press", "nexttrack") in backend.calls


def test_browser_mode_controls_tabs():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.handle_keyboard(ord("u"))
    engine.handle_keyboard(ord("b"))
    engine.update("point", gesture("point"))
    engine.update("peace", gesture("peace"))
    engine.update("pinch", gesture("pinch"))

    assert ("open_url", "https://www.google.com") in backend.calls
    assert ("hotkey", ("ctrl", "w")) in backend.calls


def test_presentation_mode_controls_slides():
    backend = FakeBackend()
    engine = GestureActionEngine(RuntimeConfig(enable_actions=True, action_cooldown_seconds=0), backend)

    engine.handle_keyboard(ord("u"))
    engine.handle_keyboard(ord("p"))
    engine.update("point", gesture("point"))
    engine.update("peace", gesture("peace"))

    assert ("press", "right") in backend.calls
    assert ("press", "left") in backend.calls


def test_share_mode_copies_and_opens_link():
    backend = FakeBackend()
    engine = GestureActionEngine(
        RuntimeConfig(enable_actions=True, action_cooldown_seconds=0, share_url="http://192.168.1.10:8765/"),
        backend,
    )

    engine.handle_keyboard(ord("u"))
    engine.handle_keyboard(ord("h"))
    engine.update("point", gesture("point"))
    engine.update("peace", gesture("peace"))
    engine.update("pinch", gesture("pinch"))

    assert ("copy_text", "http://192.168.1.10:8765/") in backend.calls
    assert ("open_url", "http://192.168.1.10:8765/") in backend.calls
