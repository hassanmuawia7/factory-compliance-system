import cv2
import os
import numpy as np
from ultralytics import YOLO

video_path = "data/videos/test.mp4"

# 1. Explicitly check if the file exists before doing anything
print(f"Checking for video at: {os.path.abspath(video_path)}")

if not os.path.exists(video_path):
    print("❌ ERROR: Video file not found! Please check the folder and file name.")
    exit()

# 2. Load the model
print("Loading YOLO model...")
model = YOLO("yolov8n.pt")
print("✅ YOLO loaded successfully!")

# 3. Open the video
cap = cv2.VideoCapture(video_path)
cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("YOLO Detection", 1280, 720)

# --- THE POLYGON COORDINATES ---
SAFE_ZONE = np.array([
    [1380, 0],
    [1920, 0],
    [1920, 1080],
    [1650, 1080]
], np.int32)

if not cap.isOpened():
    print("❌ ERROR: OpenCV found the file, but cannot open it (might be corrupted).")
    exit()

print("✅ Video playing! Press 'q' on your keyboard to stop.")

# 4. Process the frames
while cap.isOpened():
    success, frame = cap.read()

    if not success:
        print("End of video reached.")
        break

    # Run YOLO detection
    results = model(frame, classes=[0])

    # Draw boxes on the frame
    annotated_frame = results[0].plot()

    # Show the frame
    cv2.imshow("YOLO Detection", annotated_frame)

    # Wait for the 'q' key to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("User stopped the video.")
        break

# Clean up
cap.release()
cv2.destroyAllWindows()