"""
SQLAlchemy models for MatchIQ.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from matchiq.db.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    profile_data = Column(JSON, nullable=True) # JSON containing columns, stats
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    dataset_a_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    dataset_b_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    mapping_config = Column(JSON, nullable=False)
    model_id = Column(String, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    stage = Column(String, default="queued")
    progress = Column(Float, default=0.0)
    error = Column(String, nullable=True)
    stats = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    dataset_a = relationship("Dataset", foreign_keys=[dataset_a_id])
    dataset_b = relationship("Dataset", foreign_keys=[dataset_b_id])

class MatchPair(Base):
    __tablename__ = "match_pairs"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    record_a_id = Column(String, nullable=False, index=True)
    record_b_id = Column(String, nullable=False, index=True)
    probability = Column(Float, nullable=False)
    decision = Column(String, nullable=False) # MATCH, REVIEW, NON_MATCH
    features = Column(JSON, nullable=True)
    
    job = relationship("Job")

class ReviewLabel(Base):
    __tablename__ = "review_labels"

    id = Column(String, primary_key=True, index=True)
    pair_id = Column(String, ForeignKey("match_pairs.id"), nullable=False, index=True)
    label = Column(String, nullable=False) # MATCH, NON_MATCH
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    pair = relationship("MatchPair")
