import cv2
import numpy as np
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

video_path = "data/videos/test.mp4"

# Walkway polygon
SAFE_ZONE = np.array([
    [780, 0],
    [1000, 0],
    [1000, 570],
    [780, 570]
], dtype=np.int32)

cap = cv2.VideoCapture(video_path)

while True:

    success, frame = cap.read()

    if not success:
        break

    results = model(frame)

    # Draw walkway zone
    cv2.polylines(
        frame,
        [SAFE_ZONE],
        True,
        (0,255,255),
        3
    )

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            class_name = model.names[class_id]

            if class_name != "person":
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Draw center point
            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                (255,0,0),
                -1
            )

            inside = cv2.pointPolygonTest(
                SAFE_ZONE,
                (center_x, center_y),
                False
            )

            # SAFE
            if inside >= 0:

                color = (0,255,0)

                label = "SAFE"

            # VIOLATION
            else:

                color = (0,0,255)

                label = "WALKWAY VIOLATION"

            cv2.rectangle(
                frame,
                (x1,y1),
                (x2,y2),
                color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

    cv2.imshow(
        "Walkway Detector",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()