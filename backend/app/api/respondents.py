from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Response, ConversationTurn, Session as SessionModel
from app.schemas import ResponseData, ConversationTurnData, SessionResponse
from app.utils.logger import setup_logger

router = APIRouter(prefix="/respondents", tags=["respondents"])
logger = setup_logger(__name__)

@router.get("/{respondent_id}/sessions", response_model=List[SessionResponse])
def get_respondent_sessions(
    respondent_id: str,
    db: Session = Depends(get_db)
):
    """Get all sessions for a specific respondent."""
    try:
        sessions = db.query(SessionModel).filter(
            SessionModel.respondent_id == respondent_id
        ).all()
        
        if not sessions:
            raise HTTPException(status_code=404, detail="No sessions found for this respondent")
        
        return sessions
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get sessions for respondent {respondent_id}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{respondent_id}/responses", response_model=List[ResponseData])
def get_respondent_responses(
    respondent_id: str,
    db: Session = Depends(get_db)
):
    """Get all responses from a specific respondent across all sessions."""
    try:
        responses = db.query(Response).filter(
            Response.respondent_id == respondent_id
        ).all()
        
        if not responses:
            raise HTTPException(status_code=404, detail="No responses found for this respondent")
        
        return responses
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get responses for respondent {respondent_id}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{respondent_id}/conversation", response_model=List[ConversationTurnData])
def get_respondent_conversation(
    respondent_id: str,
    db: Session = Depends(get_db)
):
    """Get all conversation turns from a specific respondent."""
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.respondent_id == respondent_id
        ).order_by(ConversationTurn.timestamp).all()
        
        if not turns:
            raise HTTPException(status_code=404, detail="No conversation history found for this respondent")
        
        return turns
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get conversation for respondent {respondent_id}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{respondent_id}/summary")
def get_respondent_summary(
    respondent_id: str,
    db: Session = Depends(get_db)
):
    """Get a summary of all activity for a specific respondent."""
    try:
        sessions = db.query(SessionModel).filter(
            SessionModel.respondent_id == respondent_id
        ).all()
        
        responses = db.query(Response).filter(
            Response.respondent_id == respondent_id
        ).all()
        
        conversations = db.query(ConversationTurn).filter(
            ConversationTurn.respondent_id == respondent_id
        ).all()
        
        return {
            "respondent_id": respondent_id,
            "total_sessions": len(sessions),
            "completed_sessions": len([s for s in sessions if s.completed_at]),
            "total_responses": len(responses),
            "total_conversation_turns": len(conversations),
            "sessions": [
                {
                    "session_id": s.id,
                    "survey_id": s.survey_id,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "completed": s.completed_at is not None
                }
                for s in sessions
            ]
        }
    
    except Exception as e:
        logger.exception(f"Failed to get summary for respondent {respondent_id}")
        raise HTTPException(status_code=400, detail=str(e))