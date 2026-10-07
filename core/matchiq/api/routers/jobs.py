"""
Jobs router for running and querying matching pipelines.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from matchiq.db.database import get_db
from matchiq.db.models import Job, Dataset, MatchPair, ReviewLabel
from matchiq.api.schemas.job import JobCreate, JobResponse, MatchPairResponse, ReviewCreate
from matchiq.api.services.runner import run_job_background

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse)
def create_job(job_in: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate datasets exist
    ds_a = db.query(Dataset).filter(Dataset.id == job_in.dataset_a_id).first()
    ds_b = db.query(Dataset).filter(Dataset.id == job_in.dataset_b_id).first()
    if not ds_a or not ds_b:
        raise HTTPException(status_code=400, detail="Invalid dataset IDs")
        
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        dataset_a_id=job_in.dataset_a_id,
        dataset_b_id=job_in.dataset_b_id,
        mapping_config=job_in.mapping_config,
        model_id=job_in.model_id
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Launch background task
    background_tasks.add_task(run_job_background, job_id)
    
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/results", response_model=List[MatchPairResponse])
def get_job_results(
    job_id: str, 
    decision: Optional[str] = None, 
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(MatchPair).filter(MatchPair.job_id == job_id)
    if decision:
        query = query.filter(MatchPair.decision == decision)
        
    pairs = query.offset((page - 1) * page_size).limit(page_size).all()
    return pairs

@router.get("/{job_id}/review-queue", response_model=List[MatchPairResponse])
def get_review_queue(job_id: str, limit: int = 10, db: Session = Depends(get_db)):
    # Find REVIEW decisions that don't have a label yet
    query = db.query(MatchPair).outerjoin(ReviewLabel, MatchPair.id == ReviewLabel.pair_id) \
              .filter(MatchPair.job_id == job_id) \
              .filter(MatchPair.decision == "REVIEW") \
              .filter(ReviewLabel.id == None) \
              .limit(limit)
    return query.all()

@router.post("/{job_id}/reviews")
def submit_review(job_id: str, pair_id: str, review_in: ReviewCreate, db: Session = Depends(get_db)):
    pair = db.query(MatchPair).filter(MatchPair.id == pair_id, MatchPair.job_id == job_id).first()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
        
    label = ReviewLabel(
        id=str(uuid.uuid4()),
        pair_id=pair_id,
        label=review_in.label
    )
    db.add(label)
    
    # Update stats incrementally? For MVP just add label
    db.commit()
    return {"status": "success", "label_id": label.id}

from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/{job_id}/export")
def export_job_results(job_id: str, type: str = "all", db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    query = db.query(MatchPair).filter(MatchPair.job_id == job_id)
    if type == "matches":
        query = query.filter(MatchPair.decision == "MATCH")
    elif type == "review":
        query = query.filter(MatchPair.decision == "REVIEW")
    elif type == "non_matches":
        query = query.filter(MatchPair.decision == "NON_MATCH")
        
    pairs = query.all()
    if not pairs:
        return StreamingResponse(iter(["id_A,id_B,probability,decision\n"]), media_type="text/csv")
        
    # Read datasets to enrich CSV
    dataset_a = db.query(Dataset).filter(Dataset.id == job.dataset_a_id).first()
    dataset_b = db.query(Dataset).filter(Dataset.id == job.dataset_b_id).first()
    
    import os
    import pandas as pd
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    
    # Path handling (uploaded files are in core/data/uploads via dataset.file_path)
    path_a = dataset_a.file_path if os.path.isabs(dataset_a.file_path) else os.path.join(base_dir, "core", dataset_a.file_path)
    path_b = dataset_b.file_path if os.path.isabs(dataset_b.file_path) else os.path.join(base_dir, "core", dataset_b.file_path)
    
    try:
        df_a = pd.read_csv(path_a, dtype=str).set_index("rec_id").add_prefix("A_")
        df_b = pd.read_csv(path_b, dtype=str).set_index("rec_id").add_prefix("B_")
    except Exception as e:
        # Fallback to simple export if files missing or malformed
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id_A", "id_B", "probability", "decision"])
        for p in pairs:
            writer.writerow([p.record_a_id, p.record_b_id, p.probability, p.decision])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_export.csv"}
        )
        
    # Build dataframe of pairs
    pairs_data = [{"id_A": p.record_a_id, "id_B": p.record_b_id, "probability": p.probability, "decision": p.decision} for p in pairs]
    df_pairs = pd.DataFrame(pairs_data)
    
    # Join Dataframes
    df_export = df_pairs.merge(df_a, left_on="id_A", right_index=True, how="left")
    df_export = df_export.merge(df_b, left_on="id_B", right_index=True, how="left")
    
    output = io.StringIO()
    df_export.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_export.csv"}
    )

