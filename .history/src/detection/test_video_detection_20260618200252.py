import cv2
import numpy as np
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

video_path = "data/videos/test.mp4"
cap = cv2.VideoCapture(video_path)

# --- THE FIX FOR SCREEN SIZING ---
# Create a window that allows resizing, then set it to 720p
cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("YOLO Detection", 1280, 720)

# --- THE POLYGON COORDINATES ---
SAFE_ZONE = np.array([
    [1380, 0],
    [1920, 0],
    [1920, 1080],
    [1650, 1080]
], np.int32)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # --- THE FIX FOR THE "TRUCKS" ---
    # classes=[0] forces YOLO to ONLY detect 'person'
    results = model(frame, classes=[0])
    
    # Plot the YOLO bounding boxes
    annotated_frame = results[0].plot()

    # --- DRAW THE SAFE ZONE ---
    # We draw a thick green line so you can see where the computer thinks the walkway is
    cv2.polylines(annotated_frame, [SAFE_ZONE], isClosed=True, color=(0, 255, 0), thickness=4)

    cv2.imshow("YOLO Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()