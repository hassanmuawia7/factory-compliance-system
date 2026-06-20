import sys
import os
# Force Python to see the root project folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, ViolationRecord
from src.database.models import ViolationRecord

# Create the database file inside your outputs folder
DB_PATH = "sqlite:///outputs/compliance_logs.db"

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Creates the database table if it doesn't exist yet."""
    os.makedirs("outputs", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized at outputs/compliance_logs.db")

def log_event_to_db(event_dict):
    """Takes the JSON event, determines the escalation route, and saves it."""
    session = SessionLocal()
    
    try:
        if event_dict["severity"] in ["HIGH", "CRITICAL"]:
            escalation_action = "Real-time alert triggered + DB log"
        else:
            escalation_action = "Logged to DB only"
            
        new_record = ViolationRecord(
            event_id=event_dict["event_id"],
            timestamp=event_dict["timestamp"],  # Directly passing the string
            behavior_class=event_dict["behavior_class"],
            policy_rule_ref=event_dict["policy_rule_ref"],
            severity=event_dict["severity"],
            description=event_dict["description"],
            escalation_action=escalation_action
        )
        
        session.add(new_record)
        session.commit()
        print(f"💾 Event {event_dict['event_id']} saved to database!")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()