import cv2
import screen_brightness_control as sbc

# Primary + alternate frontal cascades
frontal_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)
alt_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
)


def _count_faces(gray_eq):
    """Return the face count agreed upon by both cascades (reduces false positives)."""
    faces1 = frontal_cascade.detectMultiScale(
        gray_eq,
        scaleFactor=1.1,
        minNeighbors=5,       # strict enough to avoid false positives
        minSize=(60, 60),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    faces2 = alt_cascade.detectMultiScale(
        gray_eq,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    # Only count a face if at least ONE of the cascades confirms it
    count1 = len(faces1) if len(faces1) > 0 else 0
    count2 = len(faces2) if len(faces2) > 0 else 0
    return max(count1, count2)


def process_frame():
    cap = cv2.VideoCapture(0)

    try:
        # Warm up — let auto-exposure settle (discard 20 frames)
        for _ in range(20):
            cap.read()

        # Sample 3 frames and take the most common result (majority vote)
        votes = []
        for _ in range(3):
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            votes.append(_count_faces(gray))

        if not votes:
            return {"error": "Camera not accessible"}

        # Use the maximum detected across 3 frames
        # (if even one frame sees a face, you are probably there)
        face_count = max(votes)

        brightness = 100 if face_count >= 1 else 0
        sbc.set_brightness(brightness)

        return {
            "faces_detected": face_count,
            "brightness_set": brightness,
        }

    finally:
        cap.release()