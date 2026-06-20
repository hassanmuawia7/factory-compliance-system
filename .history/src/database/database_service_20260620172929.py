"""
Database Service Layer - CRUD Operations & Utilities
Provides clean database access without exposing SQLAlchemy directly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.database.db_manager import SessionLocal, engine
from src.database.models import ViolationRecord
import pandas as pd


class DatabaseService:
    """Service layer for all database operations."""
    
    @staticmethod
    def get_session() -> Session:
        """Get a new database session."""
        return SessionLocal()
    
    @staticmethod
    def create_violation(event_dict: dict) -> bool:
        session = DatabaseService.get_session()
        try:
            if event_dict.get("severity") in ["HIGH", "CRITICAL"]:
                escalation_action = "Real-time alert triggered + DB log"
            else:
                escalation_action = "Logged to DB only"
            
            record = ViolationRecord(
                event_id=event_dict["event_id"],
                timestamp=event_dict["timestamp"],
                clip_id=event_dict["clip_id"],
                zone=event_dict["zone"],
                behavior_class=event_dict["behavior_class"],
                policy_rule_ref=event_dict["policy_rule_ref"],
                event_description=event_dict["event_description"],
                severity=event_dict["severity"],
                escalation_action=escalation_action
            )
            
            session.add(record)
            session.commit()
            print(f"✅ Event {event_dict['event_id']} saved to database!")
            return True
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def get_all_violations() -> pd.DataFrame:
        """
        Retrieve all violations as pandas DataFrame.
        
        Returns:
            pd.DataFrame: All violations
        """
        session = DatabaseService.get_session()
        try:
            records = session.query(ViolationRecord).all()
            data = [{
                'id': r.id,
                'event_id': r.event_id,
                'timestamp': r.timestamp,
                'behavior_class': r.behavior_class,
                'policy_rule_ref': r.policy_rule_ref,
                'severity': r.severity,
                'description': r.description,
                'escalation_action': r.escalation_action
            } for r in records]
            return pd.DataFrame(data)
        finally:
            session.close()
    
    @staticmethod
    def get_violations_by_severity(severity: str, limit: int = None) -> pd.DataFrame:
        """
        Get violations filtered by severity.
        
        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            limit: Maximum number of records to return
            
        Returns:
            pd.DataFrame: Filtered violations
        """
        session = DatabaseService.get_session()
        try:
            query = session.query(ViolationRecord).filter_by(severity=severity)
            if limit:
                query = query.limit(limit)
            
            records = query.all()
            data = [{
                'id': r.id,
                'event_id': r.event_id,
                'timestamp': r.timestamp,
                'behavior_class': r.behavior_class,
                'policy_rule_ref': r.policy_rule_ref,
                'severity': r.severity,
                'description': r.description,
                'escalation_action': r.escalation_action
            } for r in records]
            return pd.DataFrame(data)
        finally:
            session.close()
    
    @staticmethod
    def get_violations_by_behavior(behavior_class: str) -> pd.DataFrame:
        """
        Get violations filtered by behavior class.
        
        Args:
            behavior_class: Behavior class name
            
        Returns:
            pd.DataFrame: Filtered violations
        """
        session = DatabaseService.get_session()
        try:
            records = session.query(ViolationRecord).filter_by(
                behavior_class=behavior_class
            ).all()
            
            data = [{
                'id': r.id,
                'event_id': r.event_id,
                'timestamp': r.timestamp,
                'behavior_class': r.behavior_class,
                'policy_rule_ref': r.policy_rule_ref,
                'severity': r.severity,
                'description': r.description,
                'escalation_action': r.escalation_action
            } for r in records]
            return pd.DataFrame(data)
        finally:
            session.close()
    
    @staticmethod
    def get_violations_by_date_range(start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get violations within a date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            pd.DataFrame: Violations in date range
        """
        session = DatabaseService.get_session()
        try:
            start_str = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
            end_str = end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
            
            records = session.query(ViolationRecord).filter(
                ViolationRecord.timestamp >= start_str,
                ViolationRecord.timestamp <= end_str
            ).all()
            
            data = [{
                'id': r.id,
                'event_id': r.event_id,
                'timestamp': r.timestamp,
                'behavior_class': r.behavior_class,
                'policy_rule_ref': r.policy_rule_ref,
                'severity': r.severity,
                'description': r.description,
                'escalation_action': r.escalation_action
            } for r in records]
            return pd.DataFrame(data)
        finally:
            session.close()
    
    @staticmethod
    def get_statistics() -> dict:
        """
        Get database statistics.
        
        Returns:
            dict: Statistics including counts by severity and behavior
        """
        session = DatabaseService.get_session()
        try:
            total = session.query(ViolationRecord).count()
            critical = session.query(ViolationRecord).filter_by(severity='CRITICAL').count()
            high = session.query(ViolationRecord).filter_by(severity='HIGH').count()
            medium = session.query(ViolationRecord).filter_by(severity='MEDIUM').count()
            low = session.query(ViolationRecord).filter_by(severity='LOW').count()
            
            # Calculate compliance score
            penalty = (critical * 5) + (high * 2) + (medium * 0.5)
            compliance_score = max(0, min(100, 100 - penalty))
            
            # Get behavior distribution
            behavior_counts = session.query(ViolationRecord.behavior_class).count()
            
            return {
                'total_violations': total,
                'critical_count': critical,
                'high_count': high,
                'medium_count': medium,
                'low_count': low,
                'compliance_score': compliance_score,
                'database_connected': True
            }
        except Exception as e:
            print(f"❌ Statistics Error: {e}")
            return {
                'total_violations': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'compliance_score': 100,
                'database_connected': False
            }
        finally:
            session.close()
    
    @staticmethod
    def delete_violation(event_id: str) -> bool:
        """
        Delete a violation record by event_id.
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            bool: True if successful
        """
        session = DatabaseService.get_session()
        try:
            session.query(ViolationRecord).filter_by(event_id=event_id).delete()
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Delete Error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def get_recent_violations(limit: int = 10) -> pd.DataFrame:
        """
        Get most recent violations.
        
        Args:
            limit: Number of recent violations to return
            
        Returns:
            pd.DataFrame: Recent violations
        """
        session = DatabaseService.get_session()
        try:
            records = session.query(ViolationRecord).order_by(
                ViolationRecord.timestamp.desc()
            ).limit(limit).all()
            
            data = [{
                'id': r.id,
                'event_id': r.event_id,
                'timestamp': r.timestamp,
                'behavior_class': r.behavior_class,
                'policy_rule_ref': r.policy_rule_ref,
                'severity': r.severity,
                'description': r.description,
                'escalation_action': r.escalation_action
            } for r in records]
            return pd.DataFrame(data)
        finally:
            session.close()


if __name__ == "__main__":
    # Test the service
    stats = DatabaseService.get_statistics()
    print("\n📊 Database Statistics:")
    print(f"  Total Violations: {stats['total_violations']}")
    print(f"  Critical: {stats['critical_count']}")
    print(f"  High: {stats['high_count']}")
    print(f"  Compliance Score: {stats['compliance_score']:.1f}%")
