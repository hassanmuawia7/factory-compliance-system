import sys
import os
# Force Python to see the root project folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import cv2
import json
import numpy as np
import time
from datetime import datetime
from ultralytics import YOLO

def load_configs():
    with open("outputs/zones.json", "r") as f:
        zones = json.load(f)
    
    with open("outputs/validated_rules.json", "r") as f:
        rules = json.load(f)
        
    return np.array(zones["walkway_zone"], dtype=np.int32), rules["walkway_violation"]

def generate_event(rule_data):
    event = {
        "event_id": f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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

    # --- THE COOLDOWN LOGIC ---
    last_violation_time = 0
    COOLDOWN_SECONDS = 5 

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        cv2.polylines(frame, [SAFE_ZONE], isClosed=True, color=(0, 255, 0), thickness=3)

        results = model(frame, classes=[0], verbose=False)
        current_frame_violation = False

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Bottom-Center (Feet) tracking
            feet_x = int((x1 + x2) / 2)
            feet_y = int(y2)
            
            distance = cv2.pointPolygonTest(SAFE_ZONE, (feet_x, feet_y), measureDist=False)
            
            if distance >= 0:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (feet_x, feet_y), 5, (0, 255, 0), -1)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(frame, (feet_x, feet_y), 5, (0, 0, 255), -1)
                cv2.putText(frame, "VIOLATION!", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                current_frame_violation = True
                
        # --- SIMPLE TEXT-FILE LOGGING ---
        current_time = time.time()
        
        if current_frame_violation:
            if (current_time - last_violation_time) > COOLDOWN_SECONDS:
                last_violation_time = current_time
                print("\n🚨 NEW VIOLATION DETECTED 🚨")
                
                new_event = generate_event(walkway_rule)
                print(json.dumps(new_event, indent=4))
                
                # Append the JSON event to a simple text file instead of a DB
                with open("outputs/compliance_log.txt", "a") as log_file:
                    log_file.write(json.dumps(new_event) + "\n")
                    
            else:
                cv2.putText(frame, "Violation Logged (Cooldown Active)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

        cv2.imshow("Compliance Monitor", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()