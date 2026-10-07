"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from matchiq.api.routers import datasets, jobs

app = FastAPI(
    title="MatchIQ API",
    description="Backend API for MatchIQ entity resolution",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(jobs.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
