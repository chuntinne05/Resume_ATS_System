# Resume ATS System

An AI-powered Applicant Tracking System to streamline resume processing and candidate evaluation.

## Features

- Upload and process resumes (PDF, DOCX, JPG, PNG)
- AI-driven data extraction (personal info, skills, experience)
- Candidate management with filtering and scoring
- Job matching based on skills and experience (to be continue......)
- Batch processing with progress tracking
- Dashboard with statistics
- AWS S3 integration for file storage

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, MySQL
- **AI**: Ollama (Llama3.2:3b)
- **File Processing**: PyPDF2, python-docx, pdfplumber, pytesseract
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Other**: Celery, Redis, boto3

## Prerequisites

- Python 3.9+
- MySQL Server
- Redis Server
- AWS S3 bucket
- Tesseract OCR
- Ollama service

## Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/resume-ats-system.git
   cd resume-ats-system
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR: 
   ``` bash
   - On Ubuntu:
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   - On macOS:
     ```bash
     brew install tesseract
     ```
   - On Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki).
   ```

## Configuration

1. Create `.env` file:
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/resume_ats
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_S3_BUCKET_NAME=your_bucket
   AWS_REGION=your_region
   OLLAMA_HOST=http://localhost:11434
   REDIS_URL=redis://localhost:6379/0
   ```

2. Set up MySQL database and run migrations:
   ```bash
   alembic upgrade head
   ```

3. Start Redis: `redis-server`

## Running the Project

1. Start FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Start Celery worker:
   ```bash
   celery -A backend.services.resume_processor worker --loglevel=info
   ```

3. Access the dashboard at `http://localhost:8000`.

## Project Structure

```plaintext
resume-ats-system/
├── backend/
│   ├── models/
│   │   └── database.py          # Database models and schema
│   ├── services/
│   │   ├── resume_processor.py  # Resume processing 
│   │   ├── s3_service.py        # AWS S3 
│   │   ├── file_processor.py    # File extraction 
│   │   └── ollama_service.py    # Ollama
│   └── database/
│       └── config.py            # Database configuration
├── api/
│   ├── routes/
│   │   ├── candidates.py        
│   │   ├── batches.py           
│   │   ├── dashboard.py         
│   │   └── jobs.py             
├── static/
│   │  
│   ├── js/
│   │   └── dashboard.js        
│   └── resume_ats_dashboard.html 
├── requirements.txt          
├── main.py                    
├── README.md                 
└── .env                   
```


## Usage

- **Upload Resumes**: Use the dashboard to upload resumes and monitor batch processing.
- **Manage Candidates**: Filter and view candidate details.
- **Job Matching**: Create job requirements and match candidates via API. (to be continue...)

## API Endpoints

- `GET /`: Dashboard
- `GET /api/candidates`: List candidates
- `GET /api/candidates/{id}`: Candidate details
- `DELETE /api/candidates/{id}`: Delete candidate
- `GET /api/dashboard/stats`: Dashboard stats
- `POST /api/upload`: Upload resumes
- `GET /api/batches/{batch_id}/status`: Batch status
- `POST /api/requirements`: Create job requirement
- `GET /api/requirements`: List job requirements
- `POST /api/match/{job_id}`: Match candidates to job

## License

MIT License
