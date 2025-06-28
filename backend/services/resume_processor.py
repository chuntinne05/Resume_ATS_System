import uuid
import asyncio
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging
from datetime import datetime
from backend.services.s3_service import s3_service
from backend.services.file_processor import file_processor
from backend.services.ollama_service import ollama_service
from backend.services.classification_service import ClassificationService
from backend.models.database import *
from backend.database.config import SessionLocal
from dotenv import load_dotenv
load_dotenv()

class ResumeProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_batch(self, file_data: List[Tuple[str, bytes]], batch_name: str = None) -> str:
        """Process a batch of resume files"""
        batch_id = str(uuid.uuid4())
        
        # Create batch record
        db = SessionLocal()
        try:
            batch = ProcessingBatch(
                batch_id=batch_id,
                batch_name=batch_name or f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                total_files=len(file_data),
                status=BatchStatus.PENDING
            )
            db.add(batch)
            db.commit()
            
            # Process files asynchronously
            # asyncio.create_task(self._process_files_async(batch_id, file_data))
            await self._process_files_async(batch_id, file_data) 
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Error creating batch: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def _process_files_async(self, batch_id: str, file_data: List[Tuple[str, bytes]]):
        """Process files asynchronously"""
        db = SessionLocal()
        try:
            batch = db.query(ProcessingBatch).filter(ProcessingBatch.batch_id == batch_id).first()
            batch.status = BatchStatus.PROCESSING
            batch.started_at = datetime.now()
            db.commit()
            
            successful_count = 0
            failed_count = 0
            
            for filename, content in file_data:
                try:
                    success = await self._process_single_file(db, batch_id, filename, content)
                    if success:
                        successful_count += 1
                    else:
                        failed_count += 1
                        
                    # Update progress
                    batch.processed_files += 1
                    batch.successful_files = successful_count
                    batch.failed_files = failed_count
                    db.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error processing file {filename}: {str(e)}")
                    db.rollback()
                    failed_count += 1
                    batch = db.query(ProcessingBatch).filter(ProcessingBatch.batch_id == batch_id).first()
                    batch.processed_files += 1
                    batch.failed_files = failed_count
                    db.commit()
            
            # Complete batch
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = datetime.now()
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            db.rollback()  
            batch = db.query(ProcessingBatch).filter(ProcessingBatch.batch_id == batch_id).first()
            batch.status = BatchStatus.FAILED
            db.commit()
        finally:
            db.close()
    
    async def _process_single_file(self, db: Session, batch_id: str, filename: str, file_content: bytes) -> bool:
        """Process a single resume file"""
        start_time = datetime.now()
        
        try:
            log = ProcessingLog(
                batch_id=batch_id,
                filename=filename,
                file_size=len(file_content),
                processing_status=ProcessingStatus.PROCESSING
            )
            db.add(log)
            db.commit()
            
            self.logger.info(f"Uploading {filename} to S3")
            s3_result = s3_service.upload_file(file_content, filename)
            if not s3_result['success']:
                self.logger.error(f"S3 upload failed for {filename}: {s3_result.get('error')}")
                log.processing_status = ProcessingStatus.FAILED
                log.error_message = f"S3 upload failed: {s3_result.get('error')}"
                db.commit()
                return False
            log.s3_key = s3_result['s3_key']
            self.logger.info(f"Uploaded {filename} to S3 with key: {s3_result['s3_key']}")
            
            self.logger.info(f"Extracting text from {filename}")
            extraction_result = file_processor.extract_text_from_file(
                file_content, filename, s3_result['s3_key']
            )
            if not extraction_result['success']:
                self.logger.error(f"Text extraction failed for {filename}: {extraction_result.get('error')}")
                log.processing_status = ProcessingStatus.FAILED
                log.error_message = f"Text extraction failed: {extraction_result.get('error')}"
                db.commit()
                return False
            self.logger.info(f"Text extracted successfully from {filename}")
            
            self.logger.info(f"Calling Ollama for {filename}")
            llm_start_time = datetime.now()
            llm_result = ollama_service.extract_resume_info(extraction_result['text'])
            llm_processing_time = (datetime.now() - llm_start_time).total_seconds()
            
            if not llm_result.success:
                self.logger.error(f"LLM processing failed for {filename}: {llm_result.error_message}")
                db.rollback()
                log.processing_status = ProcessingStatus.FAILED
                log.error_message = f"LLM processing failed: {llm_result.error_message}"
                log.llm_response_time = llm_processing_time
                db.commit()
                return False
            self.logger.info(f"Ollama processing completed for {filename}")
            
            # Save candidate data
            self.logger.info(f"Creating candidate from extracted data for {filename}")
            candidate = self._create_candidate_from_data(
                db, llm_result.data, filename, s3_result['s3_key']
            )
            self.logger.info(f"Candidate created with ID: {candidate.id}")
            extracted_text = ExtractedText(
                candidate_id=candidate.id,
                raw_text=extraction_result['text'],
                processed_text=extraction_result['text'],
                extraction_method=extraction_result['extraction_method'],
                page_count=extraction_result.get('page_count', 1),
                word_count=extraction_result.get('word_count', 0),
                confidence_score=llm_result.confidence,
                meta_data={
                    'file_size': len(file_content),
                    'processing_time': llm_result.processing_time,
                    'extraction_method': extraction_result['extraction_method']
                }
            )
            db.add(extracted_text)
            
            classification_service = ClassificationService()
            classification_result = classification_service.classify_candidate(candidate, db)
            candidate.classification = classification_result['classification']
            candidate.overall_score = classification_result['overall_score']
            candidate.experience_level = classification_result['experience_level']
            log.candidate_id = candidate.id
            log.processing_status = ProcessingStatus.SUCCESS
            log.extraction_confidence = llm_result.confidence
            log.llm_response_time = llm_processing_time
            log.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            
            db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing file {filename}: {str(e)}")
            db.rollback()
            log.processing_status = ProcessingStatus.FAILED
            log.error_message = str(e)
            log.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            db.commit()
            return False
    
    def _create_candidate_from_data(self, db: Session, data: Dict[str, Any], filename: str, s3_key: str) -> Candidate:
        """Create candidate record from extracted data"""
        personal_info = data.get('personal_info', {})

        email = personal_info.get('email')
        candidate = None
        if email:
            candidate = db.query(Candidate).filter(Candidate.email == email).first()

        if candidate:
            print("Updating existing candidate")
            candidate.full_name = personal_info.get('full_name', candidate.full_name)
            candidate.phone = personal_info.get('phone', candidate.phone)
            candidate.address = personal_info.get('address', candidate.address)
            candidate.original_filename = filename
            candidate.s3_file_key = s3_key
            db.query(Education).filter(Education.candidate_id == candidate.id).delete()
            db.query(Experience).filter(Experience.candidate_id == candidate.id).delete()
            db.query(Skill).filter(Skill.candidate_id == candidate.id).delete()
            db.query(Project).filter(Project.candidate_id == candidate.id).delete()
            db.query(Certification).filter(Certification.candidate_id == candidate.id).delete()
        else:
            print("Creating new candidate")
            candidate = Candidate(
                full_name=personal_info.get('full_name', ''),
                email=email,
                phone=personal_info.get('phone'),
                address=personal_info.get('address'),
                original_filename=filename,
                s3_file_key=s3_key
            )
            db.add(candidate)
        db.flush()
        print(f"Candidate ID after flush: {candidate.id}")  
        
        for edu_data in data.get('education', []):
            graduation_year = self._extract_year(edu_data.get('graduation_year'))
            education = Education(
                candidate_id=candidate.id,
                degree=edu_data.get('degree'),
                institution=edu_data.get('institution'),
                graduation_year=graduation_year,
                gpa=edu_data.get('gpa'),
                major=edu_data.get('major'),
                education_level=self._map_education_level(edu_data.get('education_level'))
            )
            db.add(education)
        print(f"Added education: {edu_data.get('degree')} for candidate ID: {candidate.id}")
        
        # Add experience records
        for exp_data in data.get('experience', []):
            experience = Experience(
                candidate_id=candidate.id,
                job_title=exp_data.get('job_title'),
                company=exp_data.get('company'),
                start_date=self._parse_date(exp_data.get('start_date')),
                end_date=self._parse_date(exp_data.get('end_date')),
                is_current=exp_data.get('is_current', False),
                responsibilities=exp_data.get('responsibilities', []),
                achievements=exp_data.get('achievements', [])
            )
            db.add(experience)
        print(f"Added experience: {exp_data.get('job_title')} at {exp_data.get('company')} for candidate ID: {candidate.id}")
        
        # Add skills
        for skill_data in data.get('skills', []):
            skill = Skill(
                candidate_id=candidate.id,
                skill_name=skill_data.get('skill_name'),
                skill_category=self._map_skill_category(skill_data.get('category')),
                proficiency_level=self._map_proficiency_level(skill_data.get('proficiency_level')),
                years_experience=skill_data.get('years_experience', 0)
            )
            db.add(skill)
        print(f"Added skill: {skill_data.get('skill_name')} for candidate ID: {candidate.id}")
        
        # Add projects
        for project_data in data.get('projects', []):
            project = Project(
                candidate_id=candidate.id,
                project_name=project_data.get('project_name'),
                description=project_data.get('description'),
                technologies=project_data.get('technologies', []),
                project_url=project_data.get('project_url'),
                github_url=project_data.get('github_url'),
                start_date=self._parse_date(project_data.get('start_date')),
                end_date=self._parse_date(project_data.get('end_date'))
            )
            db.add(project)
        print(f"Added project: {project_data.get('project_name')} for candidate ID: {candidate.id}")
        
        # Add certifications
        for cert_data in data.get('certifications', []):
            certification = Certification(
                candidate_id=candidate.id,
                certification_name=cert_data.get('certification_name'),
                issuing_organization=cert_data.get('issuing_organization'),
                issue_date=self._parse_date(cert_data.get('issue_date')),
                expiry_date=self._parse_date(cert_data.get('expiry_date'))
            )
            db.add(certification)
        print(f"Added certification: {cert_data.get('certification_name')} for candidate ID: {candidate.id}")
        db.commit() 
        return candidate
    
    def _parse_date(self, date_str: str):
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = ['%Y-%m-%d', '%Y-%m', '%Y', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None
        
    def _extract_year(self, year_input: Any) -> int:
        """Extract year from various input formats"""
        if not year_input:
            return None
        
        try:
            # If input is already an integer
            if isinstance(year_input, int):
                return year_input
            
            # Convert to string for processing
            year_str = str(year_input)
            
            # Handle YYYY-MM or YYYY formats
            if '-' in year_str:
                return int(year_str.split('-')[0])
            return int(year_str)
        except (ValueError, TypeError):
            return None
    
    def _map_education_level(self, level_str: str) -> EducationLevel:
        """Map education level string to enum"""
        if not level_str:
            return EducationLevel.OTHER
        
        level_mapping = {
            'high school': EducationLevel.HIGH_SCHOOL,
            'associate': EducationLevel.ASSOCIATE,
            'bachelor': EducationLevel.BACHELOR,
            'master': EducationLevel.MASTER,
            'phd': EducationLevel.PHD,
            'doctorate': EducationLevel.PHD
        }
        
        return level_mapping.get(level_str.lower(), EducationLevel.OTHER)
    
    def _map_skill_category(self, category_str: str) -> SkillCategory:
        """Map skill category string to enum"""
        if not category_str:
            return SkillCategory.TECHNICAL
        
        category_mapping = {
            'technical': SkillCategory.TECHNICAL,
            'soft': SkillCategory.SOFT,
            'language': SkillCategory.LANGUAGE,
            'certification': SkillCategory.CERTIFICATION,
            'tool': SkillCategory.TOOL,
            'framework': SkillCategory.FRAMEWORK
        }
        
        return category_mapping.get(category_str.lower(), SkillCategory.TECHNICAL)
    
    def _map_proficiency_level(self, level_str: str) -> ProficiencyLevel:
        """Map proficiency level string to enum"""
        if not level_str:
            return ProficiencyLevel.INTERMEDIATE
        
        level_mapping = {
            'beginner': ProficiencyLevel.BEGINNER,
            'intermediate': ProficiencyLevel.INTERMEDIATE,
            'advanced': ProficiencyLevel.ADVANCED,
            'expert': ProficiencyLevel.EXPERT
        }
        
        return level_mapping.get(level_str.lower(), ProficiencyLevel.INTERMEDIATE)

# Singleton instance
resume_processor = ResumeProcessor()