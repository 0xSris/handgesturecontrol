from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from gesture_control.actions import ActionStatus, ControlMode, GestureActionEngine

DEFAULT_WS_HOST = "127.0.0.1"
DEFAULT_WS_PORT = 7433
DEFAULT_BROADCAST_INTERVAL = 0.1


@dataclass
class BroadcastState:
    state: str = "LOCKED"
    mode: str = "cursor"
    gesture: str = "no_hand"
    fps: float = 0.0
    perf: dict[str, float] = field(default_factory=dict)


class GestureWebSocketServer:
    def __init__(
        self,
        action_engine: GestureActionEngine,
        host: str = DEFAULT_WS_HOST,
        port: int = DEFAULT_WS_PORT,
        interval_seconds: float = DEFAULT_BROADCAST_INTERVAL,
        on_toggle: Callable[[], None] | None = None,
        debug: bool = False,
    ) -> None:
        self._action_engine = action_engine
        self._host = host
        self._port = port
        self._interval = interval_seconds
        self._on_toggle = on_toggle
        self._debug = debug
        self._state = BroadcastState()
        self._clients: set[Any] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(target=self._run_thread, name="gesture-ws-server", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def update_state(
        self,
        status: ActionStatus,
        gesture: str,
        fps: float,
        perf: dict[str, float] | None = None,
    ) -> None:
        self._state = BroadcastState(
            state=status.fsm_state,
            mode=status.mode.value,
            gesture=gesture,
            fps=round(fps, 1),
            perf=perf or {},
        )

    def _run_thread(self) -> None:
        try:
            import websockets
        except ImportError:
            return

        async def handler(websocket: Any) -> None:
            self._clients.add(websocket)
            try:
                async for message in websocket:
                    await self._handle_message(message)
            finally:
                self._clients.discard(websocket)

        async def main() -> None:
            async with websockets.serve(handler, self._host, self._port):
                while not self._stop_event.is_set():
                    await self._broadcast_once()
                    await asyncio.sleep(self._interval)

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(main())

    async def _broadcast_once(self) -> None:
        if not self._clients:
            return
        payload: dict[str, Any] = {
            "state": self._state.state,
            "mode": self._state.mode,
            "gesture": self._state.gesture,
            "fps": self._state.fps,
        }
        if self._debug:
            payload["perf"] = self._state.perf
        message = json.dumps(payload)
        stale = []
        for client in tuple(self._clients):
            try:
                await client.send(message)
            except Exception:
                stale.append(client)
        for client in stale:
            self._clients.discard(client)

    async def _handle_message(self, message: str) -> None:
        try:
            command = json.loads(message)
        except json.JSONDecodeError:
            return
        cmd = command.get("cmd")
        if cmd == "toggle" and self._on_toggle is not None:
            self._on_toggle()
        elif cmd == "set_mode":
            mode = command.get("mode")
            if isinstance(mode, str) and mode in {item.value for item in ControlMode}:
                self._action_engine.set_mode(ControlMode(mode))
        elif cmd == "set_param":
            self._action_engine.set_live_param(str(command.get("key")), command.get("value"))
        elif cmd == "lock":
            self._action_engine.force_lock()


class NullWebSocketServer:
    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def update_state(self, status: ActionStatus, gesture: str, fps: float, perf: dict[str, float] | None = None) -> None:
        return None
