# Troubleshooting

## Gestures show correctly, but actions do not fire

Start with debug mode:

```powershell
python -m gesture_control --camera -1 --profile config/default_profile.json --show-debug
```

Check these overlay fields:

- `Gesture`: smoothed label for readability.
- `Action gesture`: raw label used for controls.
- `Pinch i/m`: thumb-index and thumb-middle distances.
- `Fingers`: thumb, index, middle, ring, pinky as `1` or `0`.

If `Gesture` changes but `Action gesture` does not, lower `--action-confidence`.

If pinch never appears, increase:

```powershell
python -m gesture_control --pinch-threshold 0.095 --middle-pinch-threshold 0.095 --show-debug
```

## Keyboard rescue controls

Use these while the camera window is focused:

```text
u  unlock controls
l  lock controls
c  cursor mode
v  volume mode
x  shortcuts mode
m  media mode
b  browser mode
p  presentation mode
h  share mode
t  toggle share server
s  snapshot
q  quit
```

## Create demo evidence

Record a short demo with both video and action metrics:

```powershell
python -m gesture_control --camera -1 --record-output recordings/demo.mp4 --event-log logs/events.csv --show-debug
```

The video shows the UI, while `logs/events.csv` lists the recognized gesture, triggered action, mode, and timestamp.

## Browser mode only shows actions

Browser mode needs real actions enabled:

```powershell
python -m gesture_control --camera -1 --enable-actions --browser-home-url https://www.google.com
```

Point/peace open the default browser first. After the browser is focused, pinch and middle-pinch can close or reopen tabs.

## Share files to phone or another PC

Start with a folder:

```powershell
python -m gesture_control --camera -1 --enable-actions --share-path "C:\Users\Srishti Pandey\Downloads"
```

Put your phone/other PC on the same Wi-Fi and open the URL shown in the overlay. If the page does not load, allow Python/GestureControl through Windows Firewall for private networks.

## Cursor works in preview, but does not move in Windows

Run with real actions enabled:

```powershell
python -m gesture_control --enable-actions --camera -1 --profile config/default_profile.json
```

Keep the mouse away from screen corners. PyAutoGUI intentionally stops when the pointer hits a corner.

## Build a Windows executable

After the model exists at `models/hand_landmarker.task`, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

The executable is written to `dist/GestureControl/GestureControl.exe`.
