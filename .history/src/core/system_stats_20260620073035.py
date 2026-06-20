"""
System Statistics Tracker
Tracks real-time system metrics and performance statistics.

Tracks:
- Frames processed
- Violations by severity
- Violations by behavior type
- Performance metrics
"""

from typing import Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Statistics:
    """Represents system statistics snapshot."""
    frames_processed: int = 0
    total_violations: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    walkway_violations: int = 0
    unauthorized_interventions: int = 0
    start_time: datetime = None
    
    def get_duration_seconds(self) -> float:
        """Get elapsed time in seconds since start."""
        if self.start_time is None:
            return 0
        return (datetime.now() - self.start_time).total_seconds()


class SystemStats:
    """
    Tracks real-time system statistics.
    
    Thread-safe (uses basic atomic operations).
    """
    
    def __init__(self):
        """Initialize statistics tracker."""
        self._stats = Statistics(start_time=datetime.now())
    
    def increment_frame(self) -> None:
        """Record that a frame was processed."""
        self._stats.frames_processed += 1
    
    def record_violation(
        self,
        severity: str,
        behavior_class: str
    ) -> None:
        """
        Record a detected violation.
        
        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            behavior_class: Behavior type (walkway_violation, unauthorized_intervention, etc.)
        """
        self._stats.total_violations += 1
        
        # Track by severity
        if severity == "CRITICAL":
            self._stats.critical_count += 1
        elif severity == "HIGH":
            self._stats.high_count += 1
        elif severity == "MEDIUM":
            self._stats.medium_count += 1
        elif severity == "LOW":
            self._stats.low_count += 1
        
        # Track by behavior
        if behavior_class == "walkway_violation":
            self._stats.walkway_violations += 1
        elif behavior_class == "unauthorized_intervention":
            self._stats.unauthorized_interventions += 1
    
    def get_statistics(self) -> Statistics:
        """Get current statistics snapshot."""
        return self._stats
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get human-readable statistics summary.
        
        Returns:
            Dictionary with formatted statistics
        """
        stats = self._stats
        duration = stats.get_duration_seconds()
        fps = stats.frames_processed / duration if duration > 0 else 0
        
        return {
            "frames_processed": stats.frames_processed,
            "fps": round(fps, 2),
            "total_violations": stats.total_violations,
            "critical": stats.critical_count,
            "high": stats.high_count,
            "medium": stats.medium_count,
            "low": stats.low_count,
            "walkway_violations": stats.walkway_violations,
            "unauthorized_interventions": stats.unauthorized_interventions,
            "duration_seconds": round(duration, 1),
        }
    
    def print_summary(self) -> None:
        """Print formatted statistics summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("SYSTEM STATISTICS SUMMARY")
        print("="*50)
        print(f"Duration: {summary['duration_seconds']}s")
        print(f"Frames Processed: {summary['frames_processed']}")
        print(f"Average FPS: {summary['fps']}")
        print()
        print("Violations:")
        print(f"  Total: {summary['total_violations']}")
        print(f"  🔴 CRITICAL: {summary['critical']}")
        print(f"  🟠 HIGH: {summary['high']}")
        print(f"  🟡 MEDIUM: {summary['medium']}")
        print(f"  🟢 LOW: {summary['low']}")
        print()
        print("By Type:")
        print(f"  Walkway: {summary['walkway_violations']}")
        print(f"  Unauthorized: {summary['unauthorized_interventions']}")
        print("="*50 + "\n")
    
    def reset(self) -> None:
        """Reset all statistics (use with caution)."""
        self._stats = Statistics(start_time=datetime.now())


# Global stats instance
_system_stats = None


def get_system_stats() -> SystemStats:
    """Get global SystemStats instance."""
    global _system_stats
    if _system_stats is None:
        _system_stats = SystemStats()
    return _system_stats


if __name__ == "__main__":
    # Test SystemStats
    stats = SystemStats()
    
    # Simulate activity
    for i in range(100):
        stats.increment_frame()
        if i % 10 == 0:
            stats.record_violation("CRITICAL", "walkway_violation")
        if i % 15 == 0:
            stats.record_violation("HIGH", "unauthorized_intervention")
    
    stats.print_summary()
