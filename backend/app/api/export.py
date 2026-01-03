from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import json
import csv
import io

from app.database import get_db
from app.models import (
    Session as SessionModel,
    SessionMessage,
    SessionSummary,
    SurveyVersion
)
from app.utils.logger import setup_logger

router = APIRouter(prefix="/export", tags=["export"])
logger = setup_logger(__name__)


@router.get("/sessions.json")
def export_sessions_json(db: Session = Depends(get_db)):
    """Export all sessions as JSON."""
    
    sessions = db.query(SessionModel).all()
    
    export_data = []
    for session in sessions:
        messages = db.query(SessionMessage).filter(
            SessionMessage.session_id == session.id
        ).order_by(SessionMessage.sequence_number).all()
        
        summary = db.query(SessionSummary).filter(
            SessionSummary.session_id == session.id
        ).first()
        
        survey_version = db.query(SurveyVersion).filter(
            SurveyVersion.id == session.survey_version_id
        ).first()
        
        export_data.append({
            "session_id": str(session.id),
            "survey_name": survey_version.survey.name if survey_version else None,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "summary": summary.summary_text if summary else None,
            "key_themes": summary.key_themes if summary else [],
            "messages": [
                {
                    "sequence": msg.sequence_number,
                    "type": msg.message_type,
                    "text": msg.message_text,
                    "is_follow_up": msg.is_follow_up
                }
                for msg in messages
            ]
        })
    
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=sessions.json"}
    )


@router.get("/sessions.csv")
def export_sessions_csv(db: Session = Depends(get_db)):
    """Export all sessions as CSV (flattened)."""
    
    sessions = db.query(SessionModel).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "session_id", "survey_name", "status", "started_at", "completed_at",
        "summary", "key_themes", "message_count"
    ])
    
    for session in sessions:
        message_count = db.query(SessionMessage).filter(
            SessionMessage.session_id == session.id
        ).count()
        
        summary = db.query(SessionSummary).filter(
            SessionSummary.session_id == session.id
        ).first()
        
        survey_version = db.query(SurveyVersion).filter(
            SurveyVersion.id == session.survey_version_id
        ).first()
        
        writer.writerow([
            str(session.id),
            survey_version.survey.name if survey_version else "",
            session.status,
            session.started_at.isoformat(),
            session.completed_at.isoformat() if session.completed_at else "",
            summary.summary_text if summary else "",
            ", ".join(summary.key_themes) if summary and summary.key_themes else "",
            message_count
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions.csv"}
    )