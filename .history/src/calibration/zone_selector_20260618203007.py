import cv2
import json
import numpy as np

points = []

image = cv2.imread("outputs/frame.jpg")
# --- THE FIX FOR SCREEN SIZING ---
# Create a window that allows resizing, then set it to 720p
cv2.resizeWindow( 1280, 720)

def mouse_callback(event, x, y, flags, param):

    global points

    if event == cv2.EVENT_LBUTTONDOWN:

        points.append((x, y))

        print(f"Point added: ({x}, {y})")

while True:

    display = image.copy()

    # Draw points
    for point in points:

        cv2.circle(
            display,
            point,
            5,
            (0, 0, 255),
            -1
        )

    # Draw polygon if enough points
    if len(points) > 1:

        cv2.polylines(
            display,
            [np.array(points)],
            False,
            (0,255,255),
            2
        )

    cv2.imshow(
        "Zone Selector",
        display
    )

    cv2.setMouseCallback(
        "Zone Selector",
        mouse_callback
    )

    key = cv2.waitKey(1)

    # Save
    if key == ord("s"):

        zone_data = {
            "walkway_zone": points
        }

        with open(
            "outputs/zones.json",
            "w"
        ) as f:

            json.dump(
                zone_data,
                f,
                indent=4
            )

        print(
            "Zone saved to outputs/zones.json"
        )

        break

    # Reset
    elif key == ord("r"):

        points = []

        print("Points cleared")

    # Quit
    elif key == ord("q"):

        break

cv2.destroyAllWindows()