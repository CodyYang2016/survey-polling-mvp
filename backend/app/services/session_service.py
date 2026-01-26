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
    SurveyVersion,
    SessionSummary  # ADD THIS LINE

)
from ..schemas import SessionStartResponse, QuestionResponse, QuestionOption, NextQuestionResponse
from ..utils.logger import setup_logger
from ..config import settings  # ADD THIS
from ..services.llm_client import LLMClient  # ADD THIS
from ..services.mock_llm_client import MockLLMClient  # ADD THIS
from ..agents.followup_agent import FollowUpAgent  # ADD THIS
from ..agents.summary_agent import SummaryAgent  # ADD THIS

logger = setup_logger(__name__)


class SessionService:
    """Service for managing survey sessions."""
    
    def __init__(self, db: Session):
        self.db = db

        # ADD THIS - Initialize LLM client based on settings
        if settings.use_mock_llm:
            logger.info("Using MockLLMClient")
            llm_client = MockLLMClient()
        else:
            logger.info("Using real LLMClient with Anthropic API")
            llm_client = LLMClient()
        
        # Initialize agents
        self.followup_agent = FollowUpAgent(llm_client)
        self.summary_agent = SummaryAgent(llm_client)
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
        session_id: int,
        question_id: Optional[UUID],
        answer_type: str,
        text: Optional[str] = None,
        selected_option_id: Optional[str] = None,
        parent_message_id: Optional[UUID] = None
    ) -> NextQuestionResponse:
        """Submit an answer and get next question or follow-up."""
        
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get current question
        question = None
        if question_id:
            question = self.db.query(Question).filter(Question.id == question_id).first()
        
        # Handle follow-up answers
        if answer_type == "follow_up_answer":
            # Save the follow-up conversation turn (use 'message' not 'message_text')
            if text:
                turn = ConversationTurn(
                    session_id=session_id,
                    respondent_id=session.respondent_id,
                    speaker="user",
                    message=text  # ✅ CORRECT field name
                )
                self.db.add(turn)
                self.db.commit()
            
            # After follow-up, move to next question
            session.current_question_index += 1
            
        else:
            # Regular answer - save it
            if question_id:
                response = Response(
                    session_id=session_id,
                    question_id=question_id,
                    respondent_id=session.respondent_id,
                    answer=text or selected_option_id or ""
                )
                self.db.add(response)
                self.db.commit()
            
            # Check if we should ask a follow-up using the LLM agent
            if question and text and answer_type != "prefer_not_to_answer":
                # Get conversation history for this question
                conversation_history = self.db.query(ConversationTurn).filter(
                    ConversationTurn.session_id == session_id
                ).order_by(ConversationTurn.timestamp).all()
                
                probe_count = len([t for t in conversation_history if t.speaker == "assistant"])
                
                # Get selected option text if applicable
                selected_option_text = None
                if selected_option_id and question.question_type == "single_choice":
                    option = next((opt for opt in question.options if str(opt.id) == selected_option_id), None)
                    if option:
                        selected_option_text = option.option_text
                
                # Call the follow-up agent
                try:
                    followup_decision = await self.followup_agent.should_ask_followup(
                        question_text=question.question_text,
                        question_type=question.question_type,
                        user_answer=text or selected_option_text or "",
                        selected_option_text=selected_option_text,
                        conversation_history=[
                            {"role": t.speaker, "content": t.message}  # ✅ CORRECT field
                            for t in conversation_history
                        ],
                        probe_count=probe_count,
                        session_id=str(session_id),
                        db=self.db
                    )
                    
                    logger.info(f"Follow-up decision: {followup_decision['action']}")
                    
                    # If agent wants to ask a follow-up
                    if followup_decision["action"] == "ask_followup":
                        followup_question = followup_decision.get("followup_question")
                        
                        if followup_question:
                            # Save the follow-up question
                            turn = ConversationTurn(
                                session_id=session_id,
                                respondent_id=session.respondent_id,
                                speaker="assistant",
                                message=followup_question  # ✅ CORRECT field
                            )
                            self.db.add(turn)
                            self.db.commit()
                            
                            return NextQuestionResponse(
                                message_type="follow_up_question",
                                question_text=followup_question  # ✅ Frontend expects this
                            )
                
                except Exception as e:
                    # Log error but don't fail - just continue to next question
                    logger.error(f"Follow-up agent error: {e}")
                
                # Update summary (save to SessionSummary table, not Session.summary)
                try:
                    followup_q = [t.message for t in conversation_history if t.speaker == "assistant"]
                    followup_a = [t.message for t in conversation_history if t.speaker == "user"]
                    
                    summary_result = await self.summary_agent.update_summary(
                        current_summary="",  # Get from SessionSummary if exists
                        question_text=question.question_text,
                        user_answer=text or selected_option_text or "",
                        followup_questions=followup_q,
                        followup_answers=followup_a,
                        session_id=str(session_id),
                        db=self.db
                    )
                    
                    # Save to SessionSummary table
                    existing_summary = self.db.query(SessionSummary).filter(
                        SessionSummary.session_id == session_id
                    ).first()
                    
                    if existing_summary:
                        existing_summary.summary_text = summary_result.get("summary", "")
                        existing_summary.key_themes = summary_result.get("key_themes", [])
                    else:
                        new_summary = SessionSummary(
                            session_id=session_id,
                            summary_text=summary_result.get("summary", ""),
                            key_themes=summary_result.get("key_themes", [])
                        )
                        self.db.add(new_summary)
                    
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Summary agent error: {e}")
            
            # Move to next question
            session.current_question_index += 1
        
        # Get next question
        questions = self.db.query(Question).filter(
            Question.survey_version_id == session.survey_version_id
        ).order_by(Question.position).all()
        
        if session.current_question_index >= len(questions):
            # Survey completed
            session.completed_at = datetime.now(timezone.utc)
            session.status = "completed"
            self.db.commit()
            
            # Get final summary
            final_summary = self.db.query(SessionSummary).filter(
                SessionSummary.session_id == session_id
            ).first()
            
            return NextQuestionResponse(
                message_type="completed",
                summary={
                    "questions_answered": session.current_question_index,
                    "duration_seconds": (datetime.now(timezone.utc) - session.started_at).total_seconds(),
                    "session_summary": final_summary.summary_text if final_summary else ""
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