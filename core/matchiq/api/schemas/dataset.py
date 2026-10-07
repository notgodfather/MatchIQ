"""
Pydantic schemas for Datasets.
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class DatasetResponse(BaseModel):
    id: str
    filename: str
    size_bytes: int
    row_count: int
    profile_data: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True
