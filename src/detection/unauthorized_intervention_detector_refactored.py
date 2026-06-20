"""
Unauthorized Intervention Detector (Refactored)
Detects people without proper safety equipment (green vest) in machinery zones.

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
    - Checks for safety vest (configurable HSV green color detection)
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
        
        self.machinery_zones = {}
        zones_dict = self.config.get_machinery_zones()
        for zone_name, zone_points in zones_dict.items():
            self.machinery_zones[zone_name] = np.array(zone_points, dtype=np.int32)
        
        self.rule = self.config.get_rule("unauthorized_intervention")
        
        self.last_violation_time = 0
        self.COOLDOWN_SECONDS = 5
        
        self._current_viz = VisualizationData()
        
        # Configurable green vest HSV thresholds (OpenCV hue range 0-179)
        self.LOWER_GREEN = np.array([35, 40, 40])
        self.UPPER_GREEN = np.array([85, 255, 255])
        self.VEST_DETECTION_THRESHOLD = 0.08
        self.ROI_TOP_RATIO = 0.20
        self.ROI_BOTTOM_RATIO = 0.65
        self.ROI_WIDTH_MARGIN = 0.20
    
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
        violation_zone = ""
        
        for zone_name, zone_poly in self.machinery_zones.items():
            self._current_viz.zones.append((
                zone_poly,
                (0, 0, 255),
                2
            ))
        
        for box in yolo_detections:
            if int(box.cls[0]) != 0:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            feet_x = int((x1 + x2) / 2)
            feet_y = int(y2)
            
            in_danger_zone = False
            active_zone = ""
            for zone_name, zone_poly in self.machinery_zones.items():
                distance = cv2.pointPolygonTest(
                    zone_poly,
                    (feet_x, feet_y),
                    measureDist=False
                )
                if distance >= 0:
                    in_danger_zone = True
                    active_zone = zone_name
                    break
            
            if in_danger_zone:
                has_green_vest = self._detect_green_vest(frame, x1, y1, x2, y2)
                
                if has_green_vest:
                    color = (0, 255, 0)
                    status = "AUTHORIZED"
                else:
                    color = (0, 0, 255)
                    status = "UNAUTHORIZED"
                    violation_in_frame = True
                    violation_zone = active_zone
            else:
                color = (255, 165, 0)
                status = "SAFE"
            
            self._current_viz.bounding_boxes.append((x1, y1, x2, y2, color))
            self._current_viz.circles.append((feet_x, feet_y, 5, color))
            self._current_viz.labels.append((x1, y1 - 10, status, color))
        
        if violation_in_frame:
            if (current_time - self.last_violation_time) > self.COOLDOWN_SECONDS:
                self.last_violation_time = current_time
                
                event = EventFactory.create_unauthorized_intervention(
                    event_description=(
                        self.rule.observable_indicator
                        if self.rule else "Person without green safety vest detected near machinery"
                    ),
                    zone=violation_zone or "Machine-Zone"
                )
                events.append(event)
        
        return events
    
    def _extract_vest_roi(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> np.ndarray:
        """Extract upper-torso ROI where safety vest is typically visible."""
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        x1 = max(0, x1)
        x2 = min(frame.shape[1], x2)
        y1 = max(0, y1)
        y2 = min(frame.shape[0], y2)
        
        box_h = y2 - y1
        box_w = x2 - x1
        if box_h <= 0 or box_w <= 0:
            return np.array([])
        
        roi_y1 = y1 + int(box_h * self.ROI_TOP_RATIO)
        roi_y2 = y1 + int(box_h * self.ROI_BOTTOM_RATIO)
        roi_x1 = x1 + int(box_w * self.ROI_WIDTH_MARGIN)
        roi_x2 = x2 - int(box_w * self.ROI_WIDTH_MARGIN)
        
        if roi_y2 <= roi_y1 or roi_x2 <= roi_x1:
            return np.array([])
        
        return frame[roi_y1:roi_y2, roi_x1:roi_x2]
    
    def _detect_green_vest(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> bool:
        """
        Detect if person is wearing a green safety vest.
        
        Uses HSV color space with configurable thresholds on a torso ROI.
        """
        if frame is None or frame.size == 0 or len(frame.shape) < 2:
            return False
        
        roi = self._extract_vest_roi(frame, x1, y1, x2, y2)
        
        if roi.size == 0:
            return False
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.LOWER_GREEN, self.UPPER_GREEN)
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        green_pixels = cv2.countNonZero(mask)
        total_pixels = mask.size
        green_ratio = green_pixels / total_pixels if total_pixels > 0 else 0
        
        return green_ratio > self.VEST_DETECTION_THRESHOLD
    
    def get_visualization_data(self) -> VisualizationData:
        """Get visualization data from last detection."""
        return self._current_viz


if __name__ == "__main__":
    from src.core.config_manager import ConfigManager
    
    config = ConfigManager("outputs")
    detector = UnauthorizedInterventionDetector(config)
    
    print(f"✅ Initialized: {detector.name}")
    print(f"Machinery zones: {list(detector.machinery_zones.keys())}")
    print(f"Rule: {detector.rule.name if detector.rule else 'Not found'}")
