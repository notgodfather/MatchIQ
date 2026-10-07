"""
Background job runner using the core pipeline.
"""
import uuid
import datetime
import traceback
from sqlalchemy.orm import Session

from matchiq.db.database import SessionLocal
from matchiq.db.models import Job, JobStatus, Dataset, MatchPair
from matchiq.pipeline import run_pipeline

def run_job_background(job_id: str):
    """
    Runs the pipeline in the background and updates the DB state.
    """
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return

    try:
        job.status = JobStatus.RUNNING
        job.stage = "loading_data"
        db.commit()

        dataset_a = db.query(Dataset).filter(Dataset.id == job.dataset_a_id).first()
        dataset_b = db.query(Dataset).filter(Dataset.id == job.dataset_b_id).first()
        
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        # base_dir is /Users/ankitranjan/miniproject
        
        model_path = os.path.join(base_dir, "experiments", "results", "model.pkl")
        model_card_path = os.path.join(base_dir, "experiments", "results", "model_card.json")
        
        # Temporary output path
        output_dir = os.path.join(base_dir, "data", "uploads")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"job_{job_id}_results.csv")
        
        job.stage = "running_pipeline"
        job.progress = 0.2
        db.commit()
        
        # Call the core pipeline
        resolved_df = run_pipeline(
            df_a_path=dataset_a.file_path,
            df_b_path=dataset_b.file_path,
            mapping=job.mapping_config,
            model_path=model_path,
            model_card_path=model_card_path,
            output_path=output_path
        )
        
        job.stage = "saving_results"
        job.progress = 0.8
        db.commit()
        
        # Save matches to DB for review loop
        # For a large dataset, we should bulk insert.
        # But we only save the ones resolved as MATCH or REVIEW (which is what pipeline outputs).
        match_objects = []
        import pandas as pd
        for row in resolved_df.itertuples(index=False):
            # Convert row to dict to extract features
            row_dict = row._asdict()
            features = {k: (None if pd.isna(v) else v) for k, v in row_dict.items() if k not in ["id_A", "id_B", "probability", "decision"]}
            
            mp = MatchPair(
                id=str(uuid.uuid4()),
                job_id=job.id,
                record_a_id=str(row.id_A),
                record_b_id=str(row.id_B),
                probability=float(row.probability),
                decision=str(row.decision),
                features=features
            )
            match_objects.append(mp)
            
        db.bulk_save_objects(match_objects)
        
        # Calculate stats
        matches_count = len(resolved_df[resolved_df["decision"] == "MATCH"])
        reviews_count = len(resolved_df[resolved_df["decision"] == "REVIEW"])
        
        job.stats = {
            "auto_matches": matches_count,
            "reviews_needed": reviews_count,
            "total_candidates": len(resolved_df)
        }
        
        job.status = JobStatus.COMPLETED
        job.stage = "done"
        job.progress = 1.0
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        db.commit()
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.stage = "failed"
        job.error = str(e) + "\n" + traceback.format_exc()
        db.commit()
    finally:
        db.close()
