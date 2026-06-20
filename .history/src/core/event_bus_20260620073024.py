"""
Event Bus
Centralized event routing system for the compliance monitoring system.

This module provides:
1. Event publishing and subscription pattern
2. Event filtering and routing
3. Listener notification
4. Type-safe event handling
"""

from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Types of events in the system."""
    VIOLATION_DETECTED = "violation_detected"
    CRITICAL_VIOLATION = "critical_violation"
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    FRAME_PROCESSED = "frame_processed"


@dataclass
class Event:
    """Represents a system event."""
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """
    Centralized event bus for system-wide event routing.
    
    Implements pub-sub pattern for decoupled component communication.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._listeners: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._all_listeners: List[Callable] = []
        self._event_history: List[Event] = []
        self._critical_events: List[Event] = []
    
    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event is published
        """
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to all events.
        
        Args:
            callback: Function to call when any event is published
        """
        if callback not in self._all_listeners:
            self._all_listeners.append(callback)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Store in history
        self._event_history.append(event)
        
        # Track critical events
        if event.event_type == EventType.CRITICAL_VIOLATION:
            self._critical_events.append(event)
        
        # Notify type-specific listeners
        for callback in self._listeners[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                print(f"❌ Error in event callback: {e}")
        
        # Notify all-events listeners
        for callback in self._all_listeners:
            try:
                callback(event)
            except Exception as e:
                print(f"❌ Error in all-events callback: {e}")
    
    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from specific event type.
        
        Args:
            event_type: Type of event to stop listening for
            callback: Callback to remove
        """
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
    
    def get_event_history(self, event_type: EventType = None) -> List[Event]:
        """
        Get historical events.
        
        Args:
            event_type: Filter by event type (None = all)
        
        Returns:
            List of events
        """
        if event_type is None:
            return self._event_history.copy()
        
        return [e for e in self._event_history if e.event_type == event_type]
    
    def get_critical_events(self) -> List[Event]:
        """Get all critical violation events."""
        return self._critical_events.copy()
    
    def get_event_count(self, event_type: EventType = None) -> int:
        """
        Get count of events.
        
        Args:
            event_type: Filter by event type (None = all)
        
        Returns:
            Number of events
        """
        if event_type is None:
            return len(self._event_history)
        
        return len([e for e in self._event_history if e.event_type == event_type])
    
    def clear_history(self) -> None:
        """Clear event history (use with caution)."""
        self._event_history.clear()
        self._critical_events.clear()


# Global event bus instance
_event_bus = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


if __name__ == "__main__":
    # Test the EventBus
    bus = EventBus()
    
    def on_violation(event: Event):
        print(f"🚨 Violation detected: {event.payload}")
    
    def on_any_event(event: Event):
        print(f"📢 Event: {event.event_type.value} at {event.timestamp}")
    
    # Subscribe
    bus.subscribe(EventType.VIOLATION_DETECTED, on_violation)
    bus.subscribe_all(on_any_event)
    
    # Publish
    test_event = Event(
        event_type=EventType.VIOLATION_DETECTED,
        payload={"violation": "test"}
    )
    bus.publish(test_event)
    
    print(f"\nTotal events: {bus.get_event_count()}")
