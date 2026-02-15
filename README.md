##  Face Detection Brightness Controller API
<br>
A Python-based computer vision project that detects human faces using OpenCV and automatically adjusts laptop screen brightness.

It also exposes a FastAPI endpoint so the detection system can be triggered via a custom API.
<br>


##  Features
<br>

* Real-time face detection using Haar Cascade
* Automatic screen brightness adjustment
* Brightness ON when faces detected
* Brightness OFF when no faces detected
* FastAPI integration for API access
* Lightweight and hardware-aware automation

<br>

##  Project Logic

<br>
Webcam → Frame Capture → Face Detection → Face Count → Brightness Control
<br>

Brightness Rules:

| Faces Detected | Brightness |
| -------------- | ---------- |
| ≥ 1 Face       | 100%       |
| 0 Face         | 0%         |

<br>

##  Project Structure

<br>
project/
│
├── logic.py       
├── custom_api.py 
├── requirements.txt
└── README.md
<br>


## ⚙️ Installation

###  Clone Repository

<br>
bash
git clone https://github.com/your-username/face-brightness-controller.git
cd face-brightness-controller
<br>

###  Create Virtual Environment

<br>
bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
<br>

###  Install Dependencies

<br>bash
pip install -r requirements.txt
<br>

Or manually:

<br>bash
pip install opencv-python screen-brightness-control fastapi uvicorn
<br>

## Running the API Server

<br>bash
uvicorn custom_api:app --reload
<br>

Server runs at:

<br>
http://127.0.0.1:8000
<br>


##  API Endpoints

### Root Check

<br>
GET /
<br>

Response:

<br>json
{
  "message": "Face Brightness Controller Running"
}
<br>

---

### Face Detection + Brightness Trigger

<br>
GET /check-faces
<br>

Response:

<br>json
{
  "faces_detected": 1,
  "brightness_set": 100
}
<br>

---

##  How It Works

### logic.py

* Captures frame from webcam
* Converts to grayscale
* Detects faces using Haar Cascade
* Counts faces
* Adjusts brightness via `screen_brightness_control`

### custom_api.py

* Exposes FastAPI endpoints
* Calls `process_frame()` from logic layer
* Returns JSON response








