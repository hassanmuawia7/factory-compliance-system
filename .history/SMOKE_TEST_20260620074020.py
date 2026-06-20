"""
SMOKE_TEST.py
Factory Compliance System - Smoke Test Suite
Verifies all core components initialize correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class SmokeTest:
    """Smoke test for all system components."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def test_config_manager(self):
        """Test ConfigManager initialization."""
        try:
            from core.config_manager import ConfigManager
            
            config = ConfigManager("outputs")
            
            # Verify methods exist and work
            zones = config.get_walkway_zone()
            machinery = config.get_machinery_zones()
            rules = config._load_rules()
            
            self.results.append("✅ ConfigManager: Initialized successfully")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ ConfigManager: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_event_bus(self):
        """Test EventBus initialization."""
        try:
            from core.event_bus import EventBus, EventType, Event
            
            bus = EventBus()
            
            # Test event creation
            event = Event(EventType.SYSTEM_STARTED, {"test": "data"})
            
            # Test subscription
            callback_count = [0]
            def test_callback(event):
                callback_count[0] += 1
            
            bus.subscribe(EventType.SYSTEM_STARTED, test_callback)
            bus.publish(event)
            
            assert callback_count[0] > 0, "EventBus callback not called"
            
            self.results.append("✅ EventBus: Initialized and functional")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ EventBus: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_system_stats(self):
        """Test SystemStats initialization."""
        try:
            from core.system_stats import SystemStats, get_system_stats
            
            stats = get_system_stats()
            
            # Test methods
            stats.increment_frame()
            stats.record_violation("CRITICAL", "walkway_violation")
            
            summary = stats.get_summary()
            assert summary["frames_processed"] > 0, "Frame count not incremented"
            assert summary["total_violations"] > 0, "Violation not recorded"
            
            self.results.append("✅ SystemStats: Initialized and tracking")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ SystemStats: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_base_detector(self):
        """Test BaseDetector interface."""
        try:
            from detection.base_detector import BaseDetector, VisualizationData
            
            # Verify abstract class
            assert hasattr(BaseDetector, 'detect'), "detect method missing"
            assert hasattr(BaseDetector, 'get_visualization_data'), "get_visualization_data method missing"
            
            # Verify VisualizationData
            viz = VisualizationData([], [], [], [])
            assert viz.bounding_boxes == [], "VisualizationData initialization failed"
            
            self.results.append("✅ BaseDetector: Interface verified")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ BaseDetector: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_walkway_detector(self):
        """Test WalkwayDetector initialization."""
        try:
            from core.config_manager import ConfigManager
            from detection.walkway_detector_refactored import WalkwayDetector
            
            config = ConfigManager("outputs")
            detector = WalkwayDetector(config)
            
            # Verify properties
            assert detector.name == "Walkway Detector", "Detector name incorrect"
            assert hasattr(detector, 'detect'), "detect method missing"
            assert hasattr(detector, 'get_visualization_data'), "get_visualization_data method missing"
            
            self.results.append("✅ WalkwayDetector: Initialized successfully")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ WalkwayDetector: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_unauthorized_intervention_detector(self):
        """Test UnauthorizedInterventionDetector initialization."""
        try:
            from core.config_manager import ConfigManager
            from detection.unauthorized_intervention_detector_refactored import UnauthorizedInterventionDetector
            
            config = ConfigManager("outputs")
            detector = UnauthorizedInterventionDetector(config)
            
            # Verify properties
            assert detector.name == "Unauthorized Intervention Detector", "Detector name incorrect"
            assert hasattr(detector, 'detect'), "detect method missing"
            assert hasattr(detector, 'get_visualization_data'), "get_visualization_data method missing"
            
            self.results.append("✅ UnauthorizedInterventionDetector: Initialized successfully")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ UnauthorizedInterventionDetector: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_detector_manager(self):
        """Test DetectorManager initialization."""
        try:
            from core.config_manager import ConfigManager
            from core.detector_manager import DetectorManager
            
            config = ConfigManager("outputs")
            manager = DetectorManager(config)
            
            # Verify methods
            assert hasattr(manager, 'process_frame'), "process_frame method missing"
            assert hasattr(manager, 'get_detector_names'), "get_detector_names method missing"
            
            names = manager.get_detector_names()
            assert len(names) > 0, "No detectors initialized"
            
            self.results.append("✅ DetectorManager: Initialized with detectors")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ DetectorManager: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_event_factory(self):
        """Test EventFactory initialization."""
        try:
            from severity.event_factory import EventFactory
            
            # Test event creation
            event = EventFactory.create_walkway_violation("Test violation")
            assert event is not None, "Event creation failed"
            assert "severity" in event, "Severity not in event"
            assert event["severity"] == "HIGH", "Walkway violation should be HIGH"
            
            # Test event validation
            is_valid, msg = EventFactory.validate_event(event)
            assert is_valid, f"Event validation failed: {msg}"
            
            # Test unauthorized intervention event
            event2 = EventFactory.create_unauthorized_intervention("Test intervention")
            assert event2["severity"] == "CRITICAL", "Intervention should be CRITICAL"
            
            self.results.append("✅ EventFactory: Validation working")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ EventFactory: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_database_service(self):
        """Test DatabaseService initialization."""
        try:
            from database.database_service import DatabaseService
            
            service = DatabaseService("outputs/compliance_logs.db")
            
            # Verify methods
            assert hasattr(service, 'create_violation'), "create_violation method missing"
            assert hasattr(service, 'get_statistics'), "get_statistics method missing"
            
            self.results.append("✅ DatabaseService: Initialized successfully")
            self.tests_passed += 1
            return True
        except Exception as e:
            self.results.append(f"❌ DatabaseService: {str(e)}")
            self.tests_failed += 1
            return False
    
    def run_all(self):
        """Run all smoke tests."""
        print("=" * 70)
        print("SMOKE TEST - Factory Compliance System")
        print("=" * 70)
        print()
        
        print("🧪 Running Component Tests...")
        print("-" * 70)
        
        self.test_config_manager()
        self.test_event_bus()
        self.test_system_stats()
        self.test_base_detector()
        self.test_walkway_detector()
        self.test_unauthorized_intervention_detector()
        self.test_detector_manager()
        self.test_event_factory()
        self.test_database_service()
        
        print()
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        
        for result in self.results:
            print(result)
        
        print()
        print(f"✅ PASSED: {self.tests_passed}")
        print(f"❌ FAILED: {self.tests_failed}")
        print(f"Total: {self.tests_passed + self.tests_failed}")
        print()
        
        if self.tests_failed == 0:
            print("🎉 ALL SMOKE TESTS PASSED!")
            print("System components are ready for production use.")
            print("=" * 70)
            return True
        else:
            print("⚠️  SOME TESTS FAILED!")
            print("=" * 70)
            return False


def main():
    """Run smoke tests."""
    tester = SmokeTest()
    success = tester.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
