# Face Detection Brightness Controller

A Python computer vision project that watches your webcam, detects faces, and automatically adjusts your laptop screen brightness. Comes with a FastAPI backend and a browser-based Solara frontend for end-to-end use.

---

## Features

- Real-time face detection via OpenCV Haar Cascade
- Automatic screen brightness adjustment (100% when face detected, 0% when nobody is there)
- FastAPI backend exposing clean REST endpoints
- Solara browser UI — start/stop monitoring with one click, live status badge, brightness bar

---

## How It Works

```
Webcam  →  Frame Capture  →  Face Detection  →  Face Count  →  Brightness Control
```

| Faces Detected | Brightness Set |
| -------------- | -------------- |
| 1 or more      | 100%           |
| 0              | 0%             |

---

## Project Structure

```
Camera_model/
├── logic.py          # Core: webcam capture, face detection, brightness control
├── custom_api.py     # FastAPI backend exposing /check-faces endpoint
├── app.py            # Solara browser frontend
├── requirement.txt   # Python dependencies
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/keshavmishra27/Camera_model.git
cd Camera_model
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirement.txt
```

---

## Running the App

You need **two terminals** running at the same time.

### Terminal 1 — Start the backend

```bash
uvicorn custom_api:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

### Terminal 2 — Start the frontend

```bash
solara run app.py
```

Frontend runs at: `http://localhost:8765`

Open that URL in your browser to use the dashboard.

---

## Using the Dashboard

1. Click **Start Monitoring** — the app will begin checking your webcam every 3 seconds
2. Your screen brightness adjusts automatically based on face detection
3. **Uncheck the checkbox** (shown while monitoring is active) to stop

---

## API Endpoints

### `GET /`

Health check.

```json
{ "message": "Face Brightness Controller Running" }
```

### `GET /check-faces`

Captures a webcam frame, runs face detection, sets brightness, and returns the result.

```json
{
  "faces_detected": 1,
  "brightness_set": 100
}
```

---

## File Details

### `logic.py`
- Opens webcam, reads one frame
- Converts to grayscale
- Detects faces using Haar Cascade classifier
- Counts faces and sets brightness via `screen_brightness_control`

### `custom_api.py`
- FastAPI app with two endpoints (`/` and `/check-faces`)
- Calls `process_frame()` from `logic.py` and returns JSON

### `app.py`
- Solara frontend rendered in the browser
- Reactive state (face count, brightness, status)
- Background thread polls `/check-faces` every 3 seconds when monitoring is enabled
- Components: status badge, brightness bar, stat cards, error banner
