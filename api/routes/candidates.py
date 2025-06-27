# api/routes/candidates.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from backend.database.config import get_db
from backend.models.database import *
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class CandidateResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    overall_score: float
    classification: Optional[str]
    experience_level: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CandidateDetailResponse(CandidateResponse):
    address: Optional[str]
    original_filename: Optional[str]
    education: List[dict]
    experience: List[dict]
    skills: List[dict]
    projects: List[dict]
    certifications: List[dict]

@router.get("/", response_model=List[CandidateResponse])
async def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get all candidates with filtering and pagination"""
    query = db.query(Candidate)
    
    if search:
        query = query.filter(
            Candidate.full_name.contains(search) |
            Candidate.email.contains(search) |
            Candidate.classification.contains(search)
        )
    
    if status:
        query = query.filter(Candidate.status == status)
    
    if experience_level:
        query = query.filter(Candidate.experience_level == experience_level)
    
    if min_score is not None:
        query = query.filter(Candidate.overall_score >= min_score)
    
    candidates = query.offset(skip).limit(limit).all()
    return candidates

@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate details"""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.education),
        joinedload(Candidate.experience),
        joinedload(Candidate.skills),
        joinedload(Candidate.projects),
        joinedload(Candidate.certifications)
    ).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        **candidate.__dict__,
        "education": [edu.__dict__ for edu in candidate.education],
        "experience": [exp.__dict__ for exp in candidate.experience],
        "skills": [skill.__dict__ for skill in candidate.skills],
        "projects": [proj.__dict__ for proj in candidate.projects],
        "certifications": [cert.__dict__ for cert in candidate.certifications]
    }

@router.put("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update candidate status"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    try:
        candidate.status = CandidateStatus(status)
        db.commit()
        return {"message": "Status updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")

@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Delete candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Delete S3 file if exists
    if candidate.s3_file_key:
        from backend.services.s3_service import s3_service
        s3_service.delete_file(candidate.s3_file_key)
    
    db.delete(candidate)
    db.commit()
    return {"message": "Candidate deleted successfully"}