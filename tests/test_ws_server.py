from gesture_control.actions import ActionStatus, ControlMode
from gesture_control.server.ws_server import GestureWebSocketServer


class FakeEngine:
    def __init__(self):
        self.commands = []

    def set_mode(self, mode):
        self.commands.append(("set_mode", mode))

    def set_live_param(self, key, value):
        self.commands.append(("set_param", key, value))

    def force_lock(self):
        self.commands.append(("lock",))


def test_ws_state_payload_updates_without_running_server():
    engine = FakeEngine()
    server = GestureWebSocketServer(engine)  # type: ignore[arg-type]
    status = ActionStatus(True, True, ControlMode.CURSOR, "ready", fsm_state="UNLOCKED")

    server.update_state(status, "point", 29.4, {"capture": 1.0})

    assert server._state.state == "UNLOCKED"
    assert server._state.mode == "cursor"
    assert server._state.gesture == "point"


def test_ws_command_handler_routes_controls():
    engine = FakeEngine()
    server = GestureWebSocketServer(engine)  # type: ignore[arg-type]

    import asyncio

    asyncio.run(server._handle_message('{"cmd":"set_mode","mode":"volume"}'))
    asyncio.run(server._handle_message('{"cmd":"set_param","key":"alpha","value":0.4}'))
    asyncio.run(server._handle_message('{"cmd":"lock"}'))

    assert ("set_mode", ControlMode.VOLUME) in engine.commands
    assert ("set_param", "alpha", 0.4) in engine.commands
    assert ("lock",) in engine.commands
