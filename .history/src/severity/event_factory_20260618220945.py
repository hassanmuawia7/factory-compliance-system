"""
Event Factory - Centralized Event Generation & Severity Classification
Provides reusable event creation with proper severity classification.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class BehaviorClass(Enum):
    """Enum of supported behavior classes."""
    WALKWAY_VIOLATION = "walkway_violation"
    UNAUTHORIZED_INTERVENTION = "unauthorized_intervention"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Severity levels with numeric scores."""
    CRITICAL = ("CRITICAL", 5)
    HIGH = ("HIGH", 2)
    MEDIUM = ("MEDIUM", 1)
    LOW = ("LOW", 0)


class EventFactory:
    """Factory for creating standardized compliance events."""
    
    # Severity mapping by behavior type
    BEHAVIOR_SEVERITY_MAP = {
        "walkway_violation": "HIGH",
        "unauthorized_intervention": "CRITICAL",
        "unknown": "LOW",
    }
    
    # Default policy references
    BEHAVIOR_POLICY_MAP = {
        "walkway_violation": "POLICY_WALKWAY_001",
        "unauthorized_intervention": "POLICY_SAFETY_002",
        "unknown": "POLICY_DEFAULT",
    }
    
    @staticmethod
    def create_event(
        behavior_class: str,
        description: str,
        policy_override: Optional[str] = None,
        severity_override: Optional[str] = None
    ) -> Dict:
        """
        Create a standardized violation event.
        
        Args:
            behavior_class: Type of behavior detected
            description: Event description
            policy_override: Custom policy reference
            severity_override: Custom severity level
            
        Returns:
            dict: Standardized event dictionary
        """
        # Get severity and policy
        severity = severity_override or EventFactory.BEHAVIOR_SEVERITY_MAP.get(
            behavior_class, "LOW"
        )
        policy = policy_override or EventFactory.BEHAVIOR_POLICY_MAP.get(
            behavior_class, "POLICY_DEFAULT"
        )
        
        event = {
            "event_id": EventFactory._generate_event_id(),
            "timestamp": datetime.now().isoformat(),
            "behavior_class": behavior_class,
            "policy_rule_ref": policy,
            "severity": severity,
            "description": description,
        }
        
        return event
    
    @staticmethod
    def create_walkway_violation(description: str) -> Dict:
        """
        Create a walkway violation event.
        
        Args:
            description: Event description
            
        Returns:
            dict: Walkway violation event
        """
        return EventFactory.create_event(
            behavior_class="walkway_violation",
            description=description or "Person detected in restricted walkway zone"
        )
    
    @staticmethod
    def create_unauthorized_intervention(description: str) -> Dict:
        """
        Create an unauthorized intervention event.
        
        Args:
            description: Event description
            
        Returns:
            dict: Unauthorized intervention event
        """
        return EventFactory.create_event(
            behavior_class="unauthorized_intervention",
            description=description or "Person without safety vest detected near machinery",
            severity_override="CRITICAL"
        )
    
    @staticmethod
    def _generate_event_id() -> str:
        """Generate a unique event ID."""
        return f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    @staticmethod
    def classify_severity(behavior_class: str) -> str:
        """
        Classify severity based on behavior class.
        
        Args:
            behavior_class: Behavior class name
            
        Returns:
            str: Severity level
        """
        return EventFactory.BEHAVIOR_SEVERITY_MAP.get(behavior_class, "LOW")
    
    @staticmethod
    def get_policy_for_behavior(behavior_class: str) -> str:
        """
        Get policy reference for a behavior class.
        
        Args:
            behavior_class: Behavior class name
            
        Returns:
            str: Policy reference
        """
        return EventFactory.BEHAVIOR_POLICY_MAP.get(behavior_class, "POLICY_DEFAULT")
    
    @staticmethod
    def validate_event(event: Dict) -> tuple[bool, str]:
        """
        Validate an event dictionary.
        
        Args:
            event: Event dictionary to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = [
            'event_id', 'timestamp', 'behavior_class', 
            'policy_rule_ref', 'severity', 'description'
        ]
        
        for field in required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        if event['severity'] not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            return False, f"Invalid severity: {event['severity']}"
        
        if not isinstance(event['timestamp'], str):
            return False, "Timestamp must be a string"
        
        return True, "Valid"


class SeverityClassifier:
    """Classify event severity based on various factors."""
    
    @staticmethod
    def calculate_compliance_impact(
        critical_count: int,
        high_count: int,
        medium_count: int
    ) -> float:
        """
        Calculate overall compliance score impact.
        
        Args:
            critical_count: Number of critical violations
            high_count: Number of high violations
            medium_count: Number of medium violations
            
        Returns:
            float: Compliance score (0-100)
        """
        penalty = (critical_count * 5) + (high_count * 2) + (medium_count * 0.5)
        score = max(0, min(100, 100 - penalty))
        return score
    
    @staticmethod
    def get_severity_color(severity: str) -> str:
        """
        Get color code for severity level.
        
        Args:
            severity: Severity level
            
        Returns:
            str: Hex color code
        """
        color_map = {
            "CRITICAL": "#EF4444",
            "HIGH": "#F97316",
            "MEDIUM": "#EAB308",
            "LOW": "#22C55E",
        }
        return color_map.get(severity, "#94A3B8")


if __name__ == "__main__":
    # Test event creation
    event1 = EventFactory.create_walkway_violation(
        "Person detected in walkway zone"
    )
    print("\n✅ Walkway Violation Event:")
    print(f"  Event ID: {event1['event_id']}")
    print(f"  Severity: {event1['severity']}")
    print(f"  Policy: {event1['policy_rule_ref']}")
    
    event2 = EventFactory.create_unauthorized_intervention(
        "Person without safety equipment near machinery"
    )
    print("\n✅ Unauthorized Intervention Event:")
    print(f"  Event ID: {event2['event_id']}")
    print(f"  Severity: {event2['severity']}")
    print(f"  Policy: {event2['policy_rule_ref']}")
    
    # Test validation
    is_valid, msg = EventFactory.validate_event(event1)
    print(f"\n✅ Validation: {msg}")
