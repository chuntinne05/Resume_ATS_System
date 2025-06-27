# # main.py
# from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from sqlalchemy.orm import Session
# from typing import List, Optional
# import logging
# import os
# from contextlib import asynccontextmanager

# from backend.database.config import get_db, engine
# from backend.models.database import Base
# from backend.services.resume_processor import resume_processor
# from backend.services.s3_service import s3_service
# from backend.services.ollama_service import ollama_service
# from api.routes import candidates, batches, dashboard, jobs
# from core.config import settings

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     logger.info("Starting Resume ATS System...")
    
#     # Create database tables
#     Base.metadata.create_all(bind=engine)
#     logger.info("Database tables created")
    
#     # Check Ollama service
#     if not ollama_service.is_available():
#         logger.warning("Ollama service is not available. Please ensure Ollama is running.")
#     else:
#         logger.info("Ollama service is available")
    
#     yield
    
#     # Shutdown
#     logger.info("Shutting down Resume ATS System...")

# app = FastAPI(
#     title="Resume ATS System",
#     description="AI-powered Resume Applicant Tracking System",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure properly for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Mount static files
# app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# # Include routers
# app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
# app.include_router(batches.router, prefix="/api/batches", tags=["batches"])
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
# app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

# # @app.get("/")
# # async def root():
# #     return {"message": "Resume ATS System API", "status": "running"}

# @app.get("/", response_class=HTMLResponse)
# async def serve_dashboard():
#     try:
#         with open("static/resume_ats_dashboard.html", "r", encoding="utf-8") as f:
#             return f.read()
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Dashboard HTML file not found")
    
# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     ollama_status = ollama_service.is_available()
    
#     return {
#         "status": "healthy",
#         "services": {
#             "database": "connected",
#             "ollama": "available" if ollama_status else "unavailable",
#             "s3": "configured"
#         }
#     }

# @app.post("/api/upload")
# async def upload_resumes(
#     background_tasks: BackgroundTasks,
#     files: List[UploadFile] = File(...),
#     batch_name: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """Upload and process resume files"""
#     try:
#         # Validate files
#         max_file_size = 10 * 1024 * 1024  # 10MB
#         allowed_extensions = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png'}
        
#         for file in files:
#             if file.size > max_file_size:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"File {file.filename} is too large. Maximum size is 10MB."
#                 )
            
#             file_ext = os.path.splitext(file.filename)[1].lower()
#             if file_ext not in allowed_extensions:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"File {file.filename} has unsupported format. Allowed: {', '.join(allowed_extensions)}"
#                 )
        
#         # Start batch processing
#         batch_id = await resume_processor.process_batch(files, batch_name)
        
#         return {
#             "message": f"Successfully started processing {len(files)} files",
#             "batch_id": batch_id,
#             "files_count": len(files)
#         }
        
#     except Exception as e:
#         logger.error(f"Upload failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/download/{candidate_id}")
# async def download_resume(candidate_id: int, db: Session = Depends(get_db)):
#     """Download original resume file"""
#     try:
#         from backend.models.database import Candidate
#         candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
#         if not candidate:
#             raise HTTPException(status_code=404, detail="Candidate not found")
        
#         if not candidate.s3_file_key:
#             raise HTTPException(status_code=404, detail="Resume file not found")
        
#         # Generate presigned URL
#         download_url = s3_service.generate_presigned_url(candidate.s3_file_key)
        
#         if not download_url:
#             raise HTTPException(status_code=500, detail="Failed to generate download URL")
        
#         return {"download_url": download_url}
        
#     except Exception as e:
#         logger.error(f"Download failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )

# main.py
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

app = FastAPI()

# Serve file tĩnh (HTML, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve trang dashboard
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("resume_ats_dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

# Lấy danh sách ứng viên
@app.get("/api/candidates")
async def get_candidates(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),  # Thêm skip
    limit: int = Query(20, ge=1, le=100),  # Thêm limit
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

# Lấy thống kê dashboard
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

# Tải lên resume
@app.post("/api/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    batch_name: Optional[str] = None
):
    # Đọc nội dung file trong phạm vi request
    file_contents = []
    for file in files:
        contents = await file.read()  # Đọc nội dung file
        file_contents.append((file.filename, contents))  # Lưu tên file và nội dung
    
    # Truyền danh sách (filename, contents) thay vì UploadFile vào process_batch
    batch_id = await resume_processor.process_batch(file_contents, batch_name)
    return {"batch_id": batch_id, "message": "Resumes uploaded and processing started"}

# Xem chi tiết ứng viên
@app.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "overall_score": float(candidate.overall_score),
        "experience_level": candidate.experience_level.value,
        "status": candidate.status.value
    }

# Xóa ứng viên
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