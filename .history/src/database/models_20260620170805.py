from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ViolationRecord(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False)
    timestamp = Column(String, nullable=False)
    clip_id = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    behavior_class = Column(String, nullable=False)
    policy_rule_ref = Column(String, nullable=False)
    event_description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    escalation_action = Column(String, nullable=False)