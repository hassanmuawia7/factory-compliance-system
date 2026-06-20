"""
Detector Manager
Coordinates all detectors in the system.

Responsibilities:
- Initialize all detectors
- Run detectors on each frame
- Collect events from all detectors
- Provide unified visualization data
"""

from typing import List, Dict, Any
import numpy as np

from src.detection.base_detector import BaseDetector, VisualizationData
from src.detection.walkway_detector_refactored import WalkwayDetector
from src.detection.unauthorized_intervention_detector_refactored import UnauthorizedInterventionDetector
from src.detection.forklift_detector_refactored import ForkliftOverloadDetector
from src.core.config_manager import ConfigManager


class DetectorManager:
    """
    Manages all detectors in the system.
    
    Single responsibility: Coordinate detector initialization and execution.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize detector manager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.detectors: Dict[str, BaseDetector] = {}
        
        self._initialize_detectors()
    
    def _initialize_detectors(self) -> None:
        """Initialize all detectors."""
        print("\n🚀 Initializing Detectors...")
        
        # Initialize walkway detector
        try:
            walkway = WalkwayDetector(self.config)
            self.detectors["walkway"] = walkway
            print(f"  ✅ {walkway.name} initialized")
        except Exception as e:
            print(f"  ❌ Failed to initialize WalkwayDetector: {e}")
        
        # Initialize unauthorized intervention detector
        try:
            unauthorized = UnauthorizedInterventionDetector(self.config)
            self.detectors["unauthorized"] = unauthorized
            print(f"  ✅ {unauthorized.name} initialized")
        except Exception as e:
            print(f"  ❌ Failed to initialize UnauthorizedInterventionDetector: {e}")

        try:
            forklift = ForkliftOverloadDetector(self.config)
            self.detectors["forklift"] = forklift
            print(f"  ✅ {forklift.name} initialized")
        except Exception as e:
            print(f"  ❌ Failed to initialize ForkliftOverloadDetector: {e}")
        
        print(f"  Total detectors: {len(self.detectors)}\n")
    
    def process_frame(
        self,
        frame: np.ndarray,
        yolo_detections: List[Any]
    ) -> Dict[str, Any]:
        """
        Process frame through all detectors.
        
        Args:
            frame: Video frame
            yolo_detections: YOLO detection results
        
        Returns:
            Dictionary containing:
            - events: List of all events from all detectors
            - visualization: Aggregated visualization data
        """
        all_events = []
        all_viz_data = VisualizationData()
        
        # Run each detector
        for detector_name, detector in self.detectors.items():
            try:
                # Get events from this detector
                events = detector.detect(frame, yolo_detections)
                all_events.extend(events)
                
                # Get visualization from this detector
                viz = detector.get_visualization_data()
                self._merge_visualization(all_viz_data, viz)
            
            except Exception as e:
                print(f"❌ Error in {detector_name}: {e}")
        
        return {
            "events": all_events,
            "visualization": all_viz_data
        }
    
    @staticmethod
    def _merge_visualization(
        target: VisualizationData,
        source: VisualizationData
    ) -> None:
        """
        Merge visualization data from multiple detectors.
        
        Args:
            target: VisualizationData to merge into
            source: VisualizationData to merge from
        """
        target.bounding_boxes.extend(source.bounding_boxes)
        target.labels.extend(source.labels)
        target.zones.extend(source.zones)
        target.circles.extend(source.circles)
    
    def get_detector_count(self) -> int:
        """Get number of active detectors."""
        return len(self.detectors)
    
    def get_detector_names(self) -> List[str]:
        """Get list of detector names."""
        return list(self.detectors.keys())


if __name__ == "__main__":
    # Test detector manager
    from src.core.config_manager import ConfigManager
    
    config = ConfigManager("outputs")
    manager = DetectorManager(config)
    
    print(f"Detectors: {manager.get_detector_names()}")
    print(f"Active detectors: {manager.get_detector_count()}")
