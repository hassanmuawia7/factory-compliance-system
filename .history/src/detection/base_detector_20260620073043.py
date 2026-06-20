"""
Base Detector Class
Abstract base class for all detector implementations.

Defines the interface that all detectors must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class VisualizationData:
    """Data for visualizing detector results on frame."""
    bounding_boxes: List[tuple] = None  # List of (x1, y1, x2, y2, color)
    labels: List[tuple] = None  # List of (x, y, text, color)
    zones: List[tuple] = None  # List of (polygon_points, color, thickness)
    circles: List[tuple] = None  # List of (x, y, radius, color)
    
    def __post_init__(self):
        if self.bounding_boxes is None:
            self.bounding_boxes = []
        if self.labels is None:
            self.labels = []
        if self.zones is None:
            self.zones = []
        if self.circles is None:
            self.circles = []


class BaseDetector(ABC):
    """
    Abstract base class for all detectors.
    
    All detectors must:
    1. Inherit from BaseDetector
    2. Implement detect() method
    3. Implement get_visualization_data() method
    """
    
    def __init__(self, name: str):
        """
        Initialize detector.
        
        Args:
            name: Human-readable detector name
        """
        self.name = name
        self._last_visualization = None
    
    @abstractmethod
    def detect(
        self,
        frame: np.ndarray,
        yolo_detections: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect violations in a frame using provided YOLO detections.
        
        Args:
            frame: Video frame (OpenCV image)
            yolo_detections: YOLO results.boxes from model(frame)
        
        Returns:
            List of event dictionaries to publish
            
        Example return value:
            [
                {
                    "event_id": "EVT-20260120120530000000",
                    "timestamp": "2026-01-20T12:05:30",
                    "behavior_class": "walkway_violation",
                    "severity": "HIGH",
                    "policy_rule_ref": "POLICY_WALKWAY_001",
                    "description": "Person detected outside walkway zone"
                }
            ]
        """
        pass
    
    @abstractmethod
    def get_visualization_data(self) -> VisualizationData:
        """
        Get visualization data from last detection.
        
        Returns:
            VisualizationData object with boxes, labels, zones to draw
        """
        pass
    
    def set_last_visualization(self, data: VisualizationData) -> None:
        """Store visualization data for retrieval."""
        self._last_visualization = data
    
    def get_last_visualization(self) -> VisualizationData:
        """Get stored visualization data."""
        if self._last_visualization is None:
            return VisualizationData()
        return self._last_visualization


if __name__ == "__main__":
    # Example of how to implement a detector
    class ExampleDetector(BaseDetector):
        def __init__(self):
            super().__init__("Example Detector")
        
        def detect(self, frame, yolo_detections):
            # Detection logic here
            return []
        
        def get_visualization_data(self):
            return VisualizationData()
    
    detector = ExampleDetector()
    print(f"✅ Created detector: {detector.name}")
