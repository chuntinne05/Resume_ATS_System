# Resume ATS System - Complete Project Plan

## System Architecture Overview

### Core Components
1. **Multi-format Document Processor** - PDF, DOCX, images
2. **LLM-powered Information Extractor** - GPT-4/Claude với custom prompts
3. **Validation & Quality Assurance Layer** - Đảm bảo độ chính xác
4. **Classification Engine** - Phân loại theo criteria
5. **Web Dashboard** - Enterprise-grade UI
6. **API Gateway** - RESTful services

## Tech Stack Chi Tiết

### Backend Architecture
- **Framework**: FastAPI (Python) + Celery (background tasks)
- **Database**: PostgreSQL (structured data) + MongoDB (documents)
- **Cache**: Redis (session, temporary data)
- **Message Queue**: RabbitMQ/AWS SQS
- **Storage**: AWS S3 + CloudFront CDN

### AI/ML Components
- **Primary LLM**: OpenAI GPT-4 hoặc Anthropic Claude
- **Backup NER**: spaCy custom model
- **OCR**: AWS Textract + Tesseract fallback
- **Validation**: Rule-based + ML confidence scoring

### Infrastructure
- **Container**: Docker + Kubernetes
- **Cloud**: AWS (Lambda, ECS, RDS, S3)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana + Sentry

## Detailed Pipeline Architecture

### 1. Document Ingestion Pipeline
```
Upload → Validation → Storage → Queue → Processing
```

**Input Validation:**
- File format check (PDF, DOCX, JPG, PNG)
- Size limits (max 10MB per file)
- Batch size limits (max 100 files)
- Virus scanning
- Content type verification

### 2. Multi-Stage Processing Pipeline

**Stage 1: Document Conversion**
- PDF → Text extraction (PyMuPDF, pdfplumber)
- DOCX → Text extraction (python-docx)
- Images → OCR (Textract + Tesseract)
- Quality check extracted text

**Stage 2: LLM Information Extraction**
```python
# Structured extraction prompt
extraction_prompt = """
Extract the following information from this resume:

PERSONAL INFO:
- Full Name: [exact name]
- Email: [email address]
- Phone: [phone number]
- Address: [full address]

EDUCATION:
- Degree: [degree name]
- Institution: [university/college name]
- Graduation Year: [year]
- GPA: [if mentioned, format: X.X/4.0]
- Major: [field of study]

EXPERIENCE:
- Job Title: [exact title]
- Company: [company name]
- Duration: [start date - end date]
- Responsibilities: [key responsibilities]
- Achievements: [quantifiable achievements]

SKILLS:
- Technical Skills: [programming languages, tools, etc.]
- Soft Skills: [communication, leadership, etc.]
- Certifications: [professional certifications]

ADDITIONAL:
- Languages: [language proficiency]
- Projects: [notable projects]
- Awards: [achievements, honors]

Return as structured JSON with confidence scores for each field.
"""
```

**Stage 3: Validation & Quality Assurance**
```python
class ValidationRules:
    def validate_email(self, email):
        # Regex + DNS validation
    
    def validate_phone(self, phone):
        # Phone number format validation
    
    def validate_gpa(self, gpa):
        # GPA range validation (0.0-4.0)
    
    def validate_dates(self, dates):
        # Date format + logical validation
    
    def validate_completeness(self, extracted_data):
        # Check required fields completion
```

### 3. Classification System

**Multi-dimensional Classification:**
- **Experience Level**: Entry/Mid/Senior (based on years + responsibilities)
- **Technical Proficiency**: Beginner/Intermediate/Advanced
- **Education Level**: High School/Bachelor/Master/PhD
- **Industry Match**: % match với job requirements
- **Skill Categories**: Frontend/Backend/DevOps/Data Science/etc.

**Classification Algorithm:**
```python
def classify_candidate(extracted_data):
    scores = {
        'experience_score': calculate_experience_score(extracted_data),
        'education_score': calculate_education_score(extracted_data),
        'skill_match_score': calculate_skill_match(extracted_data, job_requirements),
        'gpa_score': normalize_gpa_score(extracted_data.gpa),
        'overall_score': 0
    }
    
    # Weighted scoring
    weights = {
        'experience': 0.4,
        'education': 0.2,
        'skills': 0.3,
        'gpa': 0.1
    }
    
    scores['overall_score'] = sum(scores[key] * weights[key.split('_')[0]] 
                                 for key in scores if key != 'overall_score')
    
    return classify_tier(scores['overall_score'])
```

## Database Schema Design

### PostgreSQL Tables
```sql
-- Candidates table
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    overall_score DECIMAL(3,2),
    classification VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Education table
CREATE TABLE education (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    degree VARCHAR(255),
    institution VARCHAR(255),
    graduation_year INTEGER,
    gpa DECIMAL(3,2),
    major VARCHAR(255)
);

-- Experience table
CREATE TABLE experience (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    job_title VARCHAR(255),
    company VARCHAR(255),
    start_date DATE,
    end_date DATE,
    responsibilities TEXT[],
    achievements TEXT[]
);

-- Skills table
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    skill_name VARCHAR(100),
    skill_category VARCHAR(50),
    proficiency_level VARCHAR(20)
);

-- Processing logs
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    batch_id UUID,
    file_name VARCHAR(255),
    status VARCHAR(50),
    confidence_score DECIMAL(3,2),
    error_message TEXT,
    processing_time INTERVAL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### MongoDB Documents
```javascript
// Raw documents and metadata
{
  "_id": ObjectId("..."),
  "batch_id": "uuid",
  "file_name": "resume.pdf",
  "original_text": "extracted raw text...",
  "processed_text": "cleaned text...",
  "extraction_metadata": {
    "confidence_scores": {
      "name": 0.95,
      "email": 0.98,
      "education": 0.87,
      "experience": 0.92
    },
    "processing_time": 2.3,
    "llm_model": "gpt-4",
    "validation_passed": true
  },
  "file_metadata": {
    "size": 245760,
    "format": "pdf",
    "pages": 2,
    "upload_timestamp": ISODate("...")
  }
}
```

## API Endpoints Design

### Core Endpoints
```python
# Batch upload
POST /api/v1/batch/upload
- Multipart file upload
- Returns batch_id for tracking

# Processing status
GET /api/v1/batch/{batch_id}/status
- Processing progress
- Individual file status

# Results retrieval
GET /api/v1/batch/{batch_id}/results
- Extracted and classified data
- Filtering and sorting options

# Individual candidate
GET /api/v1/candidates/{candidate_id}
- Detailed candidate profile
- Confidence scores

# Search and filter
POST /api/v1/candidates/search
- Multi-criteria search
- Classification filters
- Skill-based matching

# Bulk operations
POST /api/v1/candidates/bulk-classify
- Reclassify based on new criteria
- Batch updates
```

## Quality Assurance Strategy

### 1. Multi-Layer Validation
- **Syntactic**: Format validation (email, phone, dates)
- **Semantic**: Logical consistency (graduation before work)
- **Confidence**: LLM confidence scores + human review thresholds
- **Completeness**: Required field coverage percentage

### 2. Accuracy Measures
```python
class AccuracyMetrics:
    def calculate_extraction_accuracy(self, ground_truth, extracted):
        """Field-level accuracy measurement"""
        
    def calculate_classification_accuracy(self, manual_labels, predicted):
        """Classification accuracy with confusion matrix"""
        
    def calculate_completeness_score(self, extracted_data):
        """Percentage of required fields extracted"""
        
    def generate_confidence_report(self, batch_results):
        """Batch-level confidence analysis"""
```

### 3. Human-in-the-Loop (HITL)
- **Low confidence alerts**: < 85% confidence → human review
- **Batch review dashboard**: Manual verification interface
- **Feedback loop**: Corrections → model improvement
- **Quality sampling**: Random 5% manual validation

## Web Dashboard Features

### Admin Dashboard
- **Batch Management**: Upload, monitor, manage batches
- **Quality Control**: Review low-confidence extractions
- **Analytics**: Processing statistics, accuracy metrics
- **System Health**: Performance monitoring

### HR Dashboard
- **Candidate Database**: Search, filter, sort candidates
- **Comparison Tools**: Side-by-side candidate comparison
- **Classification Views**: Group by experience, skills, education
- **Export Features**: Excel, PDF reports

### Candidate Profile View
```javascript
{
  "candidate_summary": {
    "name": "John Doe",
    "overall_score": 8.5,
    "classification": "Senior Software Engineer",
    "top_skills": ["Python", "AWS", "React"],
    "experience_years": 7,
    "education_level": "Master's"
  },
  "detailed_profile": {
    "contact_info": {...},
    "education": [...],
    "experience": [...],
    "skills": [...],
    "projects": [...],
    "confidence_scores": {...}
  }
}
```

## Implementation Phases

### Phase 1: Core Infrastructure (3-4 weeks)
- Setup cloud infrastructure
- Database design and implementation
- Basic API framework
- File upload and storage

### Phase 2: Document Processing (3-4 weeks)
- Multi-format text extraction
- OCR integration
- Text preprocessing pipeline
- Quality validation

### Phase 3: LLM Integration (2-3 weeks)
- LLM API integration
- Prompt engineering and optimization
- Structured extraction implementation
- Confidence scoring

### Phase 4: Classification System (2-3 weeks)
- Multi-dimensional classification
- Scoring algorithms
- Validation rules
- Performance optimization

### Phase 5: Web Dashboard (3-4 weeks)
- Admin interface
- HR dashboard
- Candidate profiles
- Search and filtering

### Phase 6: Quality Assurance (2-3 weeks)
- HITL implementation
- Accuracy measurement
- Feedback systems
- Performance monitoring

### Phase 7: Testing & Deployment (2-3 weeks)
- Load testing
- Security testing
- Performance optimization
- Production deployment

## Cost Optimization Strategies

### LLM Usage Optimization
- **Batch processing**: Group multiple resumes per API call
- **Caching**: Cache similar resumes
- **Tiered processing**: Use cheaper models for initial screening
- **Smart retry**: Avoid redundant API calls

### Infrastructure Optimization
- **Auto-scaling**: Scale based on demand
- **Reserved instances**: Cost savings for predictable workloads
- **CDN**: Reduce bandwidth costs
- **Monitoring**: Cost tracking and alerts

## Security & Compliance

### Data Protection
- **Encryption**: At rest and in transit
- **Access control**: Role-based permissions
- **Audit logging**: All data access tracked
- **Data retention**: Configurable retention policies

### Compliance Features
- **GDPR compliance**: Data deletion, consent management
- **SOC 2**: Security controls
- **HIPAA ready**: Healthcare industry compliance
- **Data anonymization**: PII protection options

## Deployment Architecture

### Production Infrastructure
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-ats-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resume-ats-api
  template:
    metadata:
      labels:
        app: resume-ats-api
    spec:
      containers:
      - name: api
        image: resume-ats:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### Monitoring & Alerting
- **Health checks**: API endpoint monitoring
- **Performance metrics**: Response times, throughput
- **Error tracking**: Exception monitoring
- **Business metrics**: Processing accuracy, completion rates

## Success Metrics

### Technical Metrics
- **Extraction Accuracy**: > 95% for key fields
- **Processing Speed**: < 30 seconds per resume
- **System Uptime**: 99.9%
- **API Response Time**: < 2 seconds

### Business Metrics
- **User Satisfaction**: Net Promoter Score > 8
- **Processing Volume**: 1000+ resumes/day capacity
- **Cost Efficiency**: < $0.10 per resume processed
- **ROI**: 50% reduction in manual resume screening time

## Future Enhancements

### Advanced Features
- **Multi-language support**: Resume processing in various languages
- **Video resume processing**: AI-powered video analysis
- **Skills gap analysis**: Identify missing skills for roles
- **Predictive analytics**: Success probability modeling

### Integration Capabilities
- **ATS Integration**: Connect with existing HR systems
- **Job board APIs**: Direct integration with job platforms
- **Assessment tools**: Technical skill evaluation
- **Background check**: Automated verification services