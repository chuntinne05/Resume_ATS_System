# models/database.py
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, Boolean, Date, DateTime, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class ExperienceLevel(enum.Enum):
    ENTRY = "ENTRY"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"

class CandidateStatus(enum.Enum):
    NEW = "NEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ProcessingStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class BatchStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SkillCategory(enum.Enum):
    TECHNICAL = "Technical"
    SOFT = "Soft"
    LANGUAGE = "Language"
    CERTIFICATION = "Certification"
    TOOL = "Tool"
    FRAMEWORK = "Framework"

class ProficiencyLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

class EducationLevel(enum.Enum):
    HIGH_SCHOOL = "HIGH_SCHOOL"
    ASSOCIATE = "ASSOCIATE"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    PHD = "PHD"
    OTHER = "OTHER"

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
    meta_data = Column(JSON)
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