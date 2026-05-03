from __future__ import annotations

import time
from dataclasses import dataclass, replace
from enum import Enum

from .config import RuntimeConfig
from .gestures import GestureResult


class ControlMode(str, Enum):
    CURSOR = "cursor"
    VOLUME = "volume"
    SHORTCUTS = "shortcuts"
    MEDIA = "media"
    BROWSER = "browser"
    PRESENTATION = "presentation"
    SHARE = "share"


@dataclass(frozen=True)
class ActionStatus:
    enabled: bool
    active: bool
    mode: ControlMode
    last_action: str
    volume_percent: int | None = None
    dragging: bool = False
    lock_progress: float = 0.0
    preview_note: str = ""
    fsm_state: str = "LOCKED"


class AutomationBackend:
    def move_cursor(self, x: float, y: float) -> None:
        raise NotImplementedError

    def click(self) -> None:
        raise NotImplementedError

    def right_click(self) -> None:
        raise NotImplementedError

    def mouse_down(self) -> None:
        raise NotImplementedError

    def mouse_up(self) -> None:
        raise NotImplementedError

    def scroll(self, clicks: int) -> None:
        raise NotImplementedError

    def press(self, key: str) -> None:
        raise NotImplementedError

    def hotkey(self, *keys: str) -> None:
        raise NotImplementedError

    def set_volume(self, percent: int) -> None:
        raise NotImplementedError

    def open_url(self, url: str) -> None:
        raise NotImplementedError

    def copy_text(self, text: str) -> None:
        raise NotImplementedError


class PreviewBackend(AutomationBackend):
    def move_cursor(self, x: float, y: float) -> None:
        return None

    def click(self) -> None:
        return None

    def right_click(self) -> None:
        return None

    def mouse_down(self) -> None:
        return None

    def mouse_up(self) -> None:
        return None

    def scroll(self, clicks: int) -> None:
        return None

    def press(self, key: str) -> None:
        return None

    def hotkey(self, *keys: str) -> None:
        return None

    def set_volume(self, percent: int) -> None:
        return None

    def open_url(self, url: str) -> None:
        return None

    def copy_text(self, text: str) -> None:
        return None


class PyAutoGuiBackend(AutomationBackend):
    def __init__(self) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError(
                "pyautogui is required for system actions. Install dependencies with "
                "`pip install -r requirements.txt`."
            ) from exc

        self._pyautogui = pyautogui
        self._pyautogui.FAILSAFE = True
        self._screen_width, self._screen_height = self._pyautogui.size()
        self._volume = WindowsVolumeController()

    def move_cursor(self, x: float, y: float) -> None:
        safe_x = min(max(x, 0.02), 0.98)
        safe_y = min(max(y, 0.02), 0.98)
        self._pyautogui.moveTo(
            safe_x * self._screen_width,
            safe_y * self._screen_height,
            duration=0.01,
        )

    def click(self) -> None:
        self._pyautogui.click()

    def right_click(self) -> None:
        self._pyautogui.click(button="right")

    def mouse_down(self) -> None:
        self._pyautogui.mouseDown()

    def mouse_up(self) -> None:
        self._pyautogui.mouseUp()

    def scroll(self, clicks: int) -> None:
        self._pyautogui.scroll(clicks)

    def press(self, key: str) -> None:
        self._pyautogui.press(key)

    def hotkey(self, *keys: str) -> None:
        self._pyautogui.hotkey(*keys)

    def set_volume(self, percent: int) -> None:
        if not self._volume.set_percent(percent):
            self._pyautogui.press("volumeup" if percent >= 50 else "volumedown")

    def open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def copy_text(self, text: str) -> None:
        try:
            import pyperclip

            pyperclip.copy(text)
        except Exception:
            self._pyautogui.write(text)


class WindowsVolumeController:
    def __init__(self) -> None:
        self._volume = None
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            self._volume = None

    def set_percent(self, percent: int) -> bool:
        if self._volume is None:
            return False
        scalar = min(max(percent, 0), 100) / 100
        self._volume.SetMasterVolumeLevelScalar(scalar, None)
        return True


class GestureActionEngine:
    def __init__(self, config: RuntimeConfig, backend: AutomationBackend | None = None, clock: object | None = None) -> None:
        self._config = config
        self._backend = backend or (PyAutoGuiBackend() if config.enable_actions else PreviewBackend())
        self._clock = clock or time.perf_counter
        self._mode = ControlMode.CURSOR
        self._active = False
        self._last_action = "preview" if not config.enable_actions else "locked"
        self._last_trigger_at = 0.0
        self._last_volume_percent: int | None = None
        self._fist_started_at: float | None = None
        self._dragging = False
        from .core.cursor_engine import CursorConfig, CursorEngine
        from .core.gesture_fsm import GestureFSM
        from .core.pinch_detector import PinchConfig, PinchDetector

        smoothing = config.smoothing
        self._cursor_engine = CursorEngine(
            CursorConfig(
                alpha=float(smoothing.get("cursor_alpha", config.smoothing_alpha)),
                dead_zone_radius=float(smoothing.get("dead_zone_radius", config.cursor_dead_zone)),
                base_speed=float(smoothing.get("base_speed", config.cursor_sensitivity)),
                acceleration_exponent=float(smoothing.get("acceleration_exponent", 1.5)),
            )
        )
        self._pinch_detector = PinchDetector(
            PinchConfig(
                enter_threshold=config.pinch_enter_threshold,
                exit_threshold=config.pinch_exit_threshold,
                min_click_hold_seconds=config.min_click_hold_seconds,
                click_cooldown_seconds=config.click_cooldown_seconds,
                drag_hold_seconds=config.drag_hold_seconds,
            )
        )
        self._fsm = GestureFSM(ControlMode.CURSOR, config.gesture_debounce, default_frames=1)

    @property
    def status(self) -> ActionStatus:
        lock_progress = 0.0
        if self._fist_started_at is not None:
            hold = max(self._config.lock_hold_seconds, 0.001)
            lock_progress = min(max((self._clock() - self._fist_started_at) / hold, 0.0), 1.0)

        return ActionStatus(
            enabled=self._config.enable_actions,
            active=self._active,
            mode=self._mode,
            last_action=self._last_action,
            volume_percent=self._last_volume_percent,
            dragging=self._dragging,
            lock_progress=lock_progress,
            preview_note="" if self._config.enable_actions else "preview only: add --enable-actions for real keyboard/browser controls",
            fsm_state=self._fsm.state.value,
        )

    def update(self, label: str, gesture: GestureResult) -> ActionStatus:
        now = self._clock()
        fsm_event = self._fsm.update(label, gesture.confidence)
        if fsm_event.transition is not None:
            self._last_action = f"state:{fsm_event.transition[1].value}"

        if label != "fist":
            self._fist_started_at = None

        if label == "open_palm":
            self._fist_started_at = None
            self._active = True
            self._fsm.force_unlock()
            self._last_action = "unlocked"
            return self.status

        if label == "fist":
            self._release_drag()
            self._reset_pinch()
            if self._fist_started_at is None:
                self._fist_started_at = now
                self._last_action = "hold fist to lock"
                return self.status

            if now - self._fist_started_at >= self._config.lock_hold_seconds:
                self._active = False
                self._fsm.force_lock()
                self._fist_started_at = None
                self._last_action = "locked"
            else:
                self._last_action = "hold fist to lock"
            return self.status

        if self._ready(now) and label == "three_fingers":
            self._cycle_mode()
            self._fsm.set_mode(self._mode)
            self._mark_trigger(now, f"mode:{self._mode.value}")
            return self.status

        if not self._active:
            self._reset_pinch()
            return self.status

        if self._mode == ControlMode.CURSOR:
            self._handle_cursor_mode(label, gesture, now)
        elif self._mode == ControlMode.VOLUME:
            self._handle_volume_mode(label, gesture)
        elif self._mode == ControlMode.SHORTCUTS:
            self._handle_shortcut_mode(label, now)
        elif self._mode == ControlMode.MEDIA:
            self._handle_media_mode(label, now)
        elif self._mode == ControlMode.BROWSER:
            self._handle_browser_mode(label, now)
        elif self._mode == ControlMode.PRESENTATION:
            self._handle_presentation_mode(label, now)
        elif self._mode == ControlMode.SHARE:
            self._handle_share_mode(label, now)

        return self.status

    def handle_keyboard(self, key: int) -> ActionStatus:
        if key == ord("u"):
            self._active = True
            self._fsm.force_unlock()
            self._last_action = "unlocked by key"
        elif key == ord("l"):
            self._release_drag()
            self._active = False
            self._fsm.force_lock()
            self._last_action = "locked by key"
        elif key == ord("c"):
            self._mode = ControlMode.CURSOR
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:cursor"
        elif key == ord("v"):
            self._mode = ControlMode.VOLUME
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:volume"
        elif key == ord("x"):
            self._mode = ControlMode.SHORTCUTS
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:shortcuts"
        elif key == ord("m"):
            self._mode = ControlMode.MEDIA
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:media"
        elif key == ord("b"):
            self._mode = ControlMode.BROWSER
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:browser"
        elif key == ord("p"):
            self._mode = ControlMode.PRESENTATION
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:presentation"
        elif key == ord("h"):
            self._mode = ControlMode.SHARE
            self._fsm.set_mode(self._mode)
            self._last_action = "mode:share"
        return self.status

    def force_lock(self) -> ActionStatus:
        self._release_drag()
        self._active = False
        self._fsm.force_lock()
        self._last_action = "locked remotely"
        return self.status

    def toggle_active(self) -> ActionStatus:
        if self._active:
            return self.force_lock()
        self._active = True
        self._fsm.force_unlock()
        self._last_action = "unlocked remotely"
        return self.status

    def set_mode(self, mode: ControlMode) -> ActionStatus:
        self._mode = mode
        self._fsm.set_mode(mode)
        self._last_action = f"mode:{mode.value}"
        return self.status

    def set_live_param(self, key: str, value: object) -> ActionStatus:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return self.status
        if key in {"alpha", "cursor_alpha"}:
            self._cursor_engine.config = replace(self._cursor_engine.config, alpha=number)
        elif key in {"dead_zone", "dead_zone_radius"}:
            self._cursor_engine.config = replace(self._cursor_engine.config, dead_zone_radius=number)
        elif key in {"cursor_speed", "base_speed"}:
            self._cursor_engine.config = replace(self._cursor_engine.config, base_speed=number)
        self._last_action = f"param:{key}"
        return self.status

    def handle_hand_missing(self, elapsed_seconds: float) -> ActionStatus:
        if elapsed_seconds >= 0.5:
            self._reset_pinch()
            self._fsm.update("no_hand", 0.0)
            self._last_action = "waiting for hand"
        return self.status

    def _handle_cursor_mode(self, label: str, gesture: GestureResult, now: float) -> None:
        if label not in {"no_hand"}:
            x, y = self._cursor_engine.update(gesture.index_position)
            self._backend.move_cursor(x, y)
            self._last_action = "move cursor"

        pinch_distance = gesture.pinch_distance
        if label != "pinch":
            pinch_distance = (
                pinch_distance
                if self._pinch_detector.phase.value == "open" and pinch_distance <= self._config.pinch_enter_threshold
                else 1.0
            )
        pinch_event = self._pinch_detector.update(pinch_distance, now)
        if pinch_event.drag_start and not self._dragging:
            self._backend.mouse_down()
            self._dragging = True
            self._last_action = "dragging"
        if pinch_event.drag_release:
            self._release_drag()
            self._mark_trigger(now, "drop")
        if pinch_event.click_release:
            self._backend.click()
            self._mark_trigger(now, "click")

        if label in {"middle_pinch", "thumbs_up"} and self._ready(now):
            self._backend.right_click()
            self._mark_trigger(now, "right click")

        if label == "peace":
            scroll = 4 if gesture.index_position[1] < 0.45 else -4
            self._backend.scroll(scroll)
            self._last_action = "scroll up" if scroll > 0 else "scroll down"

    def _handle_volume_mode(self, label: str, gesture: GestureResult) -> None:
        if label == "no_hand":
            return

        percent = self._pinch_to_percent(gesture.pinch_distance)
        if self._last_volume_percent is None or abs(percent - self._last_volume_percent) >= 3:
            self._backend.set_volume(percent)
            self._last_volume_percent = percent
            self._last_action = f"volume {percent}%"

    def _handle_shortcut_mode(self, label: str, now: float) -> None:
        if not self._ready(now):
            return

        keys = self._config.shortcuts.get(label)
        if not keys:
            return

        if len(keys) == 1:
            self._backend.press(keys[0])
        else:
            self._backend.hotkey(*keys)
        self._mark_trigger(now, "+".join(keys))

    def _handle_media_mode(self, label: str, now: float) -> None:
        if not self._ready(now):
            return
        if label == "point":
            self._backend.hotkey("shift", "n")
            self._mark_trigger(now, "next video")
        elif label == "peace":
            self._backend.press("playpause")
            self._mark_trigger(now, "media play/pause")
        elif label == "pinch":
            self._backend.hotkey("shift", "p")
            self._mark_trigger(now, "previous video")
        elif label in {"middle_pinch", "thumbs_up"}:
            self._backend.press("volumemute")
            self._mark_trigger(now, "mute")

    def _handle_browser_mode(self, label: str, now: float) -> None:
        if not self._ready(now):
            return
        if label == "point":
            self._backend.open_url(self._config.browser_home_url)
            self._mark_trigger(now, "open browser")
        elif label == "peace":
            self._backend.open_url(self._config.browser_home_url)
            self._mark_trigger(now, "new browser tab")
        elif label == "pinch":
            self._backend.hotkey("ctrl", "w")
            self._mark_trigger(now, "close tab")
        elif label in {"middle_pinch", "thumbs_up"}:
            self._backend.hotkey("ctrl", "shift", "t")
            self._mark_trigger(now, "reopen tab")

    def _handle_presentation_mode(self, label: str, now: float) -> None:
        if not self._ready(now):
            return
        if label == "point":
            self._backend.press("right")
            self._mark_trigger(now, "next slide")
        elif label == "peace":
            self._backend.press("left")
            self._mark_trigger(now, "previous slide")
        elif label == "pinch":
            self._backend.press("f5")
            self._mark_trigger(now, "start slideshow")
        elif label in {"middle_pinch", "thumbs_up"}:
            self._backend.press("esc")
            self._backend.press("esc")
            self._mark_trigger(now, "end slideshow")

    def _handle_share_mode(self, label: str, now: float) -> None:
        if not self._ready(now):
            return
        url = self._config.share_url
        if not url:
            self._last_action = "share not configured"
            return
        if label == "point":
            self._backend.copy_text(url)
            self._mark_trigger(now, "copied share link")
        elif label == "peace":
            self._backend.open_url(url)
            self._mark_trigger(now, "opened share page")
        elif label == "pinch":
            self._backend.copy_text(url)
            self._backend.open_url(url)
            self._mark_trigger(now, "shared link")

    def _pinch_to_percent(self, pinch_distance: float) -> int:
        low = self._config.volume_min_pinch
        high = max(self._config.volume_max_pinch, low + 0.001)
        normalized = (pinch_distance - low) / (high - low)
        return round(min(max(normalized, 0.0), 1.0) * 100)

    def _cycle_mode(self) -> None:
        modes = list(ControlMode)
        index = modes.index(self._mode)
        self._mode = modes[(index + 1) % len(modes)]
        self._fsm.set_mode(self._mode)

    def _ready(self, now: float) -> bool:
        return now - self._last_trigger_at >= self._config.action_cooldown_seconds

    def _mark_trigger(self, now: float, action: str) -> None:
        self._last_trigger_at = now
        self._last_action = action

    def _release_drag(self) -> None:
        if self._dragging:
            self._backend.mouse_up()
            self._dragging = False

    def _reset_pinch(self) -> None:
        event = self._pinch_detector.reset()
        if event.drag_release:
            self._release_drag()


