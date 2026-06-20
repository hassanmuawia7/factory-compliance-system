"""
FACTORY COMPLIANCE SYSTEM - MAIN ENTRY POINT
Phase 7: System Integration and Main Pipeline

This is the unified system orchestration that brings everything together:
- Loads configuration once
- Initializes YOLO once
- Runs all detectors together
- Manages event pipeline
- Displays unified visualization
- Tracks system statistics
- Handles graceful shutdown

Usage:
    python src/main.py [video_path]

Example:
    python src/main.py data/videos/test.mp4
    python src/main.py 0  # Use webcam
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import argparse
from typing import Optional, Dict
from ultralytics import YOLO

from src.core.config_manager import ConfigManager
from src.core.detector_manager import DetectorManager
from src.core.event_bus import EventBus, EventType, Event
from src.core.system_stats import SystemStats, get_system_stats
from src.database.database_service import DatabaseService
from src.severity.event_factory import EventFactory
from src.database.db_manager import init_db


class ComplianceMonitoringSystem:
    """
    Main system orchestrator for factory compliance monitoring.
    
    Coordinates:
    - Configuration loading
    - YOLO initialization
    - Video processing
    - Detector coordination
    - Event management
    - Database updates
    - Statistics tracking
    - Visualization
    """
    
    def __init__(self, video_source: str = "data/videos/test.mp4"):
        """
        Initialize the compliance monitoring system.
        
        Args:
            video_source: Path to video file or camera index
        """
        print("\n" + "="*70)
        print(" FACTORY COMPLIANCE MONITORING SYSTEM - MAIN PIPELINE")
        print(" Phase 7: System Integration")
        print("="*70)
        
        self.video_source = video_source
        self.is_running = False
        
        # Initialize components
        self._initialize_system()
    
    def _initialize_system(self) -> None:
        """Initialize all system components."""
        
        print("\n📋 Phase 1: Loading Configuration...")
        self.config = ConfigManager("outputs")
        if not self.config.validate():
            raise RuntimeError("Configuration validation failed")
        
        print("\n🤖 Phase 2: Initializing YOLO...")
        try:
            self.yolo = YOLO("yolov8n.pt")
            print("  ✅ YOLOv8 Nano loaded (Single instance for entire system)")
        except Exception as e:
            print(f"  ❌ Failed to load YOLO: {e}")
            raise
        
        print("\n🎬 Phase 3: Opening Video Source...")
        self.cap = cv2.VideoCapture(self.video_source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {self.video_source}")
        
        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"  ✅ Video opened: {self.width}x{self.height} @ {self.fps} FPS")
        print(f"     Total frames: {self.total_frames}")
        
        print("\n🎯 Phase 4: Initializing Detectors...")
        self.detector_manager = DetectorManager(self.config)
        
        print("\n📊 Phase 5: Initializing Systems...")
        self.event_bus = EventBus()
        self.stats = get_system_stats()
        
        # Setup window
        cv2.namedWindow("Factory Compliance Monitor", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Factory Compliance Monitor", 1280, 720)
        
        print("\n✅ System Initialization Complete!")
        print(f"   Ready to process: {self.total_frames} frames")
    
    def run(self) -> None:
        """Run the main compliance monitoring loop."""
        
        print("\n" + "="*70)
        print(" STARTING COMPLIANCE MONITORING PIPELINE")
        print("="*70)
        print("\nPress 'Q' to quit, 'P' to pause\n")
        
        self.is_running = True
        frame_count = 0
        paused = False
        
        try:
            while self.is_running:
                # Read frame
                success, frame = self.cap.read()
                if not success:
                    print("\n✅ End of video reached")
                    break
                
                frame_count += 1
                self.stats.increment_frame()
                
                # YOLO Inference (ONCE per frame, shared by all detectors)
                yolo_results = self.yolo(frame, classes=[0], verbose=False)
                yolo_detections = yolo_results[0].boxes
                
                # Process through all detectors
                detector_result = self.detector_manager.process_frame(
                    frame,
                    yolo_detections
                )
                
                events = detector_result["events"]
                visualization = detector_result["visualization"]
                
                # Process events
                for event in events:
                    self._handle_event(event)
                
                # Draw unified visualization
                frame = self._draw_unified_overlay(frame, visualization)
                
                # Add frame info
                cv2.putText(
                    frame,
                    f"Frame: {frame_count}/{self.total_frames}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (200, 200, 200),
                    2
                )
                cv2.putText(
                    frame,
                    f"Violations: {self.stats.get_statistics().total_violations}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
                
                # Display frame
                cv2.imshow("Factory Compliance Monitor", frame)
                
                # Handle keyboard
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\n⚠️  Shutdown signal received...")
                    self.is_running = False
                elif key == ord('p') or key == ord('P'):
                    paused = not paused
                    status = "PAUSED" if paused else "RUNNING"
                    print(f"   System {status}")
                
                # Pause logic
                while paused:
                    key = cv2.waitKey(100) & 0xFF
                    if key == ord('p') or key == ord('P'):
                        paused = False
                        print("   System RESUMED")
                        break
        
        except KeyboardInterrupt:
            print("\n⚠️  Keyboard interrupt received...")
        
        finally:
            self._shutdown()
    
    def _handle_event(self, event: Dict) -> None:
        """
        Process a detected event.
        
        Args:
            event: Event dictionary from detector
        """
        # Update statistics
        self.stats.record_violation(
            event.get("severity", "LOW"),
            event.get("behavior_class", "unknown")
        )
        
        # Validate event
        is_valid, msg = EventFactory.validate_event(event)
        if not is_valid:
            print(f"⚠️  Event validation warning: {msg}")
            return
        
        # Save to database
        success = DatabaseService.create_violation(event)
        
        # Publish event on event bus
        if success:
            bus_event = Event(
                event_type=EventType.VIOLATION_DETECTED,
                payload=event
            )
            if event.get("severity") == "CRITICAL":
                bus_event.event_type = EventType.CRITICAL_VIOLATION
            
            self.event_bus.publish(bus_event)
            
            # Console notification
            severity = event.get("severity", "?")
            behavior = event.get("behavior_class", "?")
            print(f"🚨 Event: [{severity}] {behavior} - {event.get('event_id')}")
    
    @staticmethod
    def _draw_unified_overlay(frame, visualization) -> object:
        """
        Draw unified visualization from all detectors.
        
        Args:
            frame: Video frame
            visualization: Aggregated VisualizationData
        
        Returns:
            Frame with all visualizations drawn
        """
        # Draw zones
        for zone_points, color, thickness in visualization.zones:
            cv2.polylines(frame, [zone_points], isClosed=True, color=color, thickness=thickness)
        
        # Draw bounding boxes
        for x1, y1, x2, y2, color in visualization.bounding_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw circles (detection points)
        for x, y, radius, color in visualization.circles:
            cv2.circle(frame, (x, y), radius, color, -1)
        
        # Draw labels
        for x, y, text, color in visualization.labels:
            cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame
    
    def _shutdown(self) -> None:
        """Graceful system shutdown."""
        print("\n" + "="*70)
        print(" SHUTDOWN SEQUENCE INITIATED")
        print("="*70)
        
        print("\n🔒 Phase 1: Closing resources...")
        
        # Close video
        if self.cap:
            self.cap.release()
            print("  ✅ Video source closed")
        
        # Close display window
        cv2.destroyAllWindows()
        print("  ✅ Display windows closed")
        
        print("\n📊 Phase 2: Final System Statistics...")
        self.stats.print_summary()
        
        print("=" * 70)
        print(" SYSTEM SHUTDOWN COMPLETE")
        print("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Factory Compliance Monitoring System - Main Pipeline"
    )
    parser.add_argument(
        "video",
        nargs="?",
        default="data/videos/test.mp4",
        help="Path to video file or camera index (default: data/videos/test.mp4)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        system = ComplianceMonitoringSystem(args.video)
        
        # Run monitoring
        system.run()
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()