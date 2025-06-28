from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.config import get_db
from backend.models.database import ProcessingBatch, ProcessingLog
from typing import List

router = APIRouter()

@router.get("/")
async def get_batches(db: Session = Depends(get_db)):
    batches = db.query(ProcessingBatch).order_by(ProcessingBatch.created_at.desc()).all()
    return batches

@router.get("/{batch_id}")
async def get_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.query(ProcessingBatch).filter(ProcessingBatch.batch_id == batch_id).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    logs = db.query(ProcessingLog).filter(ProcessingLog.batch_id == batch_id).all()
    
    return {
        "batch": batch,
        "logs": logs
    }

