from fastapi import FastAPI, APIRouter, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import shutil
import aiofiles
import json

# Optional parsers
from io import BytesIO

try:
    from pypdf import PdfReader  # PDF text extraction
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document  # DOCX text extraction
except Exception:  # pragma: no cover
    Document = None

# Groq (text-only LLM extraction)
try:
    from groq import AsyncGroq  # type: ignore
except Exception:  # pragma: no cover
    AsyncGroq = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (must use env)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# App and router
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class UploadInitRequest(BaseModel):
    filename: str
    size: int
    mimeType: str

class UploadInitResponse(BaseModel):
    uploadId: str

class UploadCompleteRequest(BaseModel):
    uploadId: str

class ExtractResult(BaseModel):
    id: str
    filename: str
    mimeType: str
    text_chars: int
    extracted_skills: List[str]
    inferred_roles: List[str]
    created_at: str

class SkillMatch(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    match_percent: int
    matched_skills: List[str]
    missing_skills: List[str]

class AnalyzeResponse(BaseModel):
    analysis: ExtractResult
    matches: List[SkillMatch]

# Helpers: date serialization

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

# Filesystem for uploads
UPLOAD_ROOT = Path('/tmp/uploads')
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

# Seed job data
SEED_JOBS: List[Dict[str, Any]] = [
    {
        "title": "Software Engineer (Backend)",
        "company": "Acme Cloud",
        "description": "Build APIs with Python, FastAPI, MongoDB, Docker, CI/CD.",
        "required_skills": ["python", "fastapi", "mongodb", "docker", "ci/cd"],
        "location": "Remote",
        "level": "Mid",
    },
    {
        "title": "Data Scientist",
        "company": "Insight Analytics",
        "description": "Modeling in Python with pandas, numpy, scikit-learn, SQL.",
        "required_skills": ["python", "pandas", "numpy", "scikit-learn", "sql"],
        "location": "New York, NY",
        "level": "Mid",
    },
    {
        "title": "Frontend Engineer (React)",
        "company": "Pixel Labs",
        "description": "Build React apps with TypeScript, Tailwind, testing.",
        "required_skills": ["react", "typescript", "javascript", "html", "css", "tailwind"],
        "location": "San Francisco, CA",
        "level": "Mid",
    },
    {
        "title": "ML Engineer",
        "company": "VisionAI",
        "description": "Deploy ML models, PyTorch, TensorFlow, MLOps, Kubernetes.",
        "required_skills": ["python", "pytorch", "tensorflow", "mlops", "kubernetes"],
        "location": "Remote",
        "level": "Senior",
    },
    {
        "title": "DevOps Engineer",
        "company": "ShipIt",
        "description": "Kubernetes, Terraform, AWS, CI/CD pipelines.",
        "required_skills": ["kubernetes", "terraform", "aws", "ci/cd"],
        "location": "Remote",
        "level": "Mid",
    },
    {
        "title": "Product Manager (Tech)",
        "company": "NorthStar",
        "description": "Roadmaps, stakeholder mgmt, analytics, Jira.",
        "required_skills": ["product management", "analytics", "stakeholders", "jira"],
        "location": "Remote",
        "level": "Senior",
    },
    {
        "title": "Full Stack Engineer",
        "company": "StackWorks",
        "description": "Node.js, React, Postgres, AWS.",
        "required_skills": ["node.js", "react", "postgres", "aws", "javascript"],
        "location": "Austin, TX",
        "level": "Mid",
    },
    {
        "title": "Android Engineer",
        "company": "MobileCore",
        "description": "Kotlin, Android SDK, Jetpack, CI.",
        "required_skills": ["kotlin", "android", "jetpack", "ci/cd"],
        "location": "Remote",
        "level": "Mid",
    },
    {
        "title": "Data Engineer",
        "company": "Pipeline.io",
        "description": "ETL, Airflow, Spark, Python, SQL.",
        "required_skills": ["airflow", "spark", "python", "sql", "etl"],
        "location": "Remote",
        "level": "Mid",
    },
    {
        "title": "Security Engineer",
        "company": "ShieldSec",
        "description": "Threat modeling, AppSec, cloud security.",
        "required_skills": ["security", "appsec", "aws", "threat modeling"],
        "location": "Remote",
        "level": "Senior",
    },
]

async def ensure_seed_jobs():
    count = await db.jobs.count_documents({})
    if count == 0:
        now = iso_now()
        docs = []
        for j in SEED_JOBS:
            docs.append({
                "id": str(uuid.uuid4()),
                "title": j["title"],
                "company": j["company"],
                "description": j["description"],
                "required_skills": [s.lower() for s in j["required_skills"]],
                "location": j.get("location"),
                "level": j.get("level"),
                "created_at": now,
            })
        if docs:
            await db.jobs.insert_many(docs)
            logger.info(f"Seeded {len(docs)} jobs")

# Simple skill vocab
SKILL_VOCAB = {
    # Programming & frameworks
    "python", "java", "javascript", "typescript", "node.js", "node", "react", "angular", "vue",
    "fastapi", "flask", "django", "spring", "express",
    # Data
    "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "sql", "spark", "airflow",
    # DevOps
    "docker", "kubernetes", "terraform", "aws", "gcp", "azure", "ci/cd", "gitlab", "github actions",
    # Frontend
    "html", "css", "tailwind", "next.js",
    # Other
    "mongodb", "postgres", "redis", "mlops", "product management", "analytics", "jira", "etl",
    "security", "appsec", "threat modeling", "kotlin", "android", "jetpack"
}

SYNONYMS = {
    "node": "node.js",
    "js": "javascript",
    "ts": "typescript",
    "ci": "ci/cd",
    "postgresql": "postgres",
    "scikit learn": "scikit-learn",
}

ROLE_KEYWORDS = {
    "backend": ["fastapi", "django", "flask", "node.js", "express"],
    "frontend": ["react", "javascript", "typescript", "css", "html", "tailwind"],
    "full stack": ["react", "node.js", "postgres", "aws"],
    "data scientist": ["pandas", "numpy", "scikit-learn", "python"],
    "ml engineer": ["pytorch", "tensorflow", "mlops", "kubernetes"],
    "devops": ["kubernetes", "terraform", "aws", "ci/cd"],
}


def normalize(text: str) -> str:
    return text.lower()


def extract_text_from_pdf(data: bytes) -> str:
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(BytesIO(data))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"PDF parse failed: {e}")
        return ""


def extract_text_from_docx(data: bytes) -> str:
    if not Document:
        return ""
    try:
        bio = BytesIO(data)
        doc = Document(bio)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.warning(f"DOCX parse failed: {e}")
        return ""


def heuristic_skill_extraction(text: str) -> Dict[str, Any]:
    t = normalize(text)
    found = set()
    for token in SKILL_VOCAB:
        if token in t:
            found.add(SYNONYMS.get(token, token))
    # add synonyms by scanning raw keys too
    for raw, canon in SYNONYMS.items():
        if raw in t:
            found.add(canon)
    # infer roles
    roles = []
    for role, keys in ROLE_KEYWORDS.items():
        if any(k in t for k in keys):
            roles.append(role)
    return {"skills": sorted(found), "roles": sorted(set(roles))}


def score_jobs(skills: List[str], jobs: List[Dict[str, Any]]) -> List[SkillMatch]:
    skill_set = set(s.lower() for s in skills)
    matches: List[SkillMatch] = []
    for j in jobs:
        req = set((s or '').lower() for s in j.get('required_skills', []))
        matched = sorted(list(skill_set.intersection(req)))
        missing = sorted(list(req.difference(skill_set)))
        denom = max(len(req), 1)
        score = int(round(100 * len(matched) / denom))
        matches.append(SkillMatch(
            job_id=j['id'],
            job_title=j['title'],
            company=j['company'],
            location=j.get('location'),
            match_percent=score,
            matched_skills=matched,
            missing_skills=missing,
        ))
    # sort by score desc, then by company/title
    matches.sort(key=lambda m: (-m.match_percent, m.company, m.job_title))
    return matches[:8]


# ========= Groq text-only extraction =========
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

async def groq_extract_skills(text: str) -> Optional[Dict[str, Any]]:
    if not GROQ_API_KEY or not AsyncGroq:
        return None
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        prompt = f"""
        Extract skills and roles from the following resume text. Return ONLY valid JSON with keys: skills (array of strings), roles (array of strings).
        If uncertain, still return best-effort JSON. Avoid explanations.
        Resume:\n{text[:40000]}
        """
        resp = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You extract concise skill and role lists from resumes and reply only with JSON."},
                {"role": "user", "content": prompt},
            ],
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        skills = data.get("skills") or []
        roles = data.get("roles") or []
        # normalize
        skills = sorted({(s or '').strip().lower() for s in skills if isinstance(s, str) and s.strip()})
        roles = sorted({(r or '').strip().lower() for r in roles if isinstance(r, str) and r.strip()})
        return {"skills": skills, "roles": roles}
    except Exception as e:
        logger.warning(f"Groq extraction failed, falling back. Error: {e}")
        return None


@api_router.get("/")
async def root():
    return {"message": "Resume Matcher API ready"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(client_name=input.client_name)
    await db.status_checks.insert_one({
        **status_obj.dict(),
        "timestamp": status_obj.timestamp.isoformat(),
    })
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    # Pydantic will coerce timestamp string to datetime if needed; keep as-is
    return [StatusCheck(**sc) for sc in status_checks]


@api_router.post("/upload/init", response_model=UploadInitResponse)
async def upload_init(payload: UploadInitRequest):
    # prepare upload folder
    upload_id = str(uuid.uuid4())
    folder = UPLOAD_ROOT / upload_id
    folder.mkdir(parents=True, exist_ok=True)

    # Save simple metadata
    meta = {
        "id": upload_id,
        "filename": payload.filename,
        "size": payload.size,
        "mimeType": payload.mimeType,
        "created_at": iso_now(),
    }
    async def _save_meta():
        await db.uploads.insert_one(meta)
    await _save_meta()

    return UploadInitResponse(uploadId=upload_id)


@api_router.post("/upload/chunk")
async def upload_chunk(request: Request, uploadId: str, index: int):
    # Save raw bytes as chunk file
    folder = UPLOAD_ROOT / uploadId
    if not folder.exists():
        raise HTTPException(status_code=400, detail="Unknown uploadId")
    chunk_path = folder / f"chunk_{index}"
    body = await request.body()
    async with aiofiles.open(chunk_path, 'wb') as f:
        await f.write(body)
    return {"ok": True, "index": index}


@api_router.post("/upload/complete", response_model=AnalyzeResponse)
async def upload_complete(payload: UploadCompleteRequest):
    upload_id = payload.uploadId
    folder = UPLOAD_ROOT / upload_id
    if not folder.exists():
        raise HTTPException(status_code=400, detail="Unknown uploadId")

    # Load metadata
    meta = await db.uploads.find_one({"id": upload_id})
    if not meta:
        raise HTTPException(status_code=400, detail="Upload metadata missing")

    filename = meta.get("filename") or "file"
    mime = (meta.get("mimeType") or "application/octet-stream").lower()

    # Assemble chunks in order
    chunk_files = sorted([p for p in folder.iterdir() if p.name.startswith("chunk_")], key=lambda p: int(p.name.split("_")[1]))
    assembled = folder / filename
    async with aiofiles.open(assembled, 'wb') as out:
        for cf in chunk_files:
            async with aiofiles.open(cf, 'rb') as c:
                await out.write(await c.read())

    # Read assembled bytes
    async with aiofiles.open(assembled, 'rb') as f:
        data = await f.read()

    # Extract text based on mime
    text = ""
    if mime == "application/pdf" or filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(data)
    elif mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",) or filename.lower().endswith('.docx'):
        text = extract_text_from_docx(data)
    elif mime == "text/plain":
        try:
            text = data.decode('utf-8', errors='ignore')
        except Exception:
            text = ""
    else:
        # Try pdf, then docx heuristically
        text = extract_text_from_pdf(data) or extract_text_from_docx(data)

    if not text:
        # As a fallback, treat as raw text to still provide MVP experience
        try:
            text = data.decode('utf-8', errors='ignore')
        except Exception:
            text = ""

    # First try Groq text-only extraction if configured
    skills: List[str] = []
    roles: List[str] = []
    used_provider = "heuristic"

    groq_res = await groq_extract_skills(text)
    if groq_res and (groq_res.get("skills") or groq_res.get("roles")):
        skills = list(groq_res.get("skills", []))
        roles = list(groq_res.get("roles", []))
        used_provider = "groq"
    else:
        # Heuristic extraction (fallback)
        extracted = heuristic_skill_extraction(text)
        skills = extracted.get("skills", [])
        roles = extracted.get("roles", [])

    await ensure_seed_jobs()
    jobs = await db.jobs.find().to_list(1000)
    ranked = score_jobs(skills, jobs)

    analysis_id = str(uuid.uuid4())
    analysis_doc = {
        "id": analysis_id,
        "filename": filename,
        "mimeType": mime,
        "text_chars": len(text),
        "extracted_skills": skills,
        "inferred_roles": roles,
        "created_at": iso_now(),
        "provider": used_provider,
    }
    await db.analyses.insert_one(analysis_doc)

    # Optional cleanup: keep files for debugging
    # shutil.rmtree(folder, ignore_errors=True)

    # Remove Mongo _id from ranked jobs if present
    for m in ranked:
        pass

    return AnalyzeResponse(
        analysis=ExtractResult(**{k: v for k, v in analysis_doc.items() if k != 'provider'}),
        matches=ranked,
    )


@api_router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs():
    await ensure_seed_jobs()
    jobs = await db.jobs.find().to_list(1000)
    # Remove Mongo _id to avoid JSON serialization issues
    for j in jobs:
        j.pop("_id", None)
    return jobs


# Include router
app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()