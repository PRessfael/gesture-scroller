# Lazy Scroller

Lazy Scroller is a hands-free desktop scrolling tool that uses a webcam and MediaPipe hand tracking to control page scrolling with index and middle finger gestures.

## Features

- Scroll down with an upward index-finger gesture
- Scroll up with a downward index-finger gesture
- Scroll up using the middle finger
- Speed-based scroll distance
- Live webcam preview with tracked hand landmarks
- Always-on-top control window

## Technologies

- Python
- OpenCV
- MediaPipe
- PyAutoGUI

## Installation

From the project directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install opencv-python mediapipe pyautogui
```

## Usage

```bash
python gesture-scroll.py
```

- Move the tracked finger up or down to trigger scrolling.
- Press `q` to close the application.

## Notes

- A webcam is required.
- OpenCV and MediaPipe must be able to access the camera.
- The script sends scroll commands to the currently active application.
