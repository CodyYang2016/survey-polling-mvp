# Polling Survey AI Moderator - Complete MVP

Anonymous structured polling with AI-powered follow-up questions using Claude.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Anthropic API key ([Get one here](https://console.anthropic.com))

### Setup & Run

```powershell
# 1. Clone repository
git clone https://github.com/CodyYang2016/polling-survey-mvp.git
cd polling-survey-mvp

# 2. Set up environment
Copy-Item .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start everything
docker-compose up --build
```

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
- `POST /api/v1/sessions/start` - Start new session
- `POST /api/v1/sessions/{id}/answer` - Submit answer
- `POST /api/v1/sessions/{id}/end` - End interview

### Admin
- `GET /api/v1/admin/sessions` - List all sessions
- `GET /api/v1/admin/sessions/{id}` - Get session details

### Export
- `GET /api/v1/export/sessions.json` - Export as JSON
- `GET /api/v1/export/sessions.csv` - Export as CSV

## 🛠️ Development

### View Logs
```powershell
docker-compose logs -f api
```

### Run Tests
```powershell
docker-compose exec api pytest
```

### Stop Services
```powershell
docker-compose down
```

### Fresh Start (deletes database)
```powershell
docker-compose down -v
docker-compose up --build
```

## 📂 Project Structure

```
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
```

## 🔧 Troubleshooting

**Port already in use?**
Edit `docker-compose.yml` and change port mappings:
```yaml
ports:
  - "8001:8000"  # API
  - "3001:80"    # Frontend
```

**Database connection issues?**
```powershell
# Check if Postgres is healthy
docker-compose ps

# Restart services
docker-compose restart
```

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | - | Your Anthropic API key |
| `DATABASE_URL` | No | `postgresql://...` | PostgreSQL connection string |
| `APP_ENV` | No | `development` | Environment (development/production) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MAX_FOLLOWUP_PROBES` | No | `3` | Max follow-ups per question |

## 📄 License

MIT
