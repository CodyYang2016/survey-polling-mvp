from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas import (
    SessionStartRequest,
    SessionStartResponse,
    AnswerRequest,
    NextQuestionResponse,
    SessionEndRequest,
    SessionEndResponse
)
from app.services.session_service import SessionService
from app.utils.logger import setup_logger

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = setup_logger(__name__)


@router.post("/start", response_model=SessionStartResponse)
def start_session(
    request_data: SessionStartRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """Start a new survey session."""
    try:
        service = SessionService(db)
        
        result = service.start_session(
            survey_id=request_data.survey_id,
            anonymous_id=request_data.anonymous_id,
            user_agent=req.headers.get("user-agent"),
            ip_address=req.client.host
        )
        
        return result
    
    except Exception as e:
        logger.exception("Failed to start session")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/answer", response_model=NextQuestionResponse)
async def submit_answer(
    session_id: UUID,
    answer: AnswerRequest,
    db: Session = Depends(get_db)
):
    """Submit an answer and get next question or follow-up."""
    try:
        service = SessionService(db)
        
        result = await service.submit_answer(
            session_id=session_id,
            question_id=answer.question_id,
            answer_type=answer.answer_type,
            text=answer.text,
            selected_option_id=answer.selected_option_id,
            parent_message_id=answer.parent_message_id
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        # Added too track error, remove potentially later
        logger.exception("Failed to submit answer")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/end", response_model=SessionEndResponse)
def end_session(
    session_id: UUID,
    request_data: SessionEndRequest,
    db: Session = Depends(get_db)
):
    """End interview gracefully."""
    try:
        service = SessionService(db)
        result = service.end_session(session_id, request_data.reason)
        return result
    
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=400, detail=str(e))