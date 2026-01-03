from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models import (
    Session as SessionModel,
    SessionMessage,
    SessionSummary,
    ModelCall,
    SurveyVersion
)
from app.schemas import SessionListItem, SessionDetail
from app.utils.logger import setup_logger

router = APIRouter(prefix="/admin", tags=["admin"])
logger = setup_logger(__name__)


@router.get("/sessions", response_model=List[SessionListItem])
def list_sessions(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all sessions with pagination."""
    
    query = db.query(SessionModel)
    
    if status:
        query = query.filter(SessionModel.status == status)
    
    sessions = query.order_by(
        SessionModel.started_at.desc()
    ).limit(limit).offset(offset).all()
    
    result = []
    for session in sessions:
        message_count = db.query(SessionMessage).filter(
            SessionMessage.session_id == session.id
        ).count()
        
        survey_version = db.query(SurveyVersion).filter(
            SurveyVersion.id == session.survey_version_id
        ).first()
        
        result.append({
            "session_id": session.id,
            "survey_name": survey_version.survey.name if survey_version else "Unknown",
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "message_count": message_count
        })
    
    return result


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session_detail(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed session information."""
    
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(SessionMessage).filter(
        SessionMessage.session_id == session_id
    ).order_by(SessionMessage.sequence_number).all()
    
    messages_data = [
        {
            "sequence_number": msg.sequence_number,
            "message_type": msg.message_type,
            "message_text": msg.message_text,
            "is_follow_up": msg.is_follow_up,
            "followup_reason": msg.followup_reason,
            "created_at": msg.created_at
        }
        for msg in messages
    ]
    
    summary = db.query(SessionSummary).filter(
        SessionSummary.session_id == session_id
    ).first()
    
    model_calls = db.query(ModelCall).filter(
        ModelCall.session_id == session_id
    ).all()
    
    total_tokens = sum(
        (mc.input_tokens or 0) + (mc.output_tokens or 0)
        for mc in model_calls
    )
    
    total_cost = sum(mc.cost_usd or 0 for mc in model_calls)
    
    survey_version = db.query(SurveyVersion).filter(
        SurveyVersion.id == session.survey_version_id
    ).first()
    
    return {
        "session_id": session.id,
        "survey_name": survey_version.survey.name if survey_version else "Unknown",
        "status": session.status,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "summary": summary.summary_text if summary else None,
        "key_themes": summary.key_themes if summary else None,
        "messages": messages_data,
        "llm_calls_count": len(model_calls), #changed from model
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost
    }