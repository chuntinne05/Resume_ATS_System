from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.config import get_db
from backend.models.database import JobRequirement, Candidate, Skill
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class JobRequirementCreate(BaseModel):
    job_title: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: int
    education_requirements: Dict[str, Any]

@router.post("/requirements")
async def create_job_requirement(
    job_req: JobRequirementCreate,
    db: Session = Depends(get_db)
):
    """Create job requirement"""
    db_job_req = JobRequirement(
        job_title=job_req.job_title,
        required_skills=job_req.required_skills,
        preferred_skills=job_req.preferred_skills,
        min_experience_years=job_req.min_experience_years,
        education_requirements=job_req.education_requirements
    )
    
    db.add(db_job_req)
    db.commit()
    db.refresh(db_job_req)
    
    return db_job_req

@router.get("/requirements")
async def get_job_requirements(db: Session = Depends(get_db)):
    """Get all job requirements"""
    return db.query(JobRequirement).all()

@router.post("/match/{job_id}")
async def match_candidates(job_id: int, db: Session = Depends(get_db)):
    """Match candidates to job requirements"""
    job_req = db.query(JobRequirement).filter(JobRequirement.id == job_id).first()
    
    if not job_req:
        raise HTTPException(status_code=404, detail="Job requirement not found")
    
    # Simple matching algorithm
    candidates = db.query(Candidate).all()
    matches = []
    
    for candidate in candidates:
        candidate_skills = [skill.skill_name.lower() for skill in candidate.skills]
        required_skills = [skill.lower() for skill in job_req.required_skills]
        
        skill_match_score = len(set(candidate_skills) & set(required_skills)) / len(required_skills) if required_skills else 0
        
        # Calculate total experience
        total_experience = sum(
            exp.duration_months or 0 for exp in candidate.experience
        ) / 12  # Convert to years
        
        experience_match = 1.0 if total_experience >= job_req.min_experience_years else total_experience / job_req.min_experience_years
        
        overall_match = (skill_match_score * 0.7 + experience_match * 0.3) * 100
        
        if overall_match > 30:  # Minimum 30% match
            matches.append({
                "candidate": candidate,
                "match_score": round(overall_match, 2),
                "skill_match": round(skill_match_score * 100, 2),
                "experience_match": round(experience_match * 100, 2)
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "job_requirement": job_req,
        "matches": matches[:20]  # Top 20 matches
    }