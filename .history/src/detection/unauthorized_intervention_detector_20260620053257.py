"""
Unauthorized Intervention Detector
Detects people without safety equipment (green vest) in machinery danger zones.

Severity: CRITICAL
Behavior: unauthorized_intervention

This detector combines:
1. Person detection (YOLOv8)
2. Danger zone detection (polygon-based)
3. Green vest detection (color-range based HSV detection)
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
     
        rules = {
            "unauthorized_intervention": {
                "policy_reference": "POLICY_SAFETY_002",
                "observable_indicator": "Person without safety vest near machinery",
                "severity_hint": "CRITICAL"
            }
        }
    
    machinery_zone = np.array(zones.get("machinery_zone", []), dtype=np.int32)
    safety_rules = rules.get("unauthorized_intervention", {})
    
    return machinery_zone, safety_rules


def detect_green_vest(frame, bbox):
    """
    Detect if person in bounding box is wearing green safety vest.
    
    Uses HSV color space for green detection.
    Green range: H ~60-90 (HSV), S >50, V >50
    
    Args:
        frame: Video frame
        bbox: Bounding box (x1, y1, x2, y2)
        
    Returns:
        bool: True if green vest detected, False otherwise
    """
    x1, y1, x2, y2 = bbox
    
    # Ensure coordinates are valid
    x1, x2 = max(0, min(x1, x2)), min(frame.shape[1], max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(frame.shape[0], max(y1, y2))
    
    roi = frame[y1:y2, x1:x2]
    
    if roi.size == 0:
        return False
    
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Green color range in HSV
    # Hue: 35-85 (green range)
    # Saturation: 50-255 (vibrant)
    # Value: 50-255 (bright)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    # Create mask
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Calculate percentage of green pixels
    green_pixels = cv2.countNonZero(mask)
    total_pixels = mask.size
    green_ratio = green_pixels / total_pixels if total_pixels > 0 else 0
    
    # If >10% of ROI is green, consider vest detected
    return green_ratio > 0.1


def main():
    """Main detection loop for unauthorized intervention."""
    
    print("Loading configurations...")
    MACHINERY_ZONE, SAFETY_RULES = load_configurations()
    
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
    
    frame_count = 0
    violations_detected = 0
    safe_persons = 0
    
    print("\n🔴 Starting unauthorized intervention detection...")
    print("   Press 'q' to quit\n")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        
        # Draw the machinery danger zone
        cv2.polylines(
            frame, [MACHINERY_ZONE], isClosed=True,
            color=(0, 0, 255), thickness=3
        )
        
        # Draw zone label
        cv2.putText(
            frame, "MACHINERY ZONE", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
        )
        
        # Detect people (class 0)
        results = model(frame, classes=[0], verbose=False)
        
        current_frame_violation = False
        frame_violations = 0
        frame_safe = 0
        
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Calculate center point for zone detection
            center_x = int((x1 + x2) / 2)
            center_y = int(y2)  # Use bottom center (feet level)
            
            # Check if person is in machinery zone
            distance = cv2.pointPolygonTest(
                MACHINERY_ZONE, (center_x, center_y), measureDist=False
            )
            
            if distance >= 0:  # Person is IN the danger zone
                # Check for green vest
                has_vest = detect_green_vest(frame, (x1, y1, x2, y2))
                
                if has_vest:
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
                    frame_violations += 1
            else:
                # Person is OUTSIDE danger zone (safe)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 1)
                cv2.circle(frame, (center_x, center_y), 5, (0, 165, 255), -1)
                frame_safe += 1
        
        # EVENT LOGGING & DATABASE ROUTING
        current_time = time.time()
        
        if current_frame_violation:
            if (current_time - last_violation_time) > COOLDOWN_SECONDS:
                last_violation_time = current_time
                violations_detected += 1
                
                print("\n🚨 UNAUTHORIZED INTERVENTION DETECTED 🚨")
                
                # Create event using EventFactory
                violation_event = EventFactory.create_unauthorized_intervention(
                    description="Person without safety vest detected in machinery zone"
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
    print(f"Unauthorized interventions detected: {violations_detected}")
    print(f"Database records created: {violations_detected}")
    print(f"Status: ✅ Complete\n")


if __name__ == "__main__":
    main()
