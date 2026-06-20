import cv2
import json
import numpy as np
import os

# ==========================
# CONFIG
# ==========================
IMAGE_PATH = "outputs/raw_frame.jpg"
OUTPUT_PATH = "outputs/zones.json"

MACHINE_COLORS = [(0, 0, 255), (255, 0, 0), (0, 255, 255), (255, 0, 255), (0, 165, 255)]

# ==========================
# STATE
# ==========================
points = []
mode = "walkway"
machine_counter = 1
zones_data = {
    "walkway_zone": [],
    "machinery_zones": {}
}

# ==========================
# LOAD IMAGE
# ==========================
if not os.path.exists(IMAGE_PATH):
    print(f"❌ Could not load image. Missing {IMAGE_PATH}")
    exit()

image = cv2.imread(IMAGE_PATH)

# ==========================
# MOUSE
# ==========================
def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point added: ({x}, {y})")

# ==========================
# WINDOW
# ==========================
cv2.namedWindow("Zone Selector", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Zone Selector", 1280, 720)
cv2.setMouseCallback("Zone Selector", mouse_callback)

# ==========================
# LOOP
# ==========================
while True:
    display = image.copy()

    # -----------------------------------------
    # 1. DRAW SAVED ZONES (PERSISTENT)
    # -----------------------------------------
    # Walkway
    if zones_data["walkway_zone"]:
        pts = np.array(zones_data["walkway_zone"], np.int32)
        cv2.polylines(display, [pts], True, (0, 255, 0), 3)
        cv2.putText(display, "Walkway", (int(pts[0][0]), int(pts[0][1]) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Machinery
    for idx, (m_name, m_pts) in enumerate(zones_data["machinery_zones"].items()):
        color = MACHINE_COLORS[idx % len(MACHINE_COLORS)]
        pts = np.array(m_pts, np.int32)
        cv2.polylines(display, [pts], True, color, 3)
        cv2.putText(display, m_name, (int(pts[0][0]), int(pts[0][1]) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # -----------------------------------------
    # 2. DRAW CURRENT POINTS
    # -----------------------------------------
    active_color = (255, 255, 0) if mode == "walkway" else (0, 165, 255)
    for point in points:
        cv2.circle(display, point, 5, active_color, -1)

    if len(points) > 1:
        cv2.polylines(display, [np.array(points)], False, active_color, 2)

    # -----------------------------------------
    # 3. ON-SCREEN HUD / MENU
    # -----------------------------------------
    cv2.rectangle(display, (10, 10), (380, 280), (0, 0, 0), -1)

    title_color = (0, 255, 0) if mode == "walkway" else (0, 0, 255)
    cv2.putText(display, f"Mode: {mode.upper()}", (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, title_color, 2)

    menu_lines = [
        "1 : Walkway Mode",
        "2 : Machine Mode",
        "S : Save Current Zone",
        "R : Reset Current Points",
        "N : Skip to Next Machine",
        "Q : Save All & Quit"
    ]

    y = 90
    for line in menu_lines:
        cv2.putText(display, line, (20, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 35

    if mode == "machine":
        cv2.putText(display, f"Next: machine_{machine_counter}", (20, 260), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Zone Selector", display)

    key = cv2.waitKey(1) & 0xFF

    # ======================
    # CONTROLS
    # ======================
    if key == ord("1"):
        mode = "walkway"
        points = []
        print("\n➡ Walkway Mode")

    elif key == ord("2"):
        mode = "machine"
        points = []
        print(f"\n➡ Machine Mode (machine_{machine_counter})")

    elif key == ord("s"):
        if len(points) < 3:
            print("⚠ Need at least 3 points.")
            continue

        if mode == "walkway":
            zones_data["walkway_zone"] = points.copy()
            print("✅ Walkway saved")

        elif mode == "machine":
            zones_data["machinery_zones"][f"machine_{machine_counter}"] = points.copy()
            print(f"✅ machine_{machine_counter} saved")
            machine_counter += 1
            print(f"➡ Ready for machine_{machine_counter}")
        
        points = []

    elif key == ord("r"):
        points = []
        print("🔄 Points cleared")

    elif key == ord("n"):
        if mode == "machine":
            machine_counter += 1
            points = []
            print(f"➡ Switched to machine_{machine_counter}")

    elif key == ord("q"):
        with open(OUTPUT_PATH, "w") as f:
            json.dump(zones_data, f, indent=4)
        print(f"\n💾 Saved to {OUTPUT_PATH}")
        break

cv2.destroyAllWindows()