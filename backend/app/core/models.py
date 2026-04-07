from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class TrialSession(Base):
    __tablename__ = "trial_sessions"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="completed")
    initial_arms = Column(JSON)  # List of arms that started the trial
    final_phase = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Establish relationship to the phases
    phases = relationship("PhaseLog", back_populates="trial", cascade="all, delete-orphan")

class PhaseLog(Base):
    __tablename__ = "phase_logs"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trial_sessions.id"))
    phase_number = Column(Integer)
    event_type = Column(String)  # 'stats' or 'action'
    
    # Store the complex dict/metrics payload entirely in JSON to retain flexibility
    data_payload = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trial = relationship("TrialSession", back_populates="phases")
