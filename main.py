from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import backend.models.database as db_models
from backend.database.config import get_db
from backend.services.resume_processor import resume_processor
from backend.models.database import ProcessingBatch
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.routes import candidates, dashboard, batches, jobs
app = FastAPI()

app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("resume_ats_dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/candidates")
async def get_candidates(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),  
    limit: int = Query(20, ge=1, le=100),  
    db: Session = Depends(get_db)
):
    query = db.query(db_models.Candidate)
    
    if search:
        query = query.filter(
            (db_models.Candidate.full_name.ilike(f"%{search}%")) |
            (db_models.Candidate.email.ilike(f"%{search}%"))
        )
    if status and status != "All Status":
        query = query.filter(db_models.Candidate.status == status)
    if experience_level and experience_level != "All Levels":
        query = query.filter(db_models.Candidate.experience_level == experience_level)
    if min_score:
        query = query.filter(db_models.Candidate.overall_score >= min_score)
        
    total = query.count()
    candidates = query.offset(skip).limit(limit).all()
    return [{
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "overall_score": float(c.overall_score),
        "experience_level": c.experience_level.value,
        "status": c.status.value,
        "created_at": c.created_at.isoformat()
    } for c in candidates]

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_candidates = db.query(db_models.Candidate).count()
    approved_candidates = db.query(db_models.Candidate).filter(
        db_models.Candidate.status == db_models.CandidateStatus.APPROVED
    ).count()
    under_review_candidates = db.query(db_models.Candidate).filter(
        db_models.Candidate.status == db_models.CandidateStatus.REVIEWED
    ).count()
    avg_score = db.query(db_models.Candidate).with_entities(
        func.avg(db_models.Candidate.overall_score)
    ).scalar() or 0.0
    
    return {
        "total_candidates": total_candidates,
        "approved_candidates": approved_candidates,
        "under_review_candidates": under_review_candidates,
        "average_score": float(avg_score)
    }

@app.post("/api/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    batch_name: Optional[str] = None
):
    file_contents = []
    for file in files:
        contents = await file.read() 
        file_contents.append((file.filename, contents))  
    
    batch_id = await resume_processor.process_batch(file_contents, batch_name)
    return {"batch_id": batch_id, "message": "Resumes uploaded and processing started"}

@app.delete("/api/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    db.delete(candidate)
    db.commit()
    return {"message": "Candidate deleted"}

@app.get("/api/batches/{batch_id}/status")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    batch = db.query(ProcessingBatch).filter(ProcessingBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {
        "batch_id": batch.batch_id,
        "status": batch.status,
        "total_files": batch.total_files,
        "processed_files": batch.processed_files,
        "successful_files": batch.successful_files,
        "failed_files": batch.failed_files
    }


# uvicorn main:app --reload --host 0.0.0.0 --port 8000    