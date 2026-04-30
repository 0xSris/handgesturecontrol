# Demo Guide

## Before You Start

Use one exact file for the phone transfer demo. Keep the phone and laptop on the same Wi-Fi.

```powershell
python -m gesture_control --camera -1 --enable-actions --profile config/my_profile.json --share-path "C:\Users\Srishti Pandey\Downloads\demo.pdf" --show-debug --ui-scale 0.5
```

## Simple Demo Flow

1. Start with the frontend page and say: "This is a real-time hand gesture control system built with computer vision."
2. Open the Python app and show the camera overlay.
3. Show open palm: "Open palm unlocks the controls."
4. Point with index finger: "Pointing moves the cursor."
5. Pinch once: "Pinch performs a click."
6. Show three fingers: "Three fingers changes the control mode."
7. Switch to volume mode with `v` if gesture mode switching is not stable in front of the audience.
8. Move thumb and index closer/farther: "This changes system volume."
9. Press `h` for share mode.
10. Show the QR code and scan it with your phone: "This transfers the file over local Wi-Fi."
11. End with: "The main challenge was making live predictions reliable enough for real actions."

## Safety Line

"Because this controls the actual computer, I added preview mode, lock/unlock, cooldowns, smoothing, and hold-fist-to-lock safety."

## If Something Goes Wrong

- Press `u` to unlock.
- Press `l` to lock.
- Press `c`, `v`, `x`, `m`, `b`, `p`, or `h` to force a mode.
- Press `t` to restart the share server.
- Press `q` or `Esc` to exit.
