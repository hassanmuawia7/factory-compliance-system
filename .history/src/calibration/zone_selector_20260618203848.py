import cv2
import json
import numpy as np

points = []
image = cv2.imread("outputs/frame.jpg")

if image is None:
    print("❌ ERROR: Could not find outputs/frame.jpg. Run extract_frame.py first!")
    exit()

def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point added: ({x}, {y})")

# --- THE FIX 1: Screen Fit ---
cv2.namedWindow("Zone Selector", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Zone Selector", 1280, 720)

# --- THE FIX 2: Set Callback ONCE outside the loop ---
cv2.setMouseCallback("Zone Selector", mouse_callback)

print("🖱️  Click points to outline the Walkway.")
print("💾 Press 's' to save. Press 'r' to reset. Press 'q' to quit.")

while True:
    display = image.copy()

    # Draw points
    for point in points:
        cv2.circle(display, point, 5, (0, 0, 255), -1)

    # Draw polygon if enough points exist
    if len(points) > 1:
        cv2.polylines(display, [np.array(points)], True, (0, 255, 255), 2)

    cv2.imshow("Zone Selector", display)

    key = cv2.waitKey(1)

    # Save
    if key == ord("s"):
        if len(points) >= 3:
            zone_data = {
                "walkway_zone": points
            }
            with open("outputs/zones.json", "w") as f:
                json.dump(zone_data, f, indent=4)
            print("✅ Zone saved to outputs/zones.json")
            break
        else:
            print("⚠️ You need at least 3 points to make a zone!")

    # Reset
    elif key == ord("r"):
        points = []
        print("Points cleared")

    # Quit
    elif key == ord("q"):
        break

cv2.destroyAllWindows()