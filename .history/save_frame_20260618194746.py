import cv2

cap = cv2.VideoCapture(
    "data/videos/test.mp4"
)

success, frame = cap.read()

if success:
    cv2.imwrite(
        "outputs/frame.jpg",
        frame
    )

cap.release()