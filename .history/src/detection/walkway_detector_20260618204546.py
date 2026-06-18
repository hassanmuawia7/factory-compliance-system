import cv2
import json
import numpy as np
from datetime import datetime
from ultralytics import YOLO

def load_configs():
    # Load your dynamically generated polygon
    with open("outputs/zones.json", "r") as f:
        zones = json.load(f)
    
    # Load your LLM-extracted rules
    with open("outputs/validated_rules.json", "r") as f:
        rules = json.load(f)
        
    return np.array(zones["walkway_zone"], dtype=np.int32), rules["walkway_violation"]

def generate_event(rule_data):
    # This is the exact format required by the internship prompt (Module 4)
    event = {
        "event_id": f"EVT-{datetime.now().strftime('%Y%M%d%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "behavior_class": "walkway_violation",
        "policy_rule_ref": rule_data["policy_reference"],
        "severity": rule_data["severity_hint"],
        "description": f"Detected: {rule_data['observable_indicator']}"
    }
    return event

def main():
    print("Loading configurations...")
    SAFE_ZONE, walkway_rule = load_configs()
    
    print("Loading YOLO...")
    model = YOLO("yolov8n.pt")
    
    cap = cv2.VideoCapture("data/videos/test.mp4")
    
    cv2.namedWindow("Compliance Monitor", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Compliance Monitor", 1280, 720)

    # Flag to prevent spamming the console with thousands of the same event
    violation_active = False 

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Draw our custom Safe Zone on the frame
        cv2.polylines(frame, [SAFE_ZONE], isClosed=True, color=(0, 255, 0), thickness=3)

        # Detect only people (class 0)
        results = model(frame, classes=[0], verbose=False)
        
        current_frame_violation = False

        for box in results[0].boxes:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # PRO-TIP: Calculate Bottom-Center (Feet) instead of pure center
            feet_x = int((x1 + x2) / 2)
            feet_y = int(y2)
            
            # Test if feet are inside the polygon (returns > 0 if inside, < 0 if outside)
            distance = cv2.pointPolygonTest(SAFE_ZONE, (feet_x, feet_y), measureDist=False)
            
            if distance >= 0:
                # SAFE: Draw a green box and green dot at their feet
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (feet_x, feet_y), 5, (0, 255, 0), -1)
            else:
                # VIOLATION: Draw a red box and red dot
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(frame, (feet_x, feet_y), 5, (0, 0, 255), -1)
                cv2.putText(frame, "VIOLATION!", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                current_frame_violation = True
                
        # Event Logging Logic (Print once per violation entrance)
        if current_frame_violation and not violation_active:
            violation_active = True
            print("\n🚨 NEW VIOLATION DETECTED 🚨")
            print(json.dumps(generate_event(walkway_rule), indent=4))
            
        elif not current_frame_violation and violation_active:
            # They stepped back into the safe zone
            violation_active = False

        cv2.imshow("Compliance Monitor", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()