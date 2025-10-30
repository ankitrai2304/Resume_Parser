"""
Resume Parser Backend API
FastAPI application for parsing resumes and storing data in Google Sheets
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Google Sheets imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Resume parsing imports
import PyPDF2
from docx import Document
import re
import io
print(f"DEBUG: SPREADSHEET_ID = {os.getenv('GOOGLE_SPREADSHEET_ID')}")
print(f"DEBUG: SERVICE_ACCOUNT_FILE = {os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')}")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Parser API",
    description="API for parsing resumes and extracting structured data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
logger.info(f"Allowed CORS origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Validate required environment variables
if not SPREADSHEET_ID:
    logger.warning("⚠️  GOOGLE_SPREADSHEET_ID not set in .env file")
else:
    logger.info(f"✓ Google Spreadsheet configured: {SPREADSHEET_ID[:10]}...")

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    logger.warning(f"⚠️  Service account file not found: {SERVICE_ACCOUNT_FILE}")
else:
    logger.info(f"✓ Service account file found: {SERVICE_ACCOUNT_FILE}")


def get_google_sheets_service():
    """
    Initialize Google Sheets API service with service account
    
    Returns:
        Resource: Google Sheets API service object
    """
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=credentials)
        logger.info("✓ Google Sheets service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Error initializing Google Sheets service: {e}")
        return None


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file
    
    Args:
        file_content: PDF file content in bytes
        
    Returns:
        str: Extracted text from PDF
    """
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                text += page_text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
                continue
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
            
        logger.info(f"✓ Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file
    
    Args:
        file_content: DOCX file content in bytes
        
    Returns:
        str: Extracted text from DOCX
    """
    try:
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        
        # Extract text from paragraphs
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += "\n" + cell.text
        
        if not text.strip():
            raise ValueError("No text could be extracted from DOCX")
            
        logger.info(f"✓ Extracted {len(text)} characters from DOCX")
        return text
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing DOCX: {str(e)}")


def parse_resume(text: str) -> dict:
    """
    Parse resume text and extract key information
    
    Args:
        text: Resume text content
        
    Returns:
        dict: Parsed resume data
    """
    logger.info("Parsing resume text...")
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Phone extraction (multiple formats)
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International format
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\d{10}',  # 10 digit format
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    
    # Name extraction (first non-empty line typically contains name)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name = lines[0] if lines else "Not found"
    
    # Skills extraction (expanded list)
    skills_keywords = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Ruby', 'PHP', 
        'Swift', 'Kotlin', 'Go', 'Rust', 'Scala', 'R',
        # Frameworks & Libraries
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 
        'Spring', 'Express', 'Next.js', 'Laravel',
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 
        'SQLite', 'Cassandra', 'DynamoDB',
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
        'Terraform', 'Ansible',
        # Tools & Technologies
        'Git', 'GitHub', 'GitLab', 'Jira', 'Agile', 'Scrum', 'REST API', 
        'GraphQL', 'Microservices',
        # Data & AI
        'Machine Learning', 'Deep Learning', 'AI', 'Data Science', 
        'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
        # Other
        'HTML', 'CSS', 'Sass', 'Tailwind', 'Bootstrap', 'Linux', 'Unix'
    ]
    
    found_skills = []
    text_lower = text.lower()
    for skill in skills_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    # Remove duplicates while preserving order
    found_skills = list(dict.fromkeys(found_skills))
    
    # Experience extraction
    experience_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
        r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
    ]
    experience = "Not specified"
    for pattern in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            experience = match.group(0)
            break
    
    # Education extraction (expanded)
    education_keywords = [
        'Bachelor', 'Master', 'PhD', 'Doctorate', 'B.Tech', 'M.Tech', 
        'MBA', 'BS', 'MS', 'B.Sc', 'M.Sc', 'B.E', 'M.E', 'BBA', 'MCA',
        'BCA', 'Diploma', 'Associate'
    ]
    
    found_education = []
    for edu in education_keywords:
        if edu.lower() in text_lower:
            found_education.append(edu)
    
    # Remove duplicates
    found_education = list(dict.fromkeys(found_education))
    
    parsed_data = {
        "name": name,
        "email": emails[0] if emails else "Not found",
        "phone": phones[0] if phones else "Not found",
        "skills": found_skills,
        "experience": experience,
        "education": found_education,
        "raw_text_preview": text[:500]  # First 500 characters
    }
    
    logger.info(f"✓ Parsed resume: {name}, {len(found_skills)} skills found")
    return parsed_data


def write_to_google_sheets(data: dict):
    """
    Write parsed resume data to Google Sheets
    
    Args:
        data: Parsed resume data dictionary
        
    Returns:
        dict: Google Sheets API response
    """
    try:
        service = get_google_sheets_service()
        if not service:
            raise Exception("Failed to initialize Google Sheets service")
        
        if not SPREADSHEET_ID:
            raise Exception("GOOGLE_SPREADSHEET_ID not configured in .env file")
        
        # Prepare row data
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("name", ""),
            data.get("email", ""),
            data.get("phone", ""),
            ", ".join(data.get("skills", [])),
            data.get("experience", ""),
            ", ".join(data.get("education", [])),
            data.get("filename", "")
        ]
        
        # Append to sheet
        sheet = service.spreadsheets()
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A:H',
            valueInputOption='RAW',
            body={'values': [row]}
        ).execute()
        
        logger.info(f"✓ Data written to Google Sheets: {data.get('name', 'Unknown')}")
        return result
        
    except HttpError as error:
        logger.error(f"Google Sheets API error: {error}")
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {error}")
    except Exception as e:
        logger.error(f"Error writing to sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error writing to sheets: {str(e)}")


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """
    Health check endpoint
    
    Returns:
        dict: API status and configuration info
    """
    return {
        "status": "online",
        "service": "Resume Parser API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "sheets_configured": bool(SPREADSHEET_ID),
            "service_account_exists": os.path.exists(SERVICE_ACCOUNT_FILE),
            "sheet_name": SHEET_NAME
        },
        "endpoints": {
            "docs": "/docs",
            "parse_single": "/api/parse-resume",
            "parse_batch": "/api/parse-resumes-batch",
            "read_sheets": "/api/sheets/read"
        }
    }


@app.post("/api/parse-resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Parse a single resume file and store in Google Sheets
    
    Args:
        file: Resume file (PDF, DOC, DOCX)
        
    Returns:
        dict: Parsed resume data
    """
    logger.info(f"Received file: {file.filename}")
    
    # Validate file type
    allowed_types = [
        'application/pdf', 
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if file.content_type not in allowed_types:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file.content_type}. Only PDF, DOC, DOCX allowed"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    # Extract text based on file type
    if file.content_type == 'application/pdf':
        text = extract_text_from_pdf(content)
    else:
        text = extract_text_from_docx(content)
    
    # Parse the resume
    parsed_data = parse_resume(text)
    parsed_data["filename"] = file.filename
    
    # Write to Google Sheets
    try:
        sheet_result = write_to_google_sheets(parsed_data)
        parsed_data["sheets_status"] = "success"
        parsed_data["sheets_update"] = sheet_result.get('updates', {})
    except Exception as e:
        logger.error(f"Failed to write to Google Sheets: {e}")
        parsed_data["sheets_status"] = f"failed: {str(e)}"
    
    return {
        "success": True,
        "filename": file.filename,
        "parsed_data": parsed_data,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/parse-resumes-batch")
async def parse_resumes_batch(files: List[UploadFile] = File(...)):
    """
    Parse multiple resume files and store in Google Sheets
    
    Args:
        files: List of resume files (PDF, DOC, DOCX)
        
    Returns:
        dict: Batch parsing results
    """
    logger.info(f"Received {len(files)} files for batch processing")
    
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            logger.info(f"Processing: {file.filename}")
            
            # Validate file type
            allowed_types = [
                'application/pdf', 
                'application/msword', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            if file.content_type not in allowed_types:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Invalid file type: {file.content_type}"
                })
                failed += 1
                continue
            
            # Read and validate file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"File size exceeds {MAX_FILE_SIZE / (1024*1024)}MB limit"
                })
                failed += 1
                continue
            
            # Extract text
            if file.content_type == 'application/pdf':
                text = extract_text_from_pdf(content)
            else:
                text = extract_text_from_docx(content)
            
            # Parse resume
            parsed_data = parse_resume(text)
            parsed_data["filename"] = file.filename
            
            # Write to Google Sheets
            try:
                write_to_google_sheets(parsed_data)
                parsed_data["sheets_status"] = "success"
            except Exception as e:
                logger.error(f"Failed to write to sheets: {e}")
                parsed_data["sheets_status"] = f"failed: {str(e)}"
            
            results.append({
                "filename": file.filename,
                "success": True,
                "parsed_data": parsed_data
            })
            successful += 1
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
            failed += 1
    
    logger.info(f"Batch processing complete: {successful} success, {failed} failed")
    
    return {
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/sheets/read")
async def read_google_sheets(range_name: Optional[str] = None, limit: Optional[int] = None):
    """
    Read data from Google Sheets
    
    Args:
        range_name: Sheet range to read (default: all data)
        limit: Maximum number of rows to return
        
    Returns:
        dict: Sheet data
    """
    try:
        if not SPREADSHEET_ID:
            raise HTTPException(
                status_code=500, 
                detail="GOOGLE_SPREADSHEET_ID not configured in .env"
            )
        
        service = get_google_sheets_service()
        if not service:
            raise HTTPException(
                status_code=500, 
                detail="Failed to initialize Google Sheets service"
            )
        
        if not range_name:
            range_name = f"{SHEET_NAME}!A:H"
        
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        # Apply limit if specified
        if limit and len(values) > limit:
            values = values[:limit]
        
        logger.info(f"✓ Read {len(values)} rows from Google Sheets")
        
        return {
            "success": True,
            "rows": len(values),
            "data": values,
            "range": range_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reading sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading sheets: {str(e)}")


@app.delete("/api/sheets/clear")
async def clear_google_sheets():
    """
    Clear all data from Google Sheets (except headers)
    
    Returns:
        dict: Clear operation result
    """
    try:
        if not SPREADSHEET_ID:
            raise HTTPException(
                status_code=500, 
                detail="GOOGLE_SPREADSHEET_ID not configured"
            )
        
        service = get_google_sheets_service()
        if not service:
            raise HTTPException(
                status_code=500, 
                detail="Failed to initialize Google Sheets service"
            )
        
        # Clear data (keep headers in row 1)
        sheet = service.spreadsheets()
        result = sheet.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:H"
        ).execute()
        
        logger.info("✓ Google Sheets cleared successfully")
        
        return {
            "success": True,
            "message": "Sheet data cleared (headers preserved)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing sheets: {str(e)}")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("Starting Resume Parser API Server")
    logger.info("=" * 60)
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Docs: http://{HOST}:{PORT}/docs")
    logger.info("=" * 60)
    
    uvicorn.run(
        app, 
        host=HOST, 
        port=PORT,
        log_level="info"
    )