"""
Tests for FastAPI backend (Milestone 5).
"""
import os
import pytest
from fastapi.testclient import TestClient

# Use a test database
os.environ["DATABASE_URL"] = "sqlite:///./test_matchiq.db"

from matchiq.api.main import app
from matchiq.db.database import Base, engine, SessionLocal
from matchiq.db.models import Dataset, Job

# Create tables in test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    # Clear tables before each test
    db = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_dataset(tmp_path):
    # Create dummy csv
    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("id,name\n1,test1\n2,test2")
    
    with open(csv_path, "rb") as f:
        response = client.post(
            "/datasets",
            files={"file": ("dummy.csv", f, "text/csv")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "dummy.csv"
    assert data["row_count"] == 2
    assert "id" in data
    
    return data["id"]

def test_create_and_get_job(tmp_path):
    # First upload two datasets
    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("id,name\n1,test1\n2,test2")
    
    with open(csv_path, "rb") as f:
        res_a = client.post("/datasets", files={"file": ("A.csv", f, "text/csv")}).json()
    with open(csv_path, "rb") as f:
        res_b = client.post("/datasets", files={"file": ("B.csv", f, "text/csv")}).json()
        
    # Create job
    job_payload = {
        "dataset_a_id": res_a["id"],
        "dataset_b_id": res_b["id"],
        "mapping_config": {"name": {"a": ["name"], "b": ["name"]}}
    }
    
    res_job = client.post("/jobs", json=job_payload)
    assert res_job.status_code == 200
    job_data = res_job.json()
    assert job_data["status"] == "PENDING"
    assert job_data["dataset_a_id"] == res_a["id"]
    
    job_id = job_data["id"]
    
    # Get job
    res_get = client.get(f"/jobs/{job_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == job_id
