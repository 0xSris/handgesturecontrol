# Project Explanation

## Short Explanation

I built a real-time hand gesture recognition system that uses a webcam to control computer actions. It detects hand landmarks, classifies gestures, smooths noisy predictions, and maps gestures to useful actions like cursor movement, volume control, shortcuts, browser control, presentation navigation, and file sharing.

## Can This Be Included In Applied AI?

Yes. This is an Applied AI project because it uses an AI computer vision model in a practical real-world workflow.

The important wording is:

"I integrated a pretrained computer vision model and engineered an application layer around it to turn hand landmark predictions into real computer interactions."

## Did I Train The Model?

No, I did not train the base model from scratch.

The project uses MediaPipe's pretrained hand landmark model. That model detects 21 keypoints on the hand in real time. My work was to build the system around it:

- Capturing webcam frames with OpenCV.
- Running hand landmark detection.
- Classifying gestures from landmark geometry.
- Smoothing labels so actions do not flicker.
- Mapping gestures to OS actions.
- Adding calibration, lock/unlock safety, file sharing, QR transfer, logs, screenshots, recordings, and a Windows executable.

## Strong Interview Answer

"I did not train a neural network from scratch because the goal was practical interaction, not dataset collection. I used a pretrained MediaPipe hand landmark model, then built the applied AI layer: gesture recognition logic, temporal smoothing, confidence thresholds, calibration, and automation. This shows I can integrate AI predictions into a usable product."

## Technical Breakdown

Camera input comes from OpenCV. MediaPipe detects 21 hand landmarks. I calculate distances and finger states, such as thumb-index pinch distance, raised fingers, and palm state. These are classified into gestures like point, pinch, peace, open palm, fist, and three fingers.

The action engine uses cooldowns and smoothing so a gesture must be stable before it triggers a real action. Different modes reuse the same gestures for different tasks: cursor mode, volume mode, shortcut mode, media mode, browser mode, presentation mode, and share mode.

## Resume Version

Built a real-time gesture-controlled computer interaction system using OpenCV and MediaPipe, enabling cursor movement, volume control, shortcuts, browser actions, presentation control, and QR-based local file transfer. Engineered gesture classification, smoothing, calibration, safety locks, event logging, and Windows packaging for a reliable applied AI user experience.
