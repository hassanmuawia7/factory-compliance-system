import cv2
import json
import os

# Globals to hold our points and the image frame
points = []
frame_copy = None
window_name = "Zone Calibration (Click 4 points, Press 's' to save, 'q' to quit)"

def mouse_click(event, x, y, flags, param):
    global points, frame_copy
    
    # Listen for Left Mouse Button clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point registered: ({x}, {y})")
        
        # Draw a visual dot where the user clicked
        cv2.circle(frame_copy, (x, y), 5, (0, 255, 0), -1)
        
        # Draw lines connecting the points
        if len(points) > 1:
            cv2.line(frame_copy, points[-2], points[-1], (0, 255, 0), 2)
            
        # Automatically close the polygon if 4 points are clicked
        if len(points) == 4:
            cv2.line(frame_copy, points[-1], points[0], (0, 255, 0), 2)
            print("Polygon closed! Press 's' to save.")
            
        cv2.imshow(window_name, frame_copy)

def main():
    global frame_copy
    os.makedirs("outputs", exist_ok=True)
    
    video_path = "data/videos/test.mp4"
    print(f"Opening video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()

    if not success:
        print("❌ ERROR: Could not read video. Check the path.")
        return

    # Create a copy of the frame to draw on
    frame_copy = frame.copy()
    
    # Set up the OpenCV window
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    # Bind our mouse click function to the window
    cv2.setMouseCallback(window_name, mouse_click)

    print("\n--- CALIBRATION INSTRUCTIONS ---")
    print("🖱️  Click 4 points on the image to outline the Walkway Zone.")
    print("💾 Press 's' to save the zone to JSON.")
    print("❌ Press 'q' to exit without saving.\n")

    cv2.imshow(window_name, frame_copy)

    # Main loop listening for keystrokes
    while True:
        key = cv2.waitKey(1) & 0xFF
        
        # 's' to save
        if key == ord("s"):
            if len(points) >= 3:
                zone_data = {"walkway_zone": points}
                with open("outputs/zones.json", "w") as f:
                    json.dump(zone_data, f, indent=4)
                print(f"✅ SUCCESS: Zone saved to outputs/zones.json")
            else:
                print("⚠️ You need to click at least 3 points to make a zone!")
            break
            
        # 'q' to quit
        elif key == ord("q"):
            print("Exiting without saving.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()