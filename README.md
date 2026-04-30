# Hand Gesture Control

Real-time hand gesture recognition for controlling a computer through a webcam. The application uses OpenCV for video capture, MediaPipe for hand landmark detection, and a custom action engine to turn gestures into mouse, keyboard, volume, browser, presentation, and file-sharing controls.

## Highlights

- Real-time hand tracking with 21 hand landmarks.
- Cursor control with point, pinch-click, drag, right-click, and scroll.
- Volume control using thumb-index distance.
- Shortcut, media, browser, and presentation control modes.
- Local Wi-Fi file transfer with a share link and QR code.
- Direct phone download flow for single-file sharing.
- Preview mode, lock/unlock gestures, cooldowns, and smoothing for safer automation.
- Calibration profiles for tuning pinch distance, sensitivity, and shortcuts.
- Event logging, screenshots, MP4 recording, and Windows executable packaging.
- Presentation frontend and demo notes for explaining the project clearly.

## Screenshots

The app displays a live camera feed with gesture labels, action status, FPS, mode hints, landmarks, and an optional QR transfer panel.

Open the presentation page:

```text
frontend/index.html
```

## Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI
- PyCAW
- PyInstaller
- HTML, CSS, JavaScript for the presentation frontend

## Project Structure

```text
config/                  Gesture tuning profiles
docs/                    Demo and project explanation notes
frontend/                Local presentation page
scripts/                 Build and app entry scripts
src/gesture_control/     Main Python package
tests/                   Automated tests
```

## Setup

Use Python 3.10 or 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

On the first run, the app downloads and caches the MediaPipe hand landmark model in `models/`.

## Run

Preview mode:

```powershell
python -m gesture_control --camera -1 --show-debug --profile config/default_profile.json
```

Real action mode:

```powershell
python -m gesture_control --camera -1 --enable-actions --show-debug --profile config/my_profile.json
```

File transfer demo:

```powershell
python -m gesture_control --camera -1 --enable-actions --profile config/my_profile.json --share-path "C:\Users\Srishti Pandey\Downloads\demo.pdf" --show-debug --ui-scale 0.5
```

Press `q` or `Esc` to exit.

## Keyboard Controls

```text
u   unlock actions
l   lock actions
c   cursor mode
v   volume mode
x   shortcuts mode
m   media mode
b   browser mode
p   presentation mode
h   share mode
t   start/stop share server
s   save snapshot
q   quit
Esc quit
```

## Gesture Controls

```text
open palm       unlock controls
hold fist       lock controls
three fingers   cycle mode

cursor mode:
point           move cursor
pinch           click on release
pinch hold      drag and drop
middle pinch    right click
peace           scroll

volume mode:
thumb-index     set volume from distance

shortcut mode:
point           Alt+Tab
peace           play/pause
pinch           screenshot snip

media mode:
point           next track
peace           play/pause
pinch           previous track
middle pinch    mute

browser mode:
point           open browser
peace           open browser tab
pinch           close tab
middle pinch    reopen closed tab

presentation mode:
point           next slide
peace           previous slide
pinch           start slideshow
middle pinch    end slideshow

share mode:
point           copy transfer link
peace           open transfer page
pinch           copy and open transfer page
phone camera    scan QR code
```

## File Transfer

To share a folder:

```powershell
python -m gesture_control --camera -1 --enable-actions --share-path "C:\Users\Srishti Pandey\Downloads" --show-debug
```

To share one file for the smoothest phone demo:

```powershell
python -m gesture_control --camera -1 --enable-actions --share-path "C:\Users\Srishti Pandey\Downloads\demo.pdf" --show-debug
```

Make sure the phone and laptop are on the same Wi-Fi. The app shows a local URL and QR code. For a single file, scanning the QR code opens the phone download flow directly.

If Windows Firewall asks for permission, allow access on private networks.

## Calibration

Create a tuned profile:

```powershell
python -m gesture_control --calibrate-output config/my_profile.json
```

The app asks for two samples:

```text
1. Touch thumb and index together
2. Spread thumb and index apart
```

Use the saved profile:

```powershell
python -m gesture_control --profile config/my_profile.json
```

## Build Windows Executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

The executable is created at:

```text
dist/GestureControl/GestureControl.exe
```

## Applied AI Explanation

This is an Applied AI project because it uses a pretrained computer vision model in a real interaction workflow. MediaPipe detects hand landmarks from camera frames. The application layer then classifies gestures, smooths noisy predictions, applies safety rules, and maps stable gestures to useful computer actions.

The base hand landmark model was not trained from scratch. The engineering work is in integrating the model and building the decision layer that makes the predictions practical, responsive, and safe.

## Testing

```powershell
pytest
```

Current test coverage includes gesture classification, action handling, calibration, event logging, media utilities, sharing, and app behavior.

## Demo Materials

- [Demo guide](docs/DEMO_GUIDE.md)
- [Project explanation](docs/PROJECT_EXPLANATION.md)
- [Presentation frontend](frontend/index.html)

## Resume Summary

Built a real-time gesture-controlled computer interaction system using OpenCV and MediaPipe, enabling cursor movement, volume control, shortcuts, browser actions, presentation control, and QR-based local file transfer. Engineered gesture classification, temporal smoothing, calibration, safety locks, event logging, and Windows packaging for a reliable Applied AI user experience.
