📄 Resume Parser API

A FastAPI-based backend that parses resumes (PDF/DOC/DOCX), extracts key details, detects duplicates, and saves data to Google Sheets.

🚀 Features

Parse PDF, DOC, DOCX resumes

Extract Name, Email, Phone, Skills, Experience, Education

Duplicate detection (by email or phone)

Google Sheets integration via Service Account

Batch upload support

Interactive Swagger UI

⚙️ Setup
git clone <repo-url>
cd resume-parser-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Create .env file:

GOOGLE_SPREADSHEET_ID=your_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
SHEET_NAME=Sheet1


Run server:

uvicorn main:app --reload


Access:

API → http://localhost:8000

Docs → http://localhost:8000/docs

📚 Endpoints
Method	Endpoint	Description
GET	/	Health check
POST	/api/parse-resume	Parse single resume
POST	/api/parse-resumes-batch	Parse multiple resumes
GET	/api/sheets/read	Read sheet data
DELETE	/api/sheets/clear	Clear sheet data
🧠 Duplicate Logic

Checks email or phone in existing Google Sheet rows — skips or blocks duplicates.

🛠️ Tech Stack

FastAPI, Google Sheets API, PyPDF2, python-docx, dotenv

🔒 Security

Don’t commit .env or credentials.json

Validate file types and size

CORS configuration for frontend

📞 Contact

Author: Ankit Rai
Email: ankitrai9977363200@gmail.com

GitHub: https://github.com/ankitrai2304