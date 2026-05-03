# Hand Gesture Control

A real-time computer vision system for controlling a desktop using hand gestures. The application captures webcam video, detects 21 hand landmarks, classifies stable gestures, and maps them to everyday actions such as cursor movement, clicks, volume control, browser navigation, media playback, presentation control, screenshots, and local file transfer.

The project focuses on practical human-computer interaction: low-latency tracking, safety locks, gesture smoothing, configurable profiles, and an optional Chrome extension panel for controlling the desktop app without typing terminal commands.

## Project Preview

| Live gesture tracking | Gesture recognition states |
| --- | --- |
| ![Point gesture detection](frontend/assets/gesture-point.jpeg) | ![Three finger gesture detection](frontend/assets/gesture-three-fingers.jpeg) |
| ![Peace gesture detection](frontend/assets/gesture-peace.jpeg) | ![Fist lock gesture detection](frontend/assets/gesture-fist.jpeg) |

## Highlights

- Real-time hand tracking from a standard webcam.
- MediaPipe hand landmark detection with 21 key points per hand.
- One Euro filtering, temporal smoothing, and gesture debouncing for stable recognition.
- Formal gesture state machine with lock, unlock, cursor, media, browser, presentation, and sharing states.
- Cursor movement with smoothing, dead-zone control, acceleration, pinch click, drag-and-drop, scroll, and right click.
- System volume control using thumb-index distance.
- Keyboard shortcut automation through PyAutoGUI.
- YouTube-friendly media controls for play/pause, next video, previous video, and mute.
- Presentation controls for starting, ending, and navigating slides.
- QR-based local file sharing from laptop to phone or another computer on the same Wi-Fi.
- Optional Chrome extension panel with live status, mode switching, sensitivity sliders, emergency lock, and desktop app launcher.
- Event logging, snapshots, recording support, calibration profiles, and Windows launch scripts.

## Tech Stack

- Python 3.10/3.11
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI
- PyCAW
- WebSockets
- Chrome Extension Manifest V3
- HTML, CSS, and JavaScript

## System Architecture

```text
Webcam
  -> OpenCV frame capture
  -> MediaPipe hand landmark detection
  -> One Euro landmark filtering
  -> Gesture classification
  -> Gesture debouncing and finite state machine
  -> Action engine
  -> OS-level automation / volume / browser / file sharing
```

The base hand landmark detector is provided by MediaPipe. The application layer builds the interaction system around it: gesture rules, filtering, thresholds, state transitions, safety logic, calibration, and OS automation.

## Gesture Controls

```text
open palm       unlock controls
hold fist       lock controls
three fingers   cycle mode

cursor mode:
point           move cursor
pinch           click on release
pinch hold      drag and drop
thumbs up       right click
peace           scroll

volume mode:
thumb-index     set volume from distance

shortcut mode:
point           Alt+Tab
peace           play/pause
pinch           screenshot snip

media mode:
point           next video
peace           play/pause
pinch           previous video
thumbs up       mute

browser mode:
point           open browser
peace           open browser tab
pinch           close tab
thumbs up       reopen closed tab

presentation mode:
point           next slide
peace           previous slide
pinch           start slideshow
thumbs up       end slideshow

share mode:
point           copy transfer link
peace           open transfer page
pinch           copy and open transfer page
phone camera    scan QR code
```

## Installation

Use Python 3.10 or 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

On the first run, the MediaPipe hand landmark model is cached in the `models/` folder.

## Quick Start

The easiest way to run the project on Windows is:

```text
Double-click Start Gesture Control.bat
```

For file sharing:

```text
Double-click Start Gesture Control Share.bat
```

You can also drag a file onto `Start Gesture Control Share.bat` to start the transfer demo with that file selected.

## Command-Line Usage

Preview mode, with no real system actions:

```powershell
python -m gesture_control --camera -1 --profile config/default_profile.json --show-debug
```

Real control mode:

```powershell
python -m gesture_control --camera -1 --enable-actions --profile config/default_profile.json --show-debug --ui-scale 0.5
```

File transfer demo:

```powershell
python -m gesture_control --camera -1 --enable-actions --profile config/default_profile.json --share-path "path\to\demo.pdf" --show-debug --ui-scale 0.5
```

Chrome extension bridge:

```powershell
python -m gesture_control --camera -1 --enable-actions --enable-extension --profile config/default_profile.json --show-debug
```

## Chrome Extension

The extension is a control panel for the Python desktop app. Gesture processing still runs locally in Python.

Setup:

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click **Load unpacked**.
4. Select the `extension` folder.

To let the extension start the desktop app directly, run this once:

```text
Install Extension Launcher.bat
```

Then open the extension popup and click **Start Desktop App**.

If you want the app to start automatically when Windows starts:

```text
Install Background Startup.bat
```

To remove startup launch:

```text
Remove Background Startup.bat
```

To remove the extension launcher protocol:

```text
Remove Extension Launcher.bat
```

## File Sharing

File sharing starts a local Wi-Fi server and displays a transfer link with a QR code. A phone or another computer on the same Wi-Fi network can scan the QR code or open the link to download the selected file.

Example:

```powershell
python -m gesture_control --camera -1 --enable-actions --share-path "path\to\demo.pdf" --show-debug
```

## Calibration

Create a tuned profile:

```powershell
python -m gesture_control --calibrate-output config/my_profile.json
```

Run with a saved profile:

```powershell
python -m gesture_control --profile config/my_profile.json
```

Profiles can tune smoothing, debounce frame counts, pinch thresholds, cursor behavior, volume range, shortcuts, and extension settings.

## Presentation Frontend

A local frontend is included for demos and project presentation.

```powershell
start frontend\index.html
```

It includes the project overview, architecture, feature summary, image gallery, demo command, and day/night mode.

## Testing

```powershell
pytest
```

The test suite covers gesture classification, action mapping, calibration, event logging, file sharing, media utilities, smoothing, pinch hysteresis, FSM behavior, WebSocket command handling, and app behavior.

## Build Executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

The executable is created at:

```text
dist/GestureControl/GestureControl.exe
```

## Repository Structure

```text
config/                  Gesture tuning profiles
docs/                    Demo and explanation notes
extension/               Chrome control panel
frontend/                Local presentation frontend
scripts/                 Build, launch, and setup scripts
src/gesture_control/     Main application package
tests/                   Automated tests
```

## Project Summary

Hand Gesture Control demonstrates an applied computer vision pipeline for real-time desktop interaction. It combines hand landmark detection, custom gesture classification, smoothing, state management, and OS-level automation into a usable control system. The main engineering work is in making gestures reliable enough for practical use through filtering, debouncing, safety states, calibration, and clear interaction modes.
