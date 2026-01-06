import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from ..models import (
    Session as SessionModel, 
    Response, 
    ConversationTurn, 
    Question,
    Survey,
    SurveyVersion
)
from ..schemas import SessionStartResponse, QuestionResponse, QuestionOption, NextQuestionResponse
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionService:
    """Service for managing survey sessions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_session(
        self,
        survey_id: str,
        respondent_id: Optional[str] = None,
        anonymous_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SessionStartResponse:
        """Start a new survey session."""
        
        # Generate respondent_id if not provided
        if not respondent_id:
            respondent_id = respondent_id or anonymous_id or self._generate_respondent_id()
        
        # Find survey by name
        survey = self.db.query(Survey).filter(Survey.name == survey_id).first()
        if not survey:
            raise ValueError(f"Survey '{survey_id}' not found")
        
        # Get current survey version
        version = self.db.query(SurveyVersion).filter(
            SurveyVersion.survey_id == survey.id,
            SurveyVersion.is_current == True
        ).first()
        
        if not version:
            raise ValueError(f"No active version found for survey '{survey_id}'")
        
        # Get questions
        questions = self.db.query(Question).filter(
            Question.survey_version_id == version.id
        ).order_by(Question.position).all()
        
        if not questions:
            raise ValueError(f"No questions found for survey '{survey_id}'")
        
        # Create session - REMOVE id parameter, let DB auto-generate
        session = SessionModel(
            survey_version_id=version.id,
            respondent_id=respondent_id,
            current_question_index=0
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Return first question
        first_question = questions[0]
        
        return SessionStartResponse(
            session_id=session.id,  # Use the auto-generated integer ID
            total_questions=len(questions),
            first_question=self._format_question(first_question)
        )
    
    async def submit_answer(
        self,
        session_id: int,  # Changed from UUID
        question_id: Optional[UUID],
        answer_type: str,
        text: Optional[str] = None,
        selected_option_id: Optional[str] = None,
        parent_message_id: Optional[UUID] = None
    ) -> NextQuestionResponse:
        """Submit an answer and get next question."""
        
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Save response if it's a regular answer
        if answer_type != "follow_up_answer" and question_id:
            response = Response(
                # REMOVED id parameter
                session_id=session_id,
                question_id=question_id,
                respondent_id=session.respondent_id,
                answer=text or selected_option_id or ""
            )
            self.db.add(response)
            self.db.commit()
        
        # Move to next question
        session.current_question_index += 1
        
        # Get next question
        questions = self.db.query(Question).filter(
            Question.survey_version_id == session.survey_version_id
        ).order_by(Question.position).all()
        
        if session.current_question_index >= len(questions):
            # Survey completed
            session.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            
            return NextQuestionResponse(
                message_type="completed",
                summary={
                    "questions_answered": session.current_question_index,
                    "duration_seconds": (datetime.now(timezone.utc) - session.started_at).total_seconds()
                }
            )
        
        self.db.commit()
        
        # Return next question
        next_question = questions[session.current_question_index]
        return NextQuestionResponse(
            message_type="survey_question",
            question=self._format_question(next_question)
        )

    def end_session(self, session_id: int, reason: str = "user_requested") -> Dict[str, Any]:
        """End a session."""
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return {
            "message_type": "completed",
            "summary": {
                "questions_answered": session.current_question_index,
                "duration_seconds": (datetime.now(timezone.utc) - session.started_at).total_seconds()
            }
        }
    
    
    def _generate_respondent_id(self) -> str:
        """Generate a unique respondent ID."""
        return f"resp_{uuid.uuid4().hex[:16]}"
    
    def _format_question(self, question: Question) -> QuestionResponse:
        """Format a question for the API response."""
        options = None
        if question.question_type == "single_choice":
            options = [
                QuestionOption(
                    option_id=str(opt.id),
                    text=opt.option_text
                )
                for opt in question.options
            ]
        
        return QuestionResponse(
            question_id=question.id,
            question_type=question.question_type,
            question_text=question.question_text,
            position=question.position,
            options=options
        )