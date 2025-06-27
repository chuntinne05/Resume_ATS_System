# Resume ATS System - Chi tiết Implementation

## Tech Stack Modifications

### Database Layer

- **Primary Database**: MySQL 8.0+ (thay vì PostgreSQL + MongoDB)
- **Connection**: mysql-connector-python hoặc PyMySQL
- **ORM**: SQLAlchemy với MySQL dialect
- **Migration**: Alembic

### AI/ML Layer

- **Local LLM**: Ollama với DeepSeek R1-8B
- **OCR**: AWS Textract + Tesseract fallback
- **Text Processing**: spaCy, NLTK
- **Validation**: Custom rule-based system

### Storage Layer

- **File Storage**: AWS S3
- **CDN**: AWS CloudFront
- **Local Cache**: Redis (temporary files)

## Phase 1: Database Setup với MySQL

### 1.1 MySQL Database Schema

```sql
-- Tạo database
CREATE DATABASE resume_ats CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE resume_ats;

-- Bảng candidates (thông tin chính)
CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    overall_score DECIMAL(5,2) DEFAULT 0.00,
    classification VARCHAR(100),
    experience_level ENUM('Entry', 'Mid', 'Senior', 'Lead') DEFAULT 'Entry',
    status ENUM('New', 'Reviewed', 'Approved', 'Rejected') DEFAULT 'New',
    original_filename VARCHAR(255),
    s3_file_key VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_classification (classification),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Bảng education
CREATE TABLE education (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    degree VARCHAR(255),
    institution VARCHAR(255),
    graduation_year YEAR,
    gpa DECIMAL(3,2),
    major VARCHAR(255),
    education_level ENUM('High School', 'Associate', 'Bachelor', 'Master', 'PhD', 'Other'),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_graduation_year (graduation_year)
);

-- Bảng experience
CREATE TABLE experience (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    job_title VARCHAR(255),
    company VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    responsibilities JSON,
    achievements JSON,
    duration_months INT GENERATED ALWAYS AS (
        CASE
            WHEN end_date IS NOT NULL THEN
                TIMESTAMPDIFF(MONTH, start_date, end_date)
            ELSE
                TIMESTAMPDIFF(MONTH, start_date, CURDATE())
        END
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_start_date (start_date),
    INDEX idx_company (company)
);

-- Bảng skills
CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    skill_category ENUM('Technical', 'Soft', 'Language', 'Certification', 'Tool', 'Framework') NOT NULL,
    proficiency_level ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Intermediate',
    years_experience INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE KEY unique_candidate_skill (candidate_id, skill_name),
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_skill_category (skill_category),
    INDEX idx_skill_name (skill_name)
);

-- Bảng projects
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    project_name VARCHAR(255),
    description TEXT,
    technologies JSON,
    project_url VARCHAR(500),
    github_url VARCHAR(500),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_id (candidate_id)
);

-- Bảng certifications
CREATE TABLE certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    verification_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_certification_name (certification_name)
);

-- Bảng batch processing
CREATE TABLE processing_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(36) UNIQUE NOT NULL,
    batch_name VARCHAR(255),
    total_files INT DEFAULT 0,
    processed_files INT DEFAULT 0,
    successful_files INT DEFAULT 0,
    failed_files INT DEFAULT 0,
    status ENUM('Pending', 'Processing', 'Completed', 'Failed') DEFAULT 'Pending',
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status)
);

-- Bảng processing logs
CREATE TABLE processing_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL,
    candidate_id INT,
    filename VARCHAR(255) NOT NULL,
    file_size INT,
    s3_key VARCHAR(500),
    processing_status ENUM('Pending', 'Processing', 'Success', 'Failed') DEFAULT 'Pending',
    extraction_confidence DECIMAL(3,2),
    error_message TEXT,
    processing_time_seconds DECIMAL(10,3),
    llm_response_time DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL,
    INDEX idx_batch_id (batch_id),
    INDEX idx_processing_status (processing_status),
    INDEX idx_filename (filename)
);

-- Bảng extracted_text (lưu raw text)
CREATE TABLE extracted_text (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    raw_text LONGTEXT,
    processed_text LONGTEXT,
    extraction_method ENUM('PDF', 'DOCX', 'OCR') NOT NULL,
    page_count INT DEFAULT 1,
    word_count INT,
    confidence_score DECIMAL(3,2),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_id (candidate_id)
);

-- Bảng job_requirements (để matching)
CREATE TABLE job_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    required_skills JSON,
    preferred_skills JSON,
    min_experience_years INT DEFAULT 0,
    education_requirements JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_title (job_title)
);
```

### 1.2 MySQL Configuration

```python
# database/config.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'resume_ats'),
    'charset': 'utf8mb4'
}

DATABASE_URL = f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"

# Engine configuration for production
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False  # Set to True for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Phase 2: Ollama + DeepSeek R1-8B Setup

### 2.2 Ollama Service Class

```python
# services/ollama_service.py
import requests
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class ExtractionResult:
    success: bool
    data: Dict[str, Any]
    confidence: float
    processing_time: float
    error_message: Optional[str] = None

class OllamaService:
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "deepseek-r1:8b"):
        self.base_url = f"http://{host}:{port}"
        self.model = model
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Kiểm tra Ollama service có available không"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def extract_resume_info(self, resume_text: str) -> ExtractionResult:
            ....

    def _build_extraction_prompt(self, resume_text: str) -> str:
            ....

    def _call_ollama(self, prompt: str) -> Optional[str]:
            ....
    def _parse_response(self, response: str) -> Dict[str, Any]:
            ....
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
            ....

    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Tính confidence score dựa trên completeness của data"""
            ....

# Configuration
OLLAMA_CONFIG = {
    'host': os.getenv('OLLAMA_HOST', 'localhost'),
    'port': int(os.getenv('OLLAMA_PORT', 11434)),
    'model': os.getenv('OLLAMA_MODEL', 'deepseek-r1:8b')
}

# Singleton instance
ollama_service = OllamaService(**OLLAMA_CONFIG)
```

## Phase 3: AWS S3 Integration

### 3.1 S3 Service Class

```python
# services/s3_service.py
import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import uuid
from pathlib import Path
import mimetypes

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'resume-ats-files')
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN', '')

    def upload_file(self, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to S3"""
            ....

    def download_file(self, s3_key: str) -> Optional[bytes]:
        """Download file from S3"""
            ....

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
            ....

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
            ....

# Singleton instance
s3_service = S3Service()
```

### 3.2 File Processing Service

```python
# services/file_processor.py
import os
import tempfile
from typing import Dict, Any, Optional
import PyPDF2
import pdfplumber
from docx import Document
import boto3
from PIL import Image
import pytesseract
import logging

class FileProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.textract_client = boto3.client(
            'textract',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    def extract_text_from_file(self, file_content: bytes, filename: str, s3_key: str) -> Dict[str, Any]:
        """Extract text from uploaded file"""
            ....

    def _extract_from_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """Extract text from PDF"""
        ....

    def _extract_from_docx(self, file_content: bytes) -> Dict[str, Any]:
        """Extract text from DOCX"""
            ....

    def _extract_from_image(self, file_content: bytes, s3_key: str) -> Dict[str, Any]:
        """Extract text from image using AWS Textract and Tesseract fallback"""
            ....

    def _extract_with_textract(self, s3_key: str) -> Dict[str, Any]:
        """Extract text using AWS Textract"""
            ....

    def _extract_with_tesseract(self, file_content: bytes) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
            ....

# Singleton instance
file_processor = FileProcessor()
```

## Phase 4: SQLAlchemy Models

### 4.1 Database Models

```python
# models/database.py
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, Boolean, Date, DateTime, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class ExperienceLevel(enum.Enum):
    ENTRY = "Entry"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"

class CandidateStatus(enum.Enum):
    NEW = "New"
    REVIEWED = "Reviewed"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ProcessingStatus(enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    SUCCESS = "Success"
    FAILED = "Failed"

class BatchStatus(enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"

class SkillCategory(enum.Enum):
    TECHNICAL = "Technical"
    SOFT = "Soft"
    LANGUAGE = "Language"
    CERTIFICATION = "Certification"
    TOOL = "Tool"
    FRAMEWORK = "Framework"

class ProficiencyLevel(enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class EducationLevel(enum.Enum):
    HIGH_SCHOOL = "High School"
    ASSOCIATE = "Associate"
    BACHELOR = "Bachelor"
    MASTER = "Master"
    PHD = "PhD"
    OTHER = "Other"

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))
    address = Column(Text)
    overall_score = Column(DECIMAL(5,2), default=0.00)
    classification = Column(String(100), index=True)
    experience_level = Column(Enum(ExperienceLevel), default=ExperienceLevel.ENTRY)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.NEW, index=True)
    original_filename = Column(String(255))
    s3_file_key = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    # Relationships
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    extracted_text = relationship("ExtractedText", back_populates="candidate", cascade="all, delete-orphan")

class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    degree = Column(String(255))
    institution = Column(String(255))
    graduation_year = Column(Integer, index=True)
    gpa = Column(DECIMAL(3,2))
    major = Column(String(255))
    education_level = Column(Enum(EducationLevel))
    is_primary = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="education")

class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_title = Column(String(255))
    company = Column(String(255), index=True)
    start_date = Column(Date, index=True)
    end_date = Column(Date)
    is_current = Column(Boolean, default=False)
    responsibilities = Column(JSON)
    achievements = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="experience")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    skill_category = Column(Enum(SkillCategory), nullable=False, index=True)
    proficiency_level = Column(Enum(ProficiencyLevel), default=ProficiencyLevel.INTERMEDIATE)
    years_experience = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="skills")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    project_name = Column(String(255))
    description = Column(Text)
    technologies = Column(JSON)
    project_url = Column(String(500))
    github_url = Column(String(500))
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    certification_name = Column(String(255), nullable=False, index=True)
    issuing_organization = Column(String(255))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    credential_id = Column(String(255))
    verification_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="certifications")

class ProcessingBatch(Base):
    __tablename__ = "processing_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), unique=True, nullable=False, index=True)
    batch_name = Column(String(255))
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING, index=True)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    processing_logs = relationship("ProcessingLog", back_populates="batch")

class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), ForeignKey("processing_batches.batch_id"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer)
    s3_key = Column(String(500))
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    extraction_confidence = Column(DECIMAL(3,2))
    error_message = Column(Text)
    processing_time_seconds = Column(DECIMAL(10,3))
    llm_response_time = Column(DECIMAL(10,3))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    # Relationships
    batch = relationship("ProcessingBatch", back_populates="processing_logs")
    candidate = relationship("Candidate")

class ExtractedText(Base):
    __tablename__ = "extracted_text"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    raw_text = Column(Text)
    processed_text = Column(Text)
    extraction_method = Column(Enum('PDF', 'DOCX', 'OCR', name='extraction_method'), nullable=False)
    page_count = Column(Integer, default=1)
    word_count = Column(Integer)
    confidence_score = Column(DECIMAL(3,2))
    metadata = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="extracted_text")

class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=False, index=True)
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    min_experience_years = Column(Integer, default=0)
    education_requirements = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
```

## Phase 5: Core Processing Pipeline

### 5.1 Main Processing Service

```python
# services/resume_processor.py
import uuid
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging
from datetime import datetime
from services.s3_service import s3_service
from services.file_processor import file_processor
from services.ollama_service import ollama_service
from services.classification_service import classification_service
from models.database import *
from database.config import SessionLocal

class ResumeProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def process_batch(self, files: List[UploadFile], batch_name: str = None) -> str:
        """Process a batch of resume files"""
            ....

    async def _process_files_async(self, batch_id: str, files: List[UploadFile]):
        """Process files asynchronously"""
            ....

    async def _process_single_file(self, db: Session, batch_id: str, file: UploadFile) -> bool:
        """Process a single resume file"""
            ....

    def _create_candidate_from_data(self, db: Session, data: Dict[str, Any], filename: str, s3_key: str) -> Candidate:
        """Create candidate record from extracted data"""
            ....

    def _parse_date(self, date_str: str):
        """Parse date string to date object"""
            ....

    def _map_education_level(self, level_str: str) -> EducationLevel:
        """Map education level string to enum"""
            ....

    def _map_skill_category(self, category_str: str) -> SkillCategory:
        """Map skill category string to enum"""
            ....

    def _map_proficiency_level(self, level_str: str) -> ProficiencyLevel:
        """Map proficiency level string to enum"""
            ....

# Singleton instance
resume_processor = ResumeProcessor()
```

### 5.2 Classification Service

```python
# services/classification_service.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from models.database import Candidate, Experience, Education, Skill, ExperienceLevel
from datetime import datetime, date
import logging

class ClassificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def classify_candidate(self, candidate: Candidate, db: Session) -> Dict[str, Any]:
        """Classify candidate based on experience, education, and skills"""
            ....

    def _calculate_experience_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate experience score based on work history"""
            ....

    def _calculate_education_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate education score"""
            ....

    def _calculate_skills_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate skills score"""
            ....

    def _determine_experience_level(self, candidate: Candidate, db: Session) -> ExperienceLevel:
        """Determine experience level"""
            ....

    def _generate_classification(self, candidate: Candidate, db: Session, overall_score: float) -> str:
        """Tạo chuỗi phân loại cho ứng viên"""
            ....
```