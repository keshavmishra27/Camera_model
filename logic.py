import cv2
import screen_brightness_control as sbc

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0)

def process_frame():
    ret, frame = cap.read()
    if not ret:
        return {"error": "Camera not accessible"}

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(30, 30)
    )

    face_count = len(faces)

    
    if face_count >= 1:
        brightness = 100
    elif face_count == 0:
        brightness = 0
    else:
        brightness = 50

    sbc.set_brightness(brightness)

    return {
        "faces_detected": face_count,
        "brightness_set": brightness
    }