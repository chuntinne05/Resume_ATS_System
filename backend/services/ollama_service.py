import requests
import json
import os
import logging
# from dotenv import load_dotenv;
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
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "llama3.2:3b"):
        self.base_url = f"http://{host}:{port}"
        self.model = model
        self.logger = logging.getLogger(__name__)
        
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def extract_resume_info(self, resume_text: str) -> ExtractionResult:
        start_time = time.time()
        
        prompt = self._build_extraction_prompt(resume_text)
        
        try:
            response = self._call_ollama(prompt)
            
            if response:
                extracted_data = self._parse_response(response)
                confidence = self._calculate_confidence(extracted_data)
                processing_time = time.time() - start_time
                
                return ExtractionResult(
                    success=True,
                    data=extracted_data,
                    confidence=confidence,
                    processing_time=processing_time
                )
            else:
                return ExtractionResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    error_message="No response from Ollama"
                )
                
        except Exception as e:
            self.logger.error(f"Error extracting resume info: {str(e)}")
            return ExtractionResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _build_extraction_prompt(self, resume_text: str) -> str:
        return f"""
You are a CV/Resume analysis expert. Extract information from the resume below and return the result in JSON format with the following structure:

{{
    "personal_info": {{
        "full_name": "Full Name",
        "email": "email@example.com",
        "phone": "Phone Number",
        "address": "Full Address",
        "linkedin": "LinkedIn profile URL",
        "github": "GitHub profile URL"
    }},
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "University Name",
            "graduation_year": 2023,
            "gpa": 3.5,
            "major": "Major",
            "education_level": "Bachelor"
        }}
    ],
    "experience": [
        {{
            "job_title": "Job Title",
            "company": "Company Name",
            "start_date": "2022-01",
            "end_date": "2023-12",
            "is_current": false,
            "responsibilities": ["Responsibility 1", "Responsibility 2"],
            "achievements": ["Achievement 1", "Achievement 2"]
        }}
    ],
    "skills": [
        {{
            "skill_name": "Python",
            "category": "Technical",
            "proficiency_level": "Advanced",
            "years_experience": 3
        }}
    ],
    "projects": [
        {{
            "project_name": "Project Name",
            "description": "Project Description",
            "technologies": ["Python", "React", "MySQL"],
            "project_url": "https://project.com",
            "github_url": "https://github.com/user/project"
        }}
    ],
    "certifications": [
        {{
            "certification_name": "AWS Certified",
            "issuing_organization": "Amazon",
            "issue_date": "2023-06",
            "expiry_date": "2026-06"
        }}
    ],
    "languages": [
        {{
            "language": "English",
            "proficiency": "Fluent"
        }}
    ]
}}

IMPORTANT:
	1.	Only return JSON, no extra text
	2.	If any information is missing, use null or an empty array
	3.	Use YYYY-MM or YYYY format for all dates
	4.	Convert GPA to 4.0 scale if necessary

Resume text:
{resume_text}
"""

    def _call_ollama(self, prompt: str) -> Optional[str]:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("Ollama response:", result.get('response', ''))
                return result.get('response', '')
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("Ollama API timeout")
            return None
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {str(e)}")
            return None
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                self.logger.warning("No JSON found in response")
                return {}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            return self._fallback_extraction(response)
        except Exception as e:
            self.logger.error(f"Response parsing error: {str(e)}")
            return {}
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        import re
        
        result = {
            "personal_info": {},
            "education": [],
            "experience": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": []
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            result["personal_info"]["email"] = emails[0]
        
        # Extract phone
        phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            result["personal_info"]["phone"] = phones[0]
        
        return result
    
    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        total_fields = 0
        filled_fields = 0
        
        personal_info = extracted_data.get("personal_info", {})
        important_personal_fields = ["full_name", "email", "phone"]
        for field in important_personal_fields:
            total_fields += 1
            if personal_info.get(field):
                filled_fields += 1
        
        education = extracted_data.get("education", [])
        if education:
            total_fields += 1
            filled_fields += 1
        
        experience = extracted_data.get("experience", [])
        if experience:
            total_fields += 1
            filled_fields += 1
        
        skills = extracted_data.get("skills", [])
        if skills:
            total_fields += 1
            filled_fields += 1
        
        return round(filled_fields / total_fields, 2) if total_fields > 0 else 0.0

OLLAMA_CONFIG = {
    'host': os.getenv('OLLAMA_HOST', 'localhost'),
    'port': int(os.getenv('OLLAMA_PORT', 11434)),
    'model': os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
}

ollama_service = OllamaService(**OLLAMA_CONFIG)