"""
Unauthorized Intervention Detector
Detects people without safety equipment (blue vest/uniform) in machinery danger zones.

Severity: CRITICAL
Behavior: unauthorized_intervention

This detector combines:
1. Person detection (YOLOv8)
2. Danger zone detection (polygon-based, multi-machine)
3. Safety vest detection (color-range based HSV detection - Blue)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import cv2
import json
import numpy as np
import time
from datetime import datetime
from ultralytics import YOLO

from src.database.database_service import DatabaseService
from src.severity.event_factory import EventFactory


def load_configurations():
    """Load danger zones and safety rules from config files."""
    try:
        with open("outputs/zones.json", "r") as f:
            zones = json.load(f)
        
        with open("outputs/validated_rules.json", "r") as f:
            rules = json.load(f)
    except FileNotFoundError:
        print("⚠️  Configuration files not found. Using default values.")
        zones = {
            "machinery_zones": {
                "machine_1": [[100, 100], [500, 100], [500, 400], [100, 400]]
            }
        }
        rules = {
            "unauthorized_intervention": {
                "policy_reference": "POLICY_SAFETY_002",
                "observable_indicator": "Person without safety vest near machinery",
                "severity_hint": "CRITICAL"
            }
        }
    
    # Extract the dictionary of multiple machines
    machinery_zones_data = zones.get("machinery_zones", {})

    if not machinery_zones_data:
        print("⚠ No machinery_zones found in zones.json")
        print("Using default machinery zone")
        machinery_zones_data = {
            "machine_1": [
                [100,100],
                [500,100],
                [500,400],
                [100,400]
            ]
        }

    # Convert all machine lists to numpy arrays
    machinery_zones = {}
    for name, pts in machinery_zones_data.items():
        machinery_zones[name] = np.array(pts, dtype=np.int32)
        
    safety_rules = rules.get("unauthorized_intervention", {})
    
    return machinery_zones, safety_rules


def detect_safety_vest(frame, bbox):
    """
    Detect if person in bounding box is wearing the required safety vest.
    
    Uses HSV color space for blue detection based on current dataset.
    Blue range: H ~90-130 (HSV), S >50, V >50
    """
    x1, y1, x2, y2 = bbox
    height = y2 - y1
    
    # Isolate the torso to eliminate floor and machine reflections
    torso_y1 = y1 + int(height * 0.25)
    torso_y2 = y1 + int(height * 0.75)
    
    # Ensure coordinates are valid within the frame
    x1, x2 = max(0, min(x1, x2)), min(frame.shape[1], max(x1, x2))
    torso_y1, torso_y2 = max(0, min(torso_y1, torso_y2)), min(frame.shape[0], max(torso_y1, torso_y2))
    
    roi = frame[torso_y1:torso_y2, x1:x2]
    
    if roi.size == 0:
        return False
    
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Blue color range in HSV
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])
    
    # Create mask
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Calculate percentage of targeted color pixels
    color_pixels = cv2.countNonZero(mask)
    total_pixels = mask.size
    color_ratio = color_pixels / total_pixels if total_pixels > 0 else 0
    
    # 20% threshold to register as a valid vest
    return color_ratio > 0.20


def main():
    """Main detection loop for unauthorized intervention."""
    
    print("Loading configurations...")
    MACHINERY_ZONES, SAFETY_RULES = load_configurations()
    
    print("Loading YOLO model...")
    model = YOLO("yolov8n.pt")
    
    # Open video source
    video_source = "data/videos/test.mp4"
    if not os.path.exists(video_source):
        print(f"⚠️  Video file not found: {video_source}")
        print("Please provide a video file in data/videos/")
        return
    
    cap = cv2.VideoCapture(video_source)
    
    # Setup window
    cv2.namedWindow("Unauthorized Intervention Detector", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Unauthorized Intervention Detector", 1280, 720)
    
    # Cooldown logic to prevent duplicate events
    last_violation_time = 0
    COOLDOWN_SECONDS = 5
    
    # Trackers
    frame_count = 0
    violations_detected = 0
    safe_persons = 0
    
    # Diagnostics Debug Counters
    people_detected = 0
    people_in_machine_zone = 0
    vest_detected_count = 0
    
    print("\n🔴 Starting unauthorized intervention detection...")
    print("   Press 'q' to quit\n")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        
        # PERFORMANCE FIX 1: Process every 3rd frame
        if frame_count % 3 != 0:
            continue
            
        orig_h, orig_w = frame.shape[:2]
        
        # Draw all machinery danger zones dynamically
        for m_name, m_zone in MACHINERY_ZONES.items():
            cv2.polylines(
                frame, [m_zone], isClosed=True,
                color=(0, 0, 255), thickness=3
            )
            cv2.putText(
                frame, m_name.upper(), tuple(m_zone[0]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
            )
            
        # PERFORMANCE FIX 2: Resize before YOLO
        small_frame = cv2.resize(frame, (960, 540))
        results = model(small_frame, classes=[0], verbose=False)
        
        # Calculate scaling factors to map small_frame boxes back to the original frame
        scale_x = orig_w / 960.0
        scale_y = orig_h / 540.0
        
        current_frame_violation = False
        active_machine_for_violation = ""
        frame_violations = 0
        frame_safe = 0
        
        for box in results[0].boxes:
            # Diagnostic Counter 1: Total YOLO Person Detections
            people_detected += 1
            
            # Map coordinates from 960x540 back to original frame size
            sx1, sy1, sx2, sy2 = map(float, box.xyxy[0])
            x1, y1, x2, y2 = int(sx1 * scale_x), int(sy1 * scale_y), int(sx2 * scale_x), int(sy2 * scale_y)
            
            # Diagnostic Test: Temporarily using body center instead of feet to test tight polygon theory
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)  
            
            person_in_any_machine = False
            current_machine_name = ""
            
            # Check if person is in ANY machinery zone
            for m_name, m_zone in MACHINERY_ZONES.items():
                distance = cv2.pointPolygonTest(m_zone, (center_x, center_y), measureDist=False)
                if distance >= 0:
                    person_in_any_machine = True
                    current_machine_name = m_name
                    # Diagnostic Counter 2: Person detected inside polygon boundaries
                    people_in_machine_zone += 1
                    break  # Found them in a zone, stop checking others
            
            if person_in_any_machine:
                # Active Safety Vest Detection (Blue)
                has_vest = detect_safety_vest(frame, (x1, y1, x2, y2))
                
                if has_vest:
                    # Diagnostic Counter 3: Person inside zone + Vest detected
                    vest_detected_count += 1
                    
                    # Authorized: has safety vest
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    cv2.putText(
                        frame, "AUTHORIZED", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                    )
                    frame_safe += 1
                else:
                    # VIOLATION: no safety vest in danger zone
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.putText(
                        frame, "UNAUTHORIZED!", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
                    )
                    
                    current_frame_violation = True
                    active_machine_for_violation = current_machine_name
                    frame_violations += 1
            else:
                # Person is OUTSIDE all danger zones (safe)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 1)
                cv2.circle(frame, (center_x, center_y), 5, (0, 165, 255), -1)
                frame_safe += 1
        
        # EVENT LOGGING & DATABASE ROUTING
        current_time = time.time()
        
        if current_frame_violation:
            if (current_time - last_violation_time) > COOLDOWN_SECONDS:
                last_violation_time = current_time
                violations_detected += 1
                
                print(f"\n🚨 UNAUTHORIZED INTERVENTION DETECTED AT {active_machine_for_violation.upper()} 🚨")
                
                # Create event using EventFactory
                violation_event = EventFactory.create_unauthorized_intervention(
                    description=f"Person without safety vest detected in {active_machine_for_violation} zone"
                )
                
                print(f"Event ID: {violation_event['event_id']}")
                print(f"Severity: {violation_event['severity']}")
                print(f"Policy: {violation_event['policy_rule_ref']}")
                
                # Validate event
                is_valid, msg = EventFactory.validate_event(violation_event)
                if is_valid:
                    # Save to database
                    success = DatabaseService.create_violation(violation_event)
                    if success:
                        print("✅ Event saved to database!")
                    else:
                        print("❌ Failed to save event")
                else:
                    print(f"❌ Event validation failed: {msg}")
            else:
                # Cooldown active
                remaining = int(COOLDOWN_SECONDS - (current_time - last_violation_time))
                cv2.putText(
                    frame, f"Violation logged (Cooldown: {remaining}s)",
                    (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2
                )
        
        # Display frame statistics
        cv2.putText(
            frame, f"Frame: {frame_count} | Violations: {violations_detected}",
            (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2
        )
        cv2.putText(
            frame, f"Unauthorized: {frame_violations} | Authorized: {frame_safe}",
            (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2
        )
        
        # Display
        cv2.imshow("Unauthorized Intervention Detector", frame)
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DETECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Frames processed: {frame_count}")
    print(f"Total people detected across frames: {people_detected}")
    print(f"Total people in machine zones across frames: {people_in_machine_zone}")
    print(f"Total vest detections across frames: {vest_detected_count}")
    print(f"Unauthorized interventions detected: {violations_detected}")
    print(f"Database records created: {violations_detected}")
    print(f"Status: ✅ Complete\n")


if __name__ == "__main__":
    main()