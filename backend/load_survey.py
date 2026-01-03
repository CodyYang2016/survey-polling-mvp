#!/usr/bin/env python3
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