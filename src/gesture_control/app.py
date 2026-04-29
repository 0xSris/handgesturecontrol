from __future__ import annotations

import argparse
import time
from dataclasses import replace

from .actions import ActionStatus, GestureActionEngine
from .calibration import CalibrationSession, CalibrationStatus
from .config import RuntimeConfig, load_profile
from .events import EventLogger
from .gestures import GestureResult, classify_gesture
from .hand_tracker import HandTracker
from .media import RecordingSession, RecordingStatus, list_available_cameras, resolve_camera_index, save_snapshot
from .share import ShareServer, ShareStatus
from .smoothing import LabelSmoother

_QR_CACHE: dict[tuple[str, int], object] = {}


def main() -> None:
    config = parse_args()
    run(config)


def run(config: RuntimeConfig) -> None:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for webcam capture. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    if config.list_cameras:
        cameras = list_available_cameras(cv2, config.camera_probe_limit)
        print("Available cameras:", ", ".join(str(camera) for camera in cameras) if cameras else "none")
        return

    share_server = ShareServer(config.share_path, config.share_port)
    share_status = share_server.start() if config.share_path else share_server.status
    if share_status.url:
        config = replace(config, share_url=share_status.url)

    tracker = HandTracker(config)
    label_smoother = LabelSmoother(config.gesture_history)
    action_engine = GestureActionEngine(config)
    recorder = RecordingSession(config.record_output, config.record_fps)
    event_logger = EventLogger(config.event_log)
    calibration = (
        CalibrationSession(config.calibration_output, config.calibration_samples)
        if config.calibration_output
        else None
    )
    camera_index = resolve_camera_index(cv2, config.camera_index, config.camera_probe_limit)
    capture = cv2.VideoCapture(camera_index)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    if not capture.isOpened():
        tracker.close()
        raise RuntimeError(f"Could not open camera index {camera_index}.")

    window_name = "Hand Gesture Control"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, config.display_width, config.display_height)
    previous_time = time.perf_counter()
    fps = 0.0

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frame = resize_for_display(cv2, frame, config.display_width, config.display_height)

            if config.mirror:
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hand = tracker.process_rgb(rgb)
            gesture = GestureResult("no_hand", 0.0, (False, False, False, False, False), 1.0, 1.0, (0.5, 0.5), (0.5, 0.5))
            stable_label = "no_hand"

            if hand is None:
                label_smoother.reset()
            else:
                gesture = classify_gesture(
                    hand.landmarks,
                    hand.handedness,
                    config.pinch_threshold,
                    config.middle_pinch_threshold,
                )
                stable_label = label_smoother.update(gesture.name)
                if calibration is not None and not calibration.saved:
                    calibration.update(gesture, config)
                if config.draw_landmarks:
                    draw_landmarks(cv2, frame, hand.raw_landmarks, tracker.connections)

            action_label = gesture.name if gesture.confidence >= config.action_confidence else stable_label
            action_status = action_engine.update(action_label, gesture)
            event_logger.log_if_changed(action_label, action_status)
            now = time.perf_counter()
            frame_delta = now - previous_time
            previous_time = now
            if frame_delta > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / frame_delta)

            draw_overlay(cv2, frame, stable_label, gesture, fps, action_status, recorder.status, config.ui_scale)
            if config.show_debug:
                draw_debug(cv2, frame, action_label, gesture, config.ui_scale)
            if calibration is not None:
                draw_calibration(cv2, frame, calibration.status, config.ui_scale)
            else:
                draw_hints(cv2, frame, action_status, config.ui_scale)
            if share_status.url or config.share_path or action_status.mode.value == "share":
                draw_share(cv2, frame, share_status, config.ui_scale)
            if recorder.status.active:
                draw_recording_indicator(cv2, frame, recorder.status)
                recorder.write(cv2, frame)
            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("s"):
                path = save_snapshot(cv2, frame, config.snapshot_dir)
                print(f"Snapshot saved: {path}")
            if key == ord("t"):
                share_status = share_server.toggle()
                if share_status.url:
                    config = replace(config, share_url=share_status.url)
            if key in (ord("u"), ord("l"), ord("c"), ord("v"), ord("x"), ord("m"), ord("b"), ord("p"), ord("h")):
                event_logger.log_if_changed("keyboard", action_engine.handle_keyboard(key))
    finally:
        capture.release()
        recorder.close()
        event_logger.close()
        share_server.close()
        tracker.close()
        cv2.destroyAllWindows()


def draw_overlay(cv2: object, frame: object, label: str, gesture: GestureResult, fps: float, status: ActionStatus, recording: RecordingStatus | None = None, scale: float = 0.62) -> None:
    scale = clamp_scale(scale)
    x, y = 12, 12
    panel_w = int(430 * scale)
    panel_h = int((172 if recording is not None and recording.active else 150) * scale)
    pad = int(16 * scale)
    line = int(28 * scale)
    cv2.rectangle(frame, (x, y), (x + panel_w, y + panel_h), (20, 24, 31), -1)
    cv2.putText(frame, f"Gesture: {label}", (x + pad, y + line), cv2.FONT_HERSHEY_SIMPLEX, 0.78 * scale, (86, 211, 100), max(1, round(2 * scale)))
    cv2.putText(frame, f"Confidence: {gesture.confidence:.2f}", (x + pad, y + line * 2), cv2.FONT_HERSHEY_SIMPLEX, 0.58 * scale, (238, 238, 238), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}", (x + pad, y + line * 3), cv2.FONT_HERSHEY_SIMPLEX, 0.58 * scale, (238, 238, 238), 1)
    cv2.putText(frame, f"Actions: {'ON' if status.enabled else 'PREVIEW'} / {'ACTIVE' if status.active else 'LOCKED'}", (x + pad, y + line * 4), cv2.FONT_HERSHEY_SIMPLEX, 0.58 * scale, (238, 238, 238), 1)
    dragging = " DRAG" if status.dragging else ""
    lock_note = f" {round(status.lock_progress * 100)}%" if status.lock_progress > 0 else ""
    cv2.putText(frame, f"Mode: {status.mode.value}{dragging}  Last: {status.last_action}{lock_note}", (x + pad, y + line * 5), cv2.FONT_HERSHEY_SIMPLEX, 0.58 * scale, (238, 238, 238), 1)
    if recording is not None and recording.active:
        cv2.putText(frame, f"Recording: {recording.frames_written} frames", (x + pad, y + line * 6), cv2.FONT_HERSHEY_SIMPLEX, 0.48 * scale, (118, 180, 255), 1)


def clamp_scale(scale: float) -> float:
    return min(max(scale, 0.45), 1.2)


def resize_for_display(cv2: object, frame: object, display_width: int, display_height: int) -> object:
    height, width = frame.shape[:2]
    if width == display_width and height == display_height:
        return frame
    return cv2.resize(frame, (display_width, display_height), interpolation=cv2.INTER_AREA)


def draw_recording_indicator(cv2: object, frame: object, status: RecordingStatus) -> None:
    height, width = frame.shape[:2]
    cv2.circle(frame, (width - 28, height - 28), 8, (45, 45, 230), -1)
    cv2.putText(frame, "REC", (width - 78, height - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (238, 238, 238), 1)


def draw_debug(cv2: object, frame: object, action_label: str, gesture: GestureResult, scale: float = 0.62) -> None:
    scale = clamp_scale(scale)
    height, _ = frame.shape[:2]
    panel_w = int(470 * scale)
    panel_h = int(86 * scale)
    line = int(24 * scale)
    pad = int(16 * scale)
    y1 = max(height - panel_h - 18, 12)
    cv2.rectangle(frame, (12, y1), (12 + panel_w, y1 + panel_h), (20, 24, 31), -1)
    fingers = "".join("1" if finger else "0" for finger in gesture.fingers_up)
    cv2.putText(frame, f"Action gesture: {action_label}", (12 + pad, y1 + line), cv2.FONT_HERSHEY_SIMPLEX, 0.52 * scale, (118, 180, 255), 1)
    cv2.putText(frame, f"Pinch i/m: {gesture.pinch_distance:.3f} / {gesture.middle_pinch_distance:.3f}", (12 + pad, y1 + line * 2), cv2.FONT_HERSHEY_SIMPLEX, 0.52 * scale, (238, 238, 238), 1)
    cv2.putText(frame, f"Fingers T-I-M-R-P: {fingers}", (12 + pad, y1 + line * 3), cv2.FONT_HERSHEY_SIMPLEX, 0.48 * scale, (238, 238, 238), 1)


def draw_hints(cv2: object, frame: object, status: ActionStatus, scale: float = 0.62) -> None:
    scale = clamp_scale(scale)
    height, width = frame.shape[:2]
    hints = mode_hints(status)
    line = int(24 * scale)
    pad = int(16 * scale)
    box_height = int(40 * scale) + line * len(hints)
    box_width = min(int(430 * scale), max(width - 24, 220))
    x1 = max(width - box_width - 12, 12)
    y1 = int(170 * scale) if width < 920 else 12
    x2 = min(x1 + box_width, width - 12)
    cv2.rectangle(frame, (x1, y1), (x2, y1 + box_height), (20, 24, 31), -1)
    cv2.putText(frame, "Controls", (x1 + pad, y1 + line), cv2.FONT_HERSHEY_SIMPLEX, 0.64 * scale, (86, 211, 100), max(1, round(2 * scale)))
    for index, hint in enumerate(hints):
        cv2.putText(frame, hint, (x1 + pad, y1 + int(48 * scale) + index * line), cv2.FONT_HERSHEY_SIMPLEX, 0.52 * scale, (238, 238, 238), 1)


def mode_hints(status: ActionStatus) -> list[str]:
    if not status.active:
        return ["open palm: unlock", "hold fist: lock", "three fingers: change mode", "keys: u unlock, l lock"]

    if status.mode.value == "cursor":
        return ["point: move", "pinch: click / hold drag", "middle pinch: right click", "peace: scroll"]
    if status.mode.value == "volume":
        return ["thumb-index distance: volume", "three fingers: shortcuts mode", "hold fist: lock"]
    if status.mode.value == "shortcuts":
        return ["point: alt-tab", "peace: play/pause", "pinch: screenshot", "hold fist: lock"]
    if status.mode.value == "media":
        return ["point: next", "peace: play/pause", "pinch: previous", "middle pinch: mute"]
    if status.mode.value == "browser":
        return ["point: open browser", "peace: new tab", "pinch: close tab", "middle pinch: reopen tab"]
    if status.mode.value == "presentation":
        return ["point: next slide", "peace: previous slide", "pinch: start show", "middle pinch: end show"]
    return ["point: copy link", "peace: open share page", "pinch: copy + open", "key t: toggle server"]


def draw_share(cv2: object, frame: object, status: ShareStatus, scale: float = 0.62) -> None:
    scale = clamp_scale(scale)
    height, width = frame.shape[:2]
    show_qr = bool(status.active and status.url)
    panel_w = min(int((520 if show_qr else 430) * scale), width - 24)
    panel_h = int((210 if show_qr else 76) * scale)
    x1 = max(width - panel_w - 12, 12)
    y1 = max(height - panel_h - int(72 * scale), 12)
    cv2.rectangle(frame, (x1, y1), (x1 + panel_w, y1 + panel_h), (20, 24, 31), -1)
    cv2.putText(frame, "Share link", (x1 + int(14 * scale), y1 + int(24 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.58 * scale, (86, 211, 100), max(1, round(2 * scale)))
    cv2.putText(frame, status.url or status.message, (x1 + int(14 * scale), y1 + int(52 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.46 * scale, (238, 238, 238), 1)
    if show_qr and status.url:
        qr_size = int(128 * scale)
        qr = qr_code(cv2, status.url, qr_size)
        qr_x = x1 + panel_w - qr_size - int(16 * scale)
        qr_y = y1 + int(64 * scale)
        frame[qr_y:qr_y + qr_size, qr_x:qr_x + qr_size] = qr
        text_x = x1 + int(14 * scale)
        cv2.putText(frame, "Scan to receive", (text_x, y1 + int(90 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.52 * scale, (238, 238, 238), 1)
        cv2.putText(frame, "Single files download", (text_x, y1 + int(116 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.42 * scale, (238, 238, 238), 1)
        cv2.putText(frame, "directly on phone", (text_x, y1 + int(140 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.42 * scale, (238, 238, 238), 1)


def qr_code(cv2: object, text: str, size: int) -> object:
    key = (text, size)
    if key in _QR_CACHE:
        return _QR_CACHE[key]
    encoder = cv2.QRCodeEncoder_create()
    raw = encoder.encode(text)
    qr = cv2.resize(raw, (size, size), interpolation=cv2.INTER_NEAREST)
    qr = cv2.cvtColor(qr, cv2.COLOR_GRAY2BGR)
    _QR_CACHE[key] = qr
    return qr


def draw_calibration(cv2: object, frame: object, status: CalibrationStatus, scale: float = 0.62) -> None:
    scale = clamp_scale(scale)
    height, width = frame.shape[:2]
    panel_h = int(126 * scale)
    y1 = height - panel_h
    cv2.rectangle(frame, (12, y1), (width - 12, height - 12), (20, 24, 31), -1)
    cv2.putText(frame, "Calibration", (28, y1 + int(32 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.76 * scale, (86, 211, 100), max(1, round(2 * scale)))
    cv2.putText(frame, status.instruction, (28, y1 + int(64 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.62 * scale, (238, 238, 238), 1)
    bar_x1, bar_y1 = 28, y1 + int(86 * scale)
    bar_x2, bar_y2 = width - 28, y1 + int(104 * scale)
    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (66, 74, 84), 1)
    fill_x = int(bar_x1 + (bar_x2 - bar_x1) * min(max(status.progress, 0.0), 1.0))
    cv2.rectangle(frame, (bar_x1, bar_y1), (fill_x, bar_y2), (86, 211, 100), -1)
    if status.complete and status.output_path:
        cv2.putText(frame, status.output_path, (28, height - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.46 * scale, (238, 238, 238), 1)


def draw_landmarks(cv2: object, frame: object, landmarks: object, connections: object) -> None:
    height, width = frame.shape[:2]
    points = []
    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

    for connection in connections:
        start = points[connection.start]
        end = points[connection.end]
        cv2.line(frame, start, end, (70, 175, 255), 2)

    for point in points:
        cv2.circle(frame, point, 4, (86, 211, 100), -1)


def parse_args() -> RuntimeConfig:
    parser = argparse.ArgumentParser(description="Run real-time hand gesture recognition.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index to open.")
    parser.add_argument("--width", type=int, default=960, help="Requested capture width.")
    parser.add_argument("--height", type=int, default=540, help="Requested capture height.")
    parser.add_argument("--display-width", type=int, default=960, help="Displayed preview width.")
    parser.add_argument("--display-height", type=int, default=540, help="Displayed preview height.")
    parser.add_argument("--ui-scale", type=float, default=0.62, help="Overlay size scale.")
    parser.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=True, help="Mirror the camera preview.")
    parser.add_argument("--landmarks", action=argparse.BooleanOptionalAction, default=True, help="Draw hand landmarks.")
    parser.add_argument("--detection-confidence", type=float, default=0.65, help="MediaPipe detection confidence.")
    parser.add_argument("--tracking-confidence", type=float, default=0.65, help="MediaPipe tracking confidence.")
    parser.add_argument("--gesture-history", type=int, default=7, help="Frames used for label smoothing.")
    parser.add_argument("--action-confidence", type=float, default=0.45, help="Minimum raw gesture confidence for actions.")
    parser.add_argument("--enable-actions", action="store_true", help="Allow real mouse, keyboard, and volume actions.")
    parser.add_argument("--cursor-sensitivity", type=float, default=1.35, help="Cursor movement amplification.")
    parser.add_argument("--action-cooldown", type=float, default=0.65, help="Seconds between one-shot actions.")
    parser.add_argument("--drag-hold", type=float, default=0.45, help="Seconds to hold pinch before dragging.")
    parser.add_argument("--lock-hold", type=float, default=0.8, help="Seconds to hold fist before locking actions.")
    parser.add_argument("--pinch-threshold", type=float, default=0.075, help="Thumb-index distance threshold for pinch.")
    parser.add_argument("--middle-pinch-threshold", type=float, default=0.075, help="Thumb-middle distance threshold for right click.")
    parser.add_argument("--profile", type=str, default=None, help="Optional JSON profile for tuning and shortcuts.")
    parser.add_argument("--calibrate-output", type=str, default=None, help="Write a tuned JSON profile from live hand calibration.")
    parser.add_argument("--calibration-samples", type=int, default=60, help="Samples per calibration phase.")
    parser.add_argument("--record-output", type=str, default=None, help="Save the annotated session as an MP4 video.")
    parser.add_argument("--record-fps", type=float, default=20.0, help="FPS for recorded video.")
    parser.add_argument("--snapshot-dir", type=str, default="captures", help="Directory for snapshots saved with the s key.")
    parser.add_argument("--event-log", type=str, default=None, help="Write gesture/action events to CSV.")
    parser.add_argument("--share-path", type=str, default=None, help="Folder or file to share over the local network.")
    parser.add_argument("--share-port", type=int, default=8765, help="Port for local file sharing.")
    parser.add_argument("--browser-home-url", type=str, default="https://www.google.com", help="URL opened by browser mode.")
    parser.add_argument("--show-debug", action="store_true", help="Show raw gesture diagnostics on the preview.")
    parser.add_argument("--list-cameras", action="store_true", help="Probe and print available camera indexes, then exit.")
    parser.add_argument("--camera-probe-limit", type=int, default=5, help="Number of camera indexes to probe.")
    args = parser.parse_args()
    profile = load_profile(args.profile)

    values = dict(
        camera_index=args.camera,
        frame_width=args.width,
        frame_height=args.height,
        display_width=args.display_width,
        display_height=args.display_height,
        ui_scale=args.ui_scale,
        mirror=args.mirror,
        draw_landmarks=args.landmarks,
        detection_confidence=args.detection_confidence,
        tracking_confidence=args.tracking_confidence,
        gesture_history=args.gesture_history,
        action_confidence=args.action_confidence,
        enable_actions=args.enable_actions,
        cursor_sensitivity=args.cursor_sensitivity,
        action_cooldown_seconds=args.action_cooldown,
        drag_hold_seconds=args.drag_hold,
        lock_hold_seconds=args.lock_hold,
        pinch_threshold=args.pinch_threshold,
        middle_pinch_threshold=args.middle_pinch_threshold,
        calibration_output=args.calibrate_output,
        calibration_samples=args.calibration_samples,
        record_output=args.record_output,
        record_fps=args.record_fps,
        snapshot_dir=args.snapshot_dir,
        event_log=args.event_log,
        share_path=args.share_path,
        share_port=args.share_port,
        browser_home_url=args.browser_home_url,
        show_debug=args.show_debug,
        list_cameras=args.list_cameras,
        camera_probe_limit=args.camera_probe_limit,
    )
    values.update(profile)
    return RuntimeConfig(**values)
