# Resume to Job Matcher

A full-stack web application that analyzes resumes and matches them with relevant job postings. The application extracts skills from uploaded resumes (PDF or DOCX) using AI-powered text analysis and heuristic methods, then calculates compatibility scores against a database of job listings.

## Features

- Resume upload with chunked file transfer for large files
- Support for PDF and DOCX file formats
- AI-powered skill extraction using Groq API (with heuristic fallback)
- Automatic job matching based on extracted skills
- Match percentage calculation with skill gap analysis
- Modern, responsive frontend with drag-and-drop interface
- Real-time upload progress tracking

## Technology Stack

### Backend
- FastAPI - Python web framework
- MongoDB - Database for storing uploads, analyses, and job listings
- Motor - Async MongoDB driver
- Groq - AI-powered text extraction
- pypdf - PDF text extraction
- python-docx - DOCX text extraction
- python-dotenv - Environment variable management

### Frontend
- React 19 - UI framework
- TailwindCSS - Styling
- Axios - HTTP client
- React Router - Navigation
- Radix UI - Component library

## Project Structure

```
CV-NEW-M1/
├── backend/
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (not in git)
│   └── .env.example           # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── App.css           # Application styles
│   │   └── components/       # UI components
│   ├── package.json          # Node dependencies
│   └── public/               # Static assets
├── tests/                     # Test files
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB (local instance or cloud deployment)
- Groq API key (optional, for AI-powered extraction)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="llama-3.3-70b-versatile"
```

5. Start the backend server:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
yarn install
```

3. Configure environment variables:
Create a `.env` file in the frontend directory:
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

4. Start the development server:
```bash
yarn start
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open the application in your browser
2. Drag and drop a resume file (PDF or DOCX) or click to browse
3. Click "Upload & Analyze" to process the resume
4. View extracted skills and job match results
5. Review matched skills and skill gaps for each job posting

## API Endpoints

### GET /api/
Health check endpoint

### POST /api/upload/init
Initialize a file upload session
- Request body: `{ filename, size, mimeType }`
- Response: `{ uploadId }`

### POST /api/upload/chunk
Upload a file chunk
- Query params: `uploadId`, `index`
- Request body: binary chunk data

### POST /api/upload/complete
Complete upload and analyze resume
- Request body: `{ uploadId }`
- Response: `{ analysis, matches }`

### GET /api/jobs
List all available job postings
- Response: Array of job objects

### POST /api/status
Create a status check (for monitoring)
- Request body: `{ client_name }`
- Response: Status check object

### GET /api/status
Get all status checks
- Response: Array of status check objects

## Skill Extraction

The application uses two methods for skill extraction:

1. **Groq AI Extraction** (primary): Uses Groq's LLM to intelligently extract skills and roles from resume text
2. **Heuristic Extraction** (fallback): Uses keyword matching against a predefined skill vocabulary

If Groq API is not configured or fails, the system automatically falls back to heuristic extraction.

## Job Matching

Job matching is based on skill overlap:
- Match percentage = (matched skills / required skills) * 100
- Results are sorted by match percentage
- Top 8 matches are returned
- Each match shows matched and missing skills

## Security Notes

- Never commit `.env` files to version control
- Use environment variables for all sensitive configuration
- The `.env.example` file shows required variables without actual values
- MongoDB connection should use authentication in production
- CORS origins should be restricted in production

## Development

### Running Tests
Backend tests can be run with:
```bash
cd backend
pytest
```

### Code Formatting
Backend uses Black for code formatting:
```bash
black backend/
```

### Linting
Backend uses flake8 for linting:
```bash
flake8 backend/
```

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `mongod` or check your MongoDB service
- Verify MONGO_URL in `.env` is correct
- Check network connectivity if using MongoDB Atlas

### Groq API Issues
- Verify GROQ_API_KEY is valid in `.env`
- Check your Groq API quota and limits
- The application will fall back to heuristic extraction if Groq fails

### File Upload Issues
- Check file size limits (currently supports files up to ~25MB)
- Ensure file format is PDF or DOCX
- Verify backend server is running and accessible

## License

This project is provided as-is for educational and development purposes.
