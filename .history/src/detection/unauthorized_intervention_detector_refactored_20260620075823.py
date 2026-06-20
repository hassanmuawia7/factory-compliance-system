"""
Unauthorized Intervention Detector (Refactored)
Detects people without proper safety equipment (blue vest) in machinery zones.

Severity: CRITICAL
Behavior: unauthorized_intervention

This is a refactored version that:
- Inherits from BaseDetector
- Takes YOLO detections as input (doesn't create its own YOLO)
- Returns events without database writes
- Provides visualization data separately
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import cv2
import numpy as np
import time
from typing import List, Dict, Any

from src.detection.base_detector import BaseDetector, VisualizationData
from src.core.config_manager import ConfigManager
from src.severity.event_factory import EventFactory


class UnauthorizedInterventionDetector(BaseDetector):
    """
    Detects people without safety equipment in machinery zones.
    
    Does NOT:
    - Create YOLO model (receives detections as parameter)
    - Write to database (returns events)
    - Load config files (receives ConfigManager instance)
    
    Only:
    - Analyzes YOLO detections against machinery zones
    - Checks for safety vest (blue color detection)
    - Generates CRITICAL violation events
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize unauthorized intervention detector.
        
        Args:
            config_manager: ConfigManager instance
        """
        super().__init__("Unauthorized Intervention Detector")
        self.config = config_manager
        
        # Load machinery zones from config
        self.machinery_zones = {}
        zones_dict = self.config.get_machinery_zones()
        for zone_name, zone_points in zones_dict.items():
            self.machinery_zones[zone_name] = np.array(zone_points, dtype=np.int32)
        
        # Get rule information
        self.rule = self.config.get_rule("unauthorized_intervention")
        
        # Cooldown logic to prevent duplicate events
        self.last_violation_time = 0
        self.COOLDOWN_SECONDS = 5
        
        # Visualization data from last detection
        self._current_viz = VisualizationData()
        
        # Blue vest detection thresholds (HSV color space)
        self.LOWER_BLUE = np.array([100, 50, 50])  # Lower bound for blue
        self.UPPER_BLUE = np.array([130, 255, 255])  # Upper bound for blue
        self.BLUE_DETECTION_THRESHOLD = 0.1  # Minimum 10% of ROI must be blue
    
    def detect(
        self,
        frame: np.ndarray,
        yolo_detections: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect unauthorized interventions.
        
        Args:
            frame: Video frame
            yolo_detections: YOLO results.boxes
        
        Returns:
            List of violation events
        """
        events = []
        self._current_viz = VisualizationData()
        
        current_time = time.time()
        violation_in_frame = False
        
        # Add machinery zones to visualization
        for zone_name, zone_poly in self.machinery_zones.items():
            self._current_viz.zones.append((
                zone_poly,
                (0, 0, 255),  # Red border for machinery zones
                2  # Thickness
            ))
        
        # Process each detected person
        for box in yolo_detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Calculate feet position (used for zone testing)
            feet_x = int((x1 + x2) / 2)
            feet_y = int(y2)
            
            # Check if person is in any machinery zone
            in_danger_zone = False
            for zone_name, zone_poly in self.machinery_zones.items():
                distance = cv2.pointPolygonTest(
                    zone_poly,
                    (feet_x, feet_y),
                    measureDist=False
                )
                if distance >= 0:
                    in_danger_zone = True
                    break
            
            if in_danger_zone:
                # Person IS in machinery zone - check for safety vest
                has_blue_vest = self._detect_blue_vest(frame, x1, y1, x2, y2)
                
                if has_blue_vest:
                    # ✅ Has proper safety equipment (OK)
                    color = (0, 255, 0)  # Green
                    status = "AUTHORIZED"
                else:
                    # ❌ No safety equipment in danger zone (VIOLATION)
                    color = (0, 0, 255)  # Red
                    status = "UNAUTHORIZED"
                    violation_in_frame = True
            else:
                # Person is OUTSIDE machinery zones (safe)
                color = (255, 165, 0)  # Orange
                status = "SAFE"
            
            # Add to visualization
            self._current_viz.bounding_boxes.append((x1, y1, x2, y2, color))
            self._current_viz.circles.append((feet_x, feet_y, 5, color))
            self._current_viz.labels.append((x1, y1 - 10, status, color))
        
        # Event creation (with cooldown)
        if violation_in_frame:
            if (current_time - self.last_violation_time) > self.COOLDOWN_SECONDS:
                self.last_violation_time = current_time
                
                # Create CRITICAL violation event
                event = EventFactory.create_unauthorized_intervention(
                    description=self.rule.observable_indicator
                )
                events.append(event)
        
        return events
    
    def _detect_blue_vest(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> bool:
        """
        Detect if person is wearing blue safety vest.
        
        Uses HSV color space for robust color detection.
        
        Args:
            frame: Video frame
            x1, y1, x2, y2: Bounding box coordinates
        
        Returns:
            True if blue vest detected
        """
        # Extract ROI
        x1 = max(0, x1)
        x2 = min(frame.shape[1], x2)
        y1 = max(0, y1)
        y2 = min(frame.shape[0], y2)
        
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return False
        
        # Convert to HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Create blue mask
        mask = cv2.inRange(hsv, self.LOWER_BLUE, self.UPPER_BLUE)
        
        # Calculate blue pixel percentage
        blue_pixels = cv2.countNonZero(mask)
        total_pixels = mask.size
        blue_ratio = blue_pixels / total_pixels if total_pixels > 0 else 0
        
        # Consider vest detected if threshold exceeded
        return blue_ratio > self.BLUE_DETECTION_THRESHOLD
    
    def get_visualization_data(self) -> VisualizationData:
        """Get visualization data from last detection."""
        return self._current_viz


if __name__ == "__main__":
    # Test unauthorized intervention detector
    from src.core.config_manager import ConfigManager
    
    config = ConfigManager("outputs")
    detector = UnauthorizedInterventionDetector(config)
    
    print(f"✅ Initialized: {detector.name}")
    print(f"Machinery zones: {list(detector.machinery_zones.keys())}")
    print(f"Rule: {detector.rule.name if detector.rule else 'Not found'}")
