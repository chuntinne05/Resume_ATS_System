# services/classification_service.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.models.database import Candidate, Experience, Education, Skill, ExperienceLevel, SkillCategory, ProficiencyLevel, EducationLevel
from datetime import datetime, date
import logging

class ClassificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def classify_candidate(self, candidate: Candidate, db: Session) -> Dict[str, Any]:
        """Classify candidate based on experience, education, and skills"""
        
        # Calculate experience score
        experience_score = self._calculate_experience_score(candidate, db)
        
        # Calculate education score
        education_score = self._calculate_education_score(candidate, db)
        
        # Calculate skills score
        skills_score = self._calculate_skills_score(candidate, db)
        
        # Calculate overall score
        weights = {
            'experience': 0.5,
            'education': 0.2,
            'skills': 0.3
        }
        
        overall_score = (
            experience_score * weights['experience'] +
            education_score * weights['education'] +
            skills_score * weights['skills']
        )
        
        # Determine experience level
        experience_level = self._determine_experience_level(candidate, db)
        
        # Generate classification
        classification = self._generate_classification(candidate, db, overall_score)
        
        return {
            'overall_score': round(overall_score, 2),
            'experience_level': experience_level,
            'classification': classification,
            'score_breakdown': {
                'experience_score': round(experience_score, 2),
                'education_score': round(education_score, 2),
                'skills_score': round(skills_score, 2)
            }
        }
    
    def _calculate_experience_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate experience score based on work history"""
        experiences = db.query(Experience).filter(Experience.candidate_id == candidate.id).all()
        
        if not experiences:
            return 0.0
        
        total_months = 0
        role_quality_score = 0
        
        for exp in experiences:
            # Calculate duration
            start_date = exp.start_date
            end_date = exp.end_date or date.today()
            
            if start_date:
                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(0, months)
            
            # Score based on role seniority
            job_title = (exp.job_title or '').lower()
            if any(word in job_title for word in ['senior', 'lead', 'principal', 'architect']):
                role_quality_score += 3
            elif any(word in job_title for word in ['mid', 'intermediate', 'ii', '2']):
                role_quality_score += 2
            else:
                role_quality_score += 1
        
        # Convert to years
        total_years = total_months / 12
        
        # Score calculation
        years_score = min(total_years / 10, 1.0) * 7  # Max 7 points for experience years
        quality_score = min(role_quality_score / len(experiences) / 3, 1.0) * 3  # Max 3 points for role quality
        
        return years_score + quality_score
    
    def _calculate_education_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate education score"""
        educations = db.query(Education).filter(Education.candidate_id == candidate.id).all()
        
        if not educations:
            return 0.0
        
        max_score = 0
        
        for edu in educations:
            score = 0
            
            # Score based on education level
            if edu.education_level == EducationLevel.PHD:
                score += 5
            elif edu.education_level == EducationLevel.MASTER:
                score += 4
            elif edu.education_level == EducationLevel.BACHELOR:
                score += 3
            elif edu.education_level == EducationLevel.ASSOCIATE:
                score += 2
            else:
                score += 1
            
            # GPA bonus
            if edu.gpa and edu.gpa >= 3.5:
                score += 1
            elif edu.gpa and edu.gpa >= 3.0:
                score += 0.5
            
            max_score = max(max_score, score)
        
        return min(max_score, 10.0)
    
    def _calculate_skills_score(self, candidate: Candidate, db: Session) -> float:
        """Calculate skills score"""
        skills = db.query(Skill).filter(Skill.candidate_id == candidate.id).all()
        
        if not skills:
            return 0.0
        
        technical_skills = [s for s in skills if s.skill_category == SkillCategory.TECHNICAL]
        
        # Score based on number and proficiency of technical skills
        skill_score = 0
        
        for skill in technical_skills:
            if skill.proficiency_level == ProficiencyLevel.EXPERT:
                skill_score += 1.0
            elif skill.proficiency_level == ProficiencyLevel.ADVANCED:
                skill_score += 0.8
            elif skill.proficiency_level == ProficiencyLevel.INTERMEDIATE:
                skill_score += 0.5
            else:
                skill_score += 0.2
        
        # Normalize to 0-10 scale
        normalized_score = min(skill_score / 2, 10.0)
        
        return normalized_score
    
    def _determine_experience_level(self, candidate: Candidate, db: Session) -> ExperienceLevel:
        """Xác định cấp độ kinh nghiệm của ứng viên"""
        experiences = db.query(Experience).filter(Experience.candidate_id == candidate.id).all()
        
        if not experiences:
            return ExperienceLevel.ENTRY
        
        total_months = 0
        has_senior_role = False
        has_lead_role = False
        
        for exp in experiences:
            start_date = exp.start_date
            end_date = exp.end_date or date.today()
            
            if start_date:
                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(0, months)
            
            job_title = (exp.job_title or '').lower()
            if any(word in job_title for word in ['senior', 'lead', 'principal', 'architect']):
                has_senior_role = True
            if any(word in job_title for word in ['manager', 'director', 'head', 'chief']):
                has_lead_role = True
        
        total_years = total_months / 12
        
        if has_lead_role and total_years >= 5:
            return ExperienceLevel.LEAD
        elif has_senior_role or total_years >= 5:
            return ExperienceLevel.SENIOR
        elif total_years >= 2:
            return ExperienceLevel.MID
        else:
            return ExperienceLevel.ENTRY
        
    def _generate_classification(self, candidate: Candidate, db: Session, overall_score: float) -> str:
        """Tạo chuỗi phân loại cho ứng viên"""
        # Lấy công việc gần nhất làm đại diện
        latest_experience = db.query(Experience).filter(Experience.candidate_id == candidate.id)\
                            .order_by(Experience.start_date.desc()).first()
        
        job_title = latest_experience.job_title if latest_experience else "Professional"
        
        # Kết hợp cấp độ kinh nghiệm và chức danh công việc
        return f"{candidate.experience_level.value} {job_title}"