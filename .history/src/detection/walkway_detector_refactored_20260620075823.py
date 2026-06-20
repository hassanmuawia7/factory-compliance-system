"""
Walkway Detector
Detects people standing outside the designated safe walkway zone.

Severity: HIGH
Behavior: walkway_violation

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


class WalkwayDetector(BaseDetector):
    """
    Detects people outside the walkway safe zone.
    
    Does NOT:
    - Create YOLO model (receives detections as parameter)
    - Write to database (returns events)
    - Load config files (receives ConfigManager instance)
    
    Only:
    - Analyzes YOLO detections against zone polygon
    - Generates violation events
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize walkway detector.
        
        Args:
            config_manager: ConfigManager instance
        """
        super().__init__("Walkway Detector")
        self.config = config_manager
        
        # Load zone from config
        self.walkway_zone = np.array(
            self.config.get_walkway_zone(),
            dtype=np.int32
        )
        
        # Get rule information
        self.rule = self.config.get_rule("walkway_violation")
        
        # Cooldown logic to prevent duplicate events
        self.last_violation_time = 0
        self.COOLDOWN_SECONDS = 5
        
        # Visualization data from last detection
        self._current_viz = VisualizationData()
    
    def detect(
        self,
        frame: np.ndarray,
        yolo_detections: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect walkway violations.
        
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
        
        # Process each detected person
        for box in yolo_detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Calculate center point at feet level
            center_x = int((x1 + x2) / 2)
            center_y = int(y2)
            
            # Test if person is INSIDE the safe zone
            distance = cv2.pointPolygonTest(
                self.walkway_zone,
                (center_x, center_y),
                measureDist=False
            )
            
            if distance >= 0:
                # ✅ Person is INSIDE safe zone (OK)
                color = (0, 255, 0)  # Green
                status = "SAFE"
            else:
                # ❌ Person is OUTSIDE safe zone (VIOLATION)
                color = (0, 0, 255)  # Red
                status = "VIOLATION"
                violation_in_frame = True
            
            # Add to visualization
            self._current_viz.bounding_boxes.append((x1, y1, x2, y2, color))
            self._current_viz.circles.append((center_x, center_y, 5, color))
            self._current_viz.labels.append((x1, y1 - 10, status, color))
        
        # Add zone visualization
        self._current_viz.zones.append((
            self.walkway_zone,
            (0, 255, 0),  # Green border
            2  # Thickness
        ))
        
        # Event creation (with cooldown)
        if violation_in_frame:
            if (current_time - self.last_violation_time) > self.COOLDOWN_SECONDS:
                self.last_violation_time = current_time
                
                # Create violation event
                event = EventFactory.create_walkway_violation(
                    description=self.rule.observable_indicator
                )
                events.append(event)
        
        return events
    
    def get_visualization_data(self) -> VisualizationData:
        """Get visualization data from last detection."""
        return self._current_viz


if __name__ == "__main__":
    # Test walkway detector
    from src.core.config_manager import ConfigManager
    
    config = ConfigManager("outputs")
    detector = WalkwayDetector(config)
    
    print(f"✅ Initialized: {detector.name}")
    print(f"Walkway zone: {detector.walkway_zone.shape[0]} points")
    print(f"Rule: {detector.rule.name if detector.rule else 'Not found'}")
