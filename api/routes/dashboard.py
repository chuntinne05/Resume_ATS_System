from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.config import get_db
from backend.models.database import *

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    total_candidates = db.query(func.count(Candidate.id)).scalar()
    
    candidates_by_status = db.query(
        Candidate.status,
        func.count(Candidate.id)
    ).group_by(Candidate.status).all()
    
    candidates_by_experience = db.query(
        Candidate.experience_level,
        func.count(Candidate.id)
    ).group_by(Candidate.experience_level).all()
    
    avg_score = db.query(func.avg(Candidate.overall_score)).scalar() or 0
    
    top_skills = db.query(
        Skill.skill_name,
        func.count(Skill.id).label('count')
    ).group_by(Skill.skill_name).order_by(func.count(Skill.id).desc()).limit(10).all()
    
    recent_batches = db.query(ProcessingBatch).order_by(
        ProcessingBatch.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_candidates": total_candidates,
        "candidates_by_status": dict(candidates_by_status),
        "candidates_by_experience": dict(candidates_by_experience),
        "average_score": round(float(avg_score), 2),
        "top_skills": [{"skill": skill, "count": count} for skill, count in top_skills],
        "recent_batches": recent_batches
    }

