"""
Dataset endpoints.
"""
import os
import uuid
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from matchiq.db.database import get_db
from matchiq.db.models import Dataset
from matchiq.api.schemas.dataset import DatasetResponse
from matchiq.io.profiler import profile_dataframe

router = APIRouter(prefix="/datasets", tags=["Datasets"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("", response_model=DatasetResponse)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    dataset_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{dataset_id}_{file.filename}"
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Profile
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding="latin-1")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")

    profile = profile_dataframe(df)
    
    db_dataset = Dataset(
        id=dataset_id,
        filename=file.filename,
        file_path=str(file_path),
        size_bytes=len(content),
        row_count=len(df),
        profile_data=profile
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset

@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: str, n: int = 20, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    try:
        df = pd.read_csv(dataset.file_path, nrows=n)
        return {"columns": df.columns.tolist(), "rows": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read preview: {e}")
