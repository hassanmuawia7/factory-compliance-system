import cv2
import json
import numpy as np
import os

# ==========================
# CONFIG
# ==========================

IMAGE_PATH = "outputs/raw_frame.jpg"
OUTPUT_PATH = "outputs/zones.json"

# ==========================
# LOAD EXISTING DATA
# ==========================

if os.path.exists(OUTPUT_PATH):

    with open(OUTPUT_PATH, "r") as f:
        zones_data = json.load(f)

else:

    zones_data = {
        "walkway_zone": [],
        "machinery_zones": {}
    }

# ==========================
# STATE
# ==========================

points = []

mode = "walkway"

machine_counter = (
    len(
        zones_data.get(
            "machinery_zones",
            {}
        )
    ) + 1
)

# ==========================
# LOAD IMAGE
# ==========================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Could not load image.")
    exit()

# ==========================
# MOUSE CALLBACK
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
print("1 = Recalibrate Walkway")
print("2 = Recalibrate Machines")
print("S = Save Current Zone")
print("R = Reset Current Points")
print("Q = Quit ")

# ==========================
# MAIN LOOP
# ==========================

while True:

    display = image.copy()

    # ==================================
    # DRAW EXISTING WALKWAY
    # ==================================

    walkway = zones_data.get(
        "walkway_zone",
        []
    )

    if len(walkway) >= 3:

        cv2.polylines(
            display,
            [np.array(walkway, dtype=np.int32)],
            True,
            (0, 255, 0),
            3
        )

    # ==================================
    # DRAW EXISTING MACHINES
    # ==================================

    machinery = zones_data.get(
        "machinery_zones",
        {}
    )

    for machine_name, zone in machinery.items():

        zone_np = np.array(
            zone,
            dtype=np.int32
        )

        cv2.polylines(
            display,
            [zone_np],
            True,
            (0, 0, 255),
            2
        )

        x, y = zone_np[0]

        cv2.putText(
            display,
            machine_name,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

    # ==================================
    # DRAW CURRENT POLYGON
    # ==================================

    if len(points) > 0:

        for point in points:

            cv2.circle(
                display,
                point,
                5,
                (0, 255, 255),
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

    # ==================================
    # SEMI-TRANSPARENT MENU
    # ==================================

    overlay = display.copy()

    cv2.rectangle(
        overlay,
        (10, 10),
        (420, 330),
        (0, 0, 0),
        -1
    )

    alpha = 0.55

    cv2.addWeighted(
        overlay,
        alpha,
        display,
        1 - alpha,
        0,
        display
    )

    menu_lines = [
        "ZONE CALIBRATION TOOL",
        "",
        "1 : Recalibrate Walkway",
        "2 : Recalibrate Machines",
        "",
        "S : Save Current Zone",
        "R : Reset Current Polygon",
        "Q : Quit ",
        "",
        f"Mode : {mode.upper()}",
        f"Machine Index : {machine_counter}"
    ]

    y = 40

    for line in menu_lines:

        cv2.putText(
            display,
            line,
            (25, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        y += 28

    # ==================================
    # DISPLAY
    # ==================================

    cv2.imshow(
        "Zone Selector",
        display
    )

    key = cv2.waitKey(1) & 0xFF

    # ==================================
    # WALKWAY MODE
    # ==================================

    if key == ord("1"):

        mode = "walkway"

        points = []

        print("\n➡ WALKWAY RECALIBRATION")

    # ==================================
    # MACHINE MODE
    # ==================================

    elif key == ord("2"):

        mode = "machine"

        points = []

        zones_data["machinery_zones"] = {}

        machine_counter = 1

        print(
            "\n🗑 Old machine zones cleared"
        )

        print(
            "➡ MACHINE RECALIBRATION STARTED"
        )

    # ==================================
    # SAVE
    # ==================================

    elif key == ord("s"):

        if len(points) < 3:

            print(
                "⚠ Need at least 3 points"
            )

            continue

        if mode == "walkway":

            zones_data[
                "walkway_zone"
            ] = points.copy()

            print(
                "✅ Walkway Saved"
            )

        elif mode == "machine":

            zones_data[
                "machinery_zones"
            ][
                f"machine_{machine_counter}"
            ] = points.copy()

            print(
                f"✅ machine_{machine_counter} Saved"
            )

            machine_counter += 1

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
            "💾 zones.json updated"
        )

        points = []

    # ==================================
    # RESET
    # ==================================

    elif key == ord("r"):

        points = []

        print(
            "🔄 Current polygon cleared"
        )

    # ==================================
    # QUIT
    # ==================================

    elif key == ord("q"):

        print(
            "\n👋 Exiting"
        )

        break

cv2.destroyAllWindows()