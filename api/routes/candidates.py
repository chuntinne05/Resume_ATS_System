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
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "address": candidate.address,
        "overall_score": float(candidate.overall_score) if candidate.overall_score else 0.0,
        "classification": candidate.classification,
        "experience_level": candidate.experience_level.value if candidate.experience_level else None,
        "status": candidate.status.value if candidate.status else None,
        "created_at": candidate.created_at,
        "original_filename": candidate.original_filename,
        "education": [{
            "degree": edu.degree,
            "institution": edu.institution,
            "graduation_year": edu.graduation_year,
            "gpa": float(edu.gpa) if edu.gpa else None,
            "major": edu.major,
            "education_level": edu.education_level.value if edu.education_level else None,
            "is_primary": edu.is_primary,
            "created_at": edu.created_at
        } for edu in candidate.education],
        "experience": [{
            "job_title": exp.job_title,
            "company": exp.company,
            "start_date": exp.start_date.isoformat() if exp.start_date else None,
            "end_date": exp.end_date.isoformat() if exp.end_date else None,
            "is_current": exp.is_current,
            "responsibilities": exp.responsibilities,
            "achievements": exp.achievements,
            "created_at": exp.created_at
        } for exp in candidate.experience],
        "skills": [{
            "skill_name": skill.skill_name,
            "skill_category": skill.skill_category.value if skill.skill_category else None,
            "proficiency_level": skill.proficiency_level.value if skill.proficiency_level else None,
            "years_experience": skill.years_experience,
            "is_verified": skill.is_verified,
            "created_at": skill.created_at
        } for skill in candidate.skills],
        "projects": [{
            "project_name": proj.project_name,
            "description": proj.description,
            "technologies": proj.technologies,
            "project_url": proj.project_url,
            "github_url": proj.github_url,
            "start_date": proj.start_date.isoformat() if proj.start_date else None,
            "end_date": proj.end_date.isoformat() if proj.end_date else None,
            "created_at": proj.created_at
        } for proj in candidate.projects],
        "certifications": [{
            "certification_name": cert.certification_name,
            "issuing_organization": cert.issuing_organization,
            "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
            "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
            "credential_id": cert.credential_id,
            "verification_url": cert.verification_url,
            "is_active": cert.is_active,
            "created_at": cert.created_at
        } for cert in candidate.certifications]
    }

@router.put("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    try:
        status_upper = status.upper()  
        candidate.status = CandidateStatus(status_upper)  
        db.commit()
        return {"message": "Status updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")

@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if candidate.s3_file_key:
        from backend.services.s3_service import s3_service
        s3_service.delete_file(candidate.s3_file_key)
    
    db.delete(candidate)
    db.commit()
    return {"message": "Candidate deleted successfully"}