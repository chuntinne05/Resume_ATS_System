from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from typing import List
from sqlalchemy.orm import Session
from database.config import SessionLocal
from models.database import Candidate
from services.resume_processor import resume_processor
import os

app = FastAPI()

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        batch_id = await resume_processor.process_batch([file])
        return {"batch_id": batch_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")

@app.get("/api/candidates")
def get_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).all()
    return [{
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "classification": c.classification,
        "overall_score": float(c.overall_score)
    } for c in candidates]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)