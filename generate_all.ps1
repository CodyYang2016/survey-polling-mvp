# Polling Survey MVP - Complete Project Generator (PowerShell)
# Repository: https://github.com/CodyYang2016/polling-survey-mvp
# 
# Usage:
#   1. Save this file as generate_all.ps1
#   2. Run: .\generate_all.ps1
#
# This creates the entire project structure with all files.

Write-Host "🚀 Generating Polling Survey MVP Project..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Create directory structure
Write-Host "📁 Creating directory structure..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "backend/app/agents" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/app/services" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/app/api" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/app/utils" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/alembic/versions" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/surveys" | Out-Null
New-Item -ItemType Directory -Force -Path "backend/tests" | Out-Null
New-Item -ItemType Directory -Force -Path "frontend/css" | Out-Null
New-Item -ItemType Directory -Force -Path "frontend/js" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# ROOT FILES
# ============================================================================

Write-Host "📝 Creating root configuration files..." -ForegroundColor Cyan

@"
# Anthropic API Key (REQUIRED)
ANTHROPIC_API_KEY=your_api_key_here

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/polling_survey

# Application
APP_ENV=development
LOG_LEVEL=INFO
MAX_FOLLOWUP_PROBES=3
SESSION_TIMEOUT_MINUTES=30
"@ | Out-File -FilePath ".env.example" -Encoding UTF8

@"
__pycache__/
*.py[cod]
*`$py.class
.Python
env/
venv/
ENV/
.pytest_cache/
.coverage
.env
.vscode/
.idea/
*.log
postgres_data/
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

@"
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: polling_survey
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/polling_survey
      - ANTHROPIC_API_KEY=`${ANTHROPIC_API_KEY}
      - APP_ENV=development
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app
      - ./backend/surveys:/app/surveys
    command: >
      sh -c "
        echo '⏳ Running database migrations...' &&
        alembic upgrade head &&
        echo '✅ Migrations complete' &&
        echo '📋 Loading sample survey...' &&
        python3 << 'PYEOF'
from app.database import SessionLocal
from app.services.survey_service import SurveyService
from app.schemas import SurveyDefinition
import json
db = SessionLocal()
try:
    with open('surveys/immigration-opinion.json') as f:
        data = json.load(f)
    survey_def = SurveyDefinition(**data)
    service = SurveyService(db)
    version_id = service.ingest_survey(survey_def)
    print(f'✅ Survey loaded: {version_id}')
except Exception as e:
    print(f'ℹ️  Survey may already exist: {e}')
finally:
    db.close()
PYEOF
        echo '🚀 Starting API server...' &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "

  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - api

volumes:
  postgres_data:
"@ | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

@"
# Polling Survey AI Moderator - Complete MVP

Anonymous structured polling with AI-powered follow-up questions using Claude.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Anthropic API key ([Get one here](https://console.anthropic.com))

### Setup & Run

``````powershell
# 1. Clone repository
git clone https://github.com/CodyYang2016/polling-survey-mvp.git
cd polling-survey-mvp

# 2. Set up environment
Copy-Item .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start everything
docker-compose up --build
``````

### Access

- **Survey Interface**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3000/admin.html
- **API Documentation**: http://localhost:8000/docs
- **API Endpoint**: http://localhost:8000

## 📋 Features

✅ Anonymous survey sessions  
✅ AI follow-up questions (max 3 per question)  
✅ Real-time session summaries  
✅ "Prefer not to answer" option  
✅ "End interview" at any time  
✅ Admin dashboard with full transcripts  
✅ Export to JSON/CSV  

## 🏗️ Architecture

- **Backend**: FastAPI + PostgreSQL
- **AI Agents**: Claude Sonnet 4 (follow-ups) + Claude Haiku (summaries)
- **Frontend**: Vanilla JavaScript (mobile-friendly)

## 📖 API Endpoints

### Sessions
- ``POST /api/v1/sessions/start`` - Start new session
- ``POST /api/v1/sessions/{id}/answer`` - Submit answer
- ``POST /api/v1/sessions/{id}/end`` - End interview

### Admin
- ``GET /api/v1/admin/sessions`` - List all sessions
- ``GET /api/v1/admin/sessions/{id}`` - Get session details

### Export
- ``GET /api/v1/export/sessions.json`` - Export as JSON
- ``GET /api/v1/export/sessions.csv`` - Export as CSV

## 🛠️ Development

### View Logs
``````powershell
docker-compose logs -f api
``````

### Run Tests
``````powershell
docker-compose exec api pytest
``````

### Stop Services
``````powershell
docker-compose down
``````

### Fresh Start (deletes database)
``````powershell
docker-compose down -v
docker-compose up --build
``````

## 📂 Project Structure

``````
polling-survey-mvp/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents (FollowUp, Summary)
│   │   ├── api/             # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── main.py          # FastAPI application
│   ├── alembic/             # Database migrations
│   ├── surveys/             # Survey JSON definitions
│   └── tests/               # Unit tests
├── frontend/
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript
│   ├── index.html           # Survey interface
│   └── admin.html           # Admin dashboard
└── docker-compose.yml
``````

## 🔧 Troubleshooting

**Port already in use?**
Edit ``docker-compose.yml`` and change port mappings:
``````yaml
ports:
  - "8001:8000"  # API
  - "3001:80"    # Frontend
``````

**Database connection issues?**
``````powershell
# Check if Postgres is healthy
docker-compose ps

# Restart services
docker-compose restart
``````

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| ``ANTHROPIC_API_KEY`` | ✅ Yes | - | Your Anthropic API key |
| ``DATABASE_URL`` | No | ``postgresql://...`` | PostgreSQL connection string |
| ``APP_ENV`` | No | ``development`` | Environment (development/production) |
| ``LOG_LEVEL`` | No | ``INFO`` | Logging level |
| ``MAX_FOLLOWUP_PROBES`` | No | ``3`` | Max follow-ups per question |

## 📄 License

MIT
"@ | Out-File -FilePath "README.md" -Encoding UTF8

Write-Host "✅ Root files created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# BACKEND FILES
# ============================================================================

Write-Host "📝 Creating backend files..." -ForegroundColor Cyan

@"
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
anthropic==0.18.0
python-dotenv==1.0.0
python-multipart==0.0.6
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
"@ | Out-File -FilePath "backend/requirements.txt" -Encoding UTF8

@"
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"@ | Out-File -FilePath "backend/Dockerfile" -Encoding UTF8

@"
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.pytest_cache/
.coverage
*.log
.env
"@ | Out-File -FilePath "backend/.dockerignore" -Encoding UTF8

@"
⚠️  IMPORTANT: Large Files Not Included

Due to script size limits, you need to copy these files from the chat:

Required files (copy from chat messages above):
1. backend/app/models.py (database models)
2. backend/app/schemas.py (pydantic schemas)
3. backend/app/services/llm_client.py
4. backend/app/services/survey_service.py
5. backend/app/services/session_service.py (largest file ~400 lines)
6. backend/app/agents/prompts.py
7. backend/app/agents/followup_agent.py
8. backend/app/agents/summary_agent.py
9. backend/app/api/sessions.py
10. backend/app/api/admin.py
11. backend/app/api/export.py
12. backend/alembic/env.py
13. backend/alembic/versions/001_initial_schema.py

These files are in the chat conversation above.
Copy each one into its respective location.

After copying, the project will be complete and ready to run!
"@ | Out-File -FilePath "backend/SETUP_INSTRUCTIONS.txt" -Encoding UTF8

# Create small files
@"
`"``"``"Polling Survey AI Moderator Backend`"``"``"
"@ | Out-File -FilePath "backend/app/__init__.py" -Encoding UTF8

@"
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@postgres:5432/polling_survey"
    anthropic_api_key: str
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    session_timeout_minutes: int = 30
    max_followup_probes: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
"@ | Out-File -FilePath "backend/app/config.py" -Encoding UTF8

@"
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, echo=settings.app_env == "development")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"@ | Out-File -FilePath "backend/app/database.py" -Encoding UTF8

@"
`"``"``"Utilities`"``"``"
"@ | Out-File -FilePath "backend/app/utils/__init__.py" -Encoding UTF8

@"
import logging
import sys
from app.config import settings

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger
"@ | Out-File -FilePath "backend/app/utils/logger.py" -Encoding UTF8

@"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sessions, admin, export
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Polling Survey AI Moderator", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(sessions.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Polling Survey AI Moderator API", "version": "1.0.0", "status": "operational"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
"@ | Out-File -FilePath "backend/app/main.py" -Encoding UTF8

# Create empty __init__.py files
"" | Out-File -FilePath "backend/app/agents/__init__.py" -Encoding UTF8
"" | Out-File -FilePath "backend/app/services/__init__.py" -Encoding UTF8
"" | Out-File -FilePath "backend/app/api/__init__.py" -Encoding UTF8
"" | Out-File -FilePath "backend/tests/__init__.py" -Encoding UTF8

# Sample survey
@"
{
  "survey": {
    "id": "immigration-opinion-2025",
    "name": "Immigration Policy Opinion Survey",
    "description": "A brief survey to understand public opinion on immigration policy.",
    "version": "1.0.0"
  },
  "questions": [
    {
      "id": "q1_immigration_sentiment",
      "type": "single_choice",
      "prompt": "How would you describe your overall view on immigration to the United States?",
      "required": true,
      "allow_prefer_not_to_answer": true,
      "options": [
        {"id": "very_positive", "text": "Very positive", "score": 5, "position": 0},
        {"id": "somewhat_positive", "text": "Somewhat positive", "score": 4, "position": 1},
        {"id": "neutral", "text": "Neutral / No strong opinion", "score": 3, "position": 2},
        {"id": "somewhat_negative", "text": "Somewhat negative", "score": 2, "position": 3},
        {"id": "very_negative", "text": "Very negative", "score": 1, "position": 4}
      ]
    },
    {
      "id": "q2_policy_preference",
      "type": "single_choice",
      "prompt": "Which of the following policy approaches do you most support?",
      "required": true,
      "allow_prefer_not_to_answer": true,
      "options": [
        {"id": "increase_legal", "text": "Increase legal immigration pathways", "position": 0},
        {"id": "maintain_current", "text": "Maintain current immigration levels", "position": 1},
        {"id": "reduce_all", "text": "Reduce both legal and illegal immigration", "position": 2},
        {"id": "focus_enforcement", "text": "Focus primarily on border enforcement", "position": 3},
        {"id": "path_to_citizenship", "text": "Create pathway to citizenship for undocumented immigrants", "position": 4}
      ]
    },
    {
      "id": "q3_reasoning",
      "type": "free_text",
      "prompt": "What factors most influence your view on immigration policy?",
      "required": false,
      "allow_prefer_not_to_answer": true
    }
  ]
}
"@ | Out-File -FilePath "backend/surveys/immigration-opinion.json" -Encoding UTF8

@"
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"@ | Out-File -FilePath "backend/alembic.ini" -Encoding UTF8

@"
`"``"`${message}

Revision ID: `${up_revision}
Revises: `${down_revision | comma,n}
Create Date: `${create_date}

`"``"
from alembic import op
import sqlalchemy as sa
`${imports if imports else ""}

revision = `${repr(up_revision)}
down_revision = `${repr(down_revision)}
branch_labels = `${repr(branch_labels)}
depends_on = `${repr(depends_on)}


def upgrade() -> None:
    `${upgrades if upgrades else "pass"}


def downgrade() -> None:
    `${downgrades if downgrades else "pass"}
"@ | Out-File -FilePath "backend/alembic/script.py.mako" -Encoding UTF8

Write-Host "✅ Backend base files created" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  NOTE: Large backend files require manual copying" -ForegroundColor Yellow
Write-Host "   See backend/SETUP_INSTRUCTIONS.txt for details" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# FRONTEND FILES
# ============================================================================

Write-Host "📝 Creating frontend files..." -ForegroundColor Cyan

@"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey - Share Your Opinion</title>
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/survey.css">
</head>
<body>
    <div class="container">
        <header class="survey-header">
            <h1>📋 Opinion Survey</h1>
            <p>Your responses are anonymous and help us understand different perspectives</p>
        </header>

        <div id="progress-section" class="progress-section hidden">
            <div class="progress-text">
                <span id="progress-text">Question 1 of 5</span>
                <span>🎯</span>
            </div>
            <div class="progress-bar">
                <div id="progress-bar" class="progress-fill" style="width: 0%"></div>
            </div>
        </div>

        <div id="question-container">
            <div class="card">
                <div class="loading-container">
                    <div class="spinner"></div>
                    <p class="mt-2">Loading survey...</p>
                </div>
            </div>
        </div>

        <footer style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 0.875rem;">
            <p>This survey uses AI to ask relevant follow-up questions</p>
            <p><a href="admin.html">Admin Dashboard</a></p>
        </footer>
    </div>

    <script src="js/config.js"></script>
    <script src="js/api.js"></script>
    <script src="js/survey.js"></script>
</body>
</html>
"@ | Out-File -FilePath "frontend/index.html" -Encoding UTF8

@"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Survey App</title>
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/admin.css">
</head>
<body>
    <div class="container">
        <header class="admin-header">
            <h1>📊 Admin Dashboard</h1>
            <p>Manage and view all survey sessions</p>
        </header>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div class="export-buttons">
                    <button id="export-json-btn" class="btn-primary">📥 Export JSON</button>
                    <button id="export-csv-btn" class="btn-secondary">📥 Export CSV</button>
                </div>
                <button id="refresh-btn" class="btn-outline">🔄 Refresh</button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" data-view="list">All Sessions</button>
        </div>

        <div id="content">
            <div class="card">
                <div class="loading-container">
                    <div class="spinner"></div>
                    <p class="mt-2">Loading sessions...</p>
                </div>
            </div>
        </div>

        <footer style="text-align: center; padding: 20px;">
            <p><a href="index.html">← Back to Survey</a></p>
        </footer>
    </div>

    <script src="js/config.js"></script>
    <script src="js/api.js"></script>
    <script src="js/admin.js"></script>
</body>
</html>
"@ | Out-File -FilePath "frontend/admin.html" -Encoding UTF8

@"
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    SURVEY_ID: 'Immigration Policy Opinion Survey',
    DEBUG: true
};

const log = (...args) => {
    if (CONFIG.DEBUG) {
        console.log('[Survey App]', ...args);
    }
};
"@ | Out-File -FilePath "frontend/js/config.js" -Encoding UTF8

@"
⚠️  FRONTEND FILES NOT INCLUDED

Due to script size limits, copy these files from the chat:

Required files:
1. frontend/css/main.css (shared styles)
2. frontend/css/survey.css (survey-specific)
3. frontend/css/admin.css (admin-specific)
4. frontend/js/api.js (API client)
5. frontend/js/survey.js (survey logic ~400 lines)
6. frontend/js/admin.js (admin logic ~300 lines)

These files are in the chat conversation above.
Search for "### --- frontend/css/main.css ---" etc.

After copying, the project will be complete!
"@ | Out-File -FilePath "frontend/SETUP_INSTRUCTIONS.txt" -Encoding UTF8

Write-Host "✅ Frontend base files created" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  NOTE: Large frontend files require manual copying" -ForegroundColor Yellow
Write-Host "   See frontend/SETUP_INSTRUCTIONS.txt for details" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "==================================================" -ForegroundColor Green
Write-Host "✨ Project Structure Created!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📂 Directory structure is complete" -ForegroundColor Cyan
Write-Host "📝 Base configuration files created" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  NEXT STEPS REQUIRED:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Copy large files from chat (marked in SETUP_INSTRUCTIONS.txt)" -ForegroundColor White
Write-Host "   - backend/app/models.py" -ForegroundColor Gray
Write-Host "   - backend/app/schemas.py" -ForegroundColor Gray
Write-Host "   - backend/app/services/*.py (3 files)" -ForegroundColor Gray
Write-Host "   - backend/app/agents/*.py (3 files)" -ForegroundColor Gray
Write-Host "   - backend/app/api/*.py (3 files)" -ForegroundColor Gray
Write-Host "   - backend/alembic/env.py" -ForegroundColor Gray
Write-Host "   - backend/alembic/versions/001_initial_schema.py" -ForegroundColor Gray
Write-Host "   - frontend/css/*.css (3 files)" -ForegroundColor Gray
Write-Host "   - frontend/js/api.js" -ForegroundColor Gray
Write-Host "   - frontend/js/survey.js" -ForegroundColor Gray
Write-Host "   - frontend/js/admin.js" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Set up environment:" -ForegroundColor White
Write-Host "   Copy-Item .env.example .env" -ForegroundColor Gray
Write-Host "   # Edit .env and add ANTHROPIC_API_KEY" -ForegroundColor Gray
Write-Host ""
Write-Host "3. After copying all files, run:" -ForegroundColor White
Write-Host "   docker-compose up --build" -ForegroundColor Gray
Write-Host ""
Write-Host "🔍 Files to copy are clearly marked in the chat with:" -ForegroundColor Cyan
Write-Host "   ### --- path/to/file ---" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 TIP: Use VS Code's multi-cursor to paste files quickly!" -ForegroundColor Cyan
Write-Host ""