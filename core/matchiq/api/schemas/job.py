"""
Pydantic schemas for Jobs.
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
from matchiq.db.models import JobStatus

class JobCreate(BaseModel):
    dataset_a_id: str
    dataset_b_id: str
    mapping_config: Dict[str, Any]
    model_id: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    dataset_a_id: str
    dataset_b_id: str
    status: JobStatus
    stage: str
    progress: float
    error: Optional[str] = None
    stats: Optional[Any] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MatchPairResponse(BaseModel):
    id: str
    job_id: str
    record_a_id: str
    record_b_id: str
    probability: float
    decision: str
    features: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        
class ReviewCreate(BaseModel):
    label: str # "MATCH" or "NON_MATCH"
