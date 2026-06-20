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
    
    BEHAVIOR_SEVERITY_MAP = {
        "walkway_violation": "HIGH",
        "unauthorized_intervention": "CRITICAL",
        "unknown": "LOW",
    }
    
    BEHAVIOR_POLICY_MAP = {
        "walkway_violation": "POLICY_WALKWAY_001",
        "unauthorized_intervention": "POLICY_SAFETY_002",
        "unknown": "POLICY_DEFAULT",
    }
    
    @staticmethod
    def create_event(
        behavior_class: str,
        description: str,
        clip_id: str,
        zone: str,
        policy_override: Optional[str] = None,
        severity_override: Optional[str] = None
    ) -> Dict:
        """Create a standardized violation event."""
        severity = severity_override or EventFactory.BEHAVIOR_SEVERITY_MAP.get(
            behavior_class, "LOW"
        )
        policy = policy_override or EventFactory.BEHAVIOR_POLICY_MAP.get(
            behavior_class, "POLICY_DEFAULT"
        )
        
        event = {
            "event_id": EventFactory._generate_event_id(),
            "timestamp": datetime.now().isoformat(),
            "clip_id": clip_id,
            "zone": zone,
            "behavior_class": behavior_class,
            "policy_rule_ref": policy,
            "severity": severity,
            "event_description": description,
        }
        
        return event
    
    @staticmethod
    def create_walkway_violation(description: str, clip_id: str, zone: str) -> Dict:
        """Create a walkway violation event."""
        return EventFactory.create_event(
            behavior_class="walkway_violation",
            description=description or "Person detected in restricted walkway zone",
            clip_id=clip_id,
            zone=zone
        )
    
    @staticmethod
    def create_unauthorized_intervention(description: str, clip_id: str, zone: str) -> Dict:
        """Create an unauthorized intervention event."""
        return EventFactory.create_event(
            behavior_class="unauthorized_intervention",
            description=description or "Person without safety vest detected near machinery",
            clip_id=clip_id,
            zone=zone,
            severity_override="CRITICAL"
        )
    
    @staticmethod
    def _generate_event_id() -> str:
        """Generate a unique event ID."""
        return f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    @staticmethod
    def validate_event(event: Dict) -> tuple[bool, str]:
        """Validate an event dictionary against the assignment constraints."""
        required_fields = [
            'event_id', 'timestamp', 'clip_id', 'zone', 
            'behavior_class', 'policy_rule_ref', 'severity', 'event_description'
        ]
        
        for field in required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        if event['severity'] not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            return False, f"Invalid severity: {event['severity']}"
        
        return True, "Valid"

# [SeverityClassifier class remains unchanged...]