"""
debug_camera.py
Run this ONCE to diagnose face detection issues:
    python debug_camera.py

It will:
  - Try camera indexes 0, 1, 2
  - Save a raw frame as  debug_raw.jpg
  - Save a face-annotated frame as  debug_faces.jpg
  - Print how many faces were detected and their sizes
"""

import cv2

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def try_camera(index):
    print(f"\n--- Trying camera index {index} ---")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # CAP_DSHOW works better on Windows
    if not cap.isOpened():
        print(f"  Camera {index}: could not open")
        cap.release()
        return False

    # Warm up: skip first 10 frames
    for i in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"  Camera {index}: opened but could not read frame")
        return False

    h, w = frame.shape[:2]
    print(f"  Camera {index}: frame size = {w}x{h}")

    # Save raw frame
    raw_path = f"debug_raw_cam{index}.jpg"
    cv2.imwrite(raw_path, frame)
    print(f"  Saved raw frame -> {raw_path}")

    # Run detection with lenient settings
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_eq = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray_eq,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(30, 30),
    )

    print(f"  Faces detected: {len(faces)}")
    for (x, y, w, h) in faces:
        print(f"    Face at ({x},{y}), size {w}x{h}")
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    annotated_path = f"debug_faces_cam{index}.jpg"
    cv2.imwrite(annotated_path, frame)
    print(f"  Saved annotated frame -> {annotated_path}")
    return True

if __name__ == "__main__":
    found_any = False
    for idx in range(3):
        found_any = try_camera(idx) or found_any

    if not found_any:
        print("\nNo working cameras found at indexes 0-2.")
    else:
        print("\nDone! Open the debug_raw_camX.jpg files to see what OpenCV captured.")
        print("If you see your face clearly in the raw image but NOT in debug_faces, ")
        print("the detection params need further tuning.")
        print("If the raw image is BLACK or BLANK, it is a camera access/index issue.")
