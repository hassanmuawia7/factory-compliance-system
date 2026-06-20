import cv2
import json
import numpy as np

# ==========================
# CONFIG
# ==========================

IMAGE_PATH = "outputs/frame.jpg"
OUTPUT_PATH = "outputs/zones.json"

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

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Could not load image.")
    exit()

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

cv2.namedWindow(
    "Zone Selector",
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    "Zone Selector",
    1280,
    720
)

cv2.setMouseCallback(
    "Zone Selector",
    mouse_callback
)

# ==========================
# HELP
# ==========================

print("\n===== ZONE CALIBRATION TOOL =====")

print("1 = Walkway Mode")
print("2 = Machine Mode")
print("S = Save Current Zone")
print("R = Reset Current Points")
print("N = New Machine")
print("Q = Save All & Quit")

# ==========================
# LOOP
# ==========================

while True:

    display = image.copy()

    title = f"Mode: {mode.upper()}"

    cv2.putText(
        display,
        title,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    # Draw current points

    for point in points:

        cv2.circle(
            display,
            point,
            5,
            (0, 0, 255),
            -1
        )

    if len(points) > 1:

        cv2.polylines(
            display,
            [np.array(points)],
            True,
            (0, 255, 255),
            2
        )

    cv2.imshow(
        "Zone Selector",
        display
    )

    key = cv2.waitKey(1) & 0xFF

    # ======================
    # WALKWAY MODE
    # ======================

    if key == ord("1"):

        mode = "walkway"

        points = []

        print("\n➡ Walkway Mode")

    # ======================
    # MACHINE MODE
    # ======================

    elif key == ord("2"):

        mode = "machine"

        points = []

        print(
            f"\n➡ Machine Mode (machine_{machine_counter})"
        )

    # ======================
    # SAVE
    # ======================

    elif key == ord("s"):

        if len(points) < 3:

            print(
                "⚠ Need at least 3 points."
            )

            continue

        if mode == "walkway":

            zones_data[
                "walkway_zone"
            ] = points.copy()

            print(
                "✅ Walkway saved"
            )

        elif mode == "machine":

            zones_data[
                "machinery_zones"
            ][
                f"machine_{machine_counter}"
            ] = points.copy()

            print(
                f"✅ machine_{machine_counter} saved"
            )

        points = []

    # ======================
    # RESET
    # ======================

    elif key == ord("r"):

        points = []

        print("🔄 Points cleared")

    # ======================
    # NEXT MACHINE
    # ======================

    elif key == ord("n"):

        if mode == "machine":

            machine_counter += 1

            points = []

            print(
                f"➡ Switched to machine_{machine_counter}"
            )

    # ======================
    # QUIT
    # ======================

    elif key == ord("q"):

        with open(
            OUTPUT_PATH,
            "w"
        ) as f:

            json.dump(
                zones_data,
                f,
                indent=4
            )

        print(
            f"\n💾 Saved to {OUTPUT_PATH}"
        )

        break

cv2.destroyAllWindows()