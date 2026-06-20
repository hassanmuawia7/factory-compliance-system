import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, ViolationRecord

DB_PATH = "sqlite:///outputs/compliance_logs.db"

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

REQUIRED_COLUMNS = {
    "id", "event_id", "timestamp", "clip_id", "zone",
    "behavior_class", "policy_rule_ref", "event_description",
    "severity", "escalation_action"
}


def _ensure_schema() -> None:
    """Recreate violations table when legacy or incomplete schema is detected."""
    inspector = inspect(engine)
    if "violations" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("violations")}
    if "description" in columns or not REQUIRED_COLUMNS.issubset(columns):
        Base.metadata.drop_all(bind=engine, tables=[ViolationRecord.__table__])


def init_db():
    """Create the database table and ensure schema matches models."""
    os.makedirs("outputs", exist_ok=True)
    _ensure_schema()
    Base.metadata.create_all(bind=engine)
    print("Database initialized at outputs/compliance_logs.db")


def log_event_to_db(event_dict):
    """Takes the JSON event and saves it to the database."""
    session = SessionLocal()
    
    try:
        escalation_action = event_dict.get("escalation_action")
        if not escalation_action:
            if event_dict.get("severity") in ["HIGH", "CRITICAL"]:
                escalation_action = "Real-time alert triggered + DB log"
            else:
                escalation_action = "Logged to DB only"
            
        new_record = ViolationRecord(
            event_id=event_dict["event_id"],
            timestamp=event_dict["timestamp"],
            clip_id=event_dict["clip_id"],
            zone=event_dict["zone"],
            behavior_class=event_dict["behavior_class"],
            policy_rule_ref=event_dict["policy_rule_ref"],
            severity=event_dict["severity"],
            event_description=event_dict["event_description"],
            escalation_action=escalation_action
        )
        
        session.add(new_record)
        session.commit()
        print(f"Event {event_dict['event_id']} saved to database!")
        
    except Exception as e:
        print(f"Database Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
