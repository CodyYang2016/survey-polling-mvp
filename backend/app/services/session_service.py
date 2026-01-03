from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Session as SessionModel,
    SessionMessage,
    SessionSummary,
    Question,
    QuestionOption
)
from app.services.survey_service import SurveyService
from app.services.llm_client import LLMClient
from app.agents.followup_agent import FollowUpAgent
from app.agents.summary_agent import SummaryAgent
from app.utils.logger import setup_logger
from app.config import settings


logger = setup_logger(__name__)


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.survey_service = SurveyService(db)
        
        # Use mock or real LLM based on config
        if settings.use_mock_llm:
            from app.services.mock_llm_client import MockLLMClient
            self.llm_client = MockLLMClient()
        else:
            self.llm_client = LLMClient()
        
        self.followup_agent = FollowUpAgent(self.llm_client)
        self.summary_agent = SummaryAgent(self.llm_client)
    def start_session(
        self,
        survey_id: str,
        anonymous_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a new survey session."""
        
        survey_version = self.survey_service.get_current_survey_version(survey_id)
        
        questions = self.db.query(Question).filter(
            Question.survey_version_id == survey_version.id
        ).order_by(Question.position).all()
        
        if not questions:
            raise ValueError(f"Survey version {survey_version.id} has no questions")
        
        session = SessionModel(
            id=uuid4(),
            survey_version_id=survey_version.id,
            anonymous_id=anonymous_id,
            current_question_id=questions[0].id,
            current_question_position=0,
            status='active',
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.db.add(session)
        self.db.flush()
        
        summary = SessionSummary(
            id=uuid4(),
            session_id=session.id,
            summary_text="Session started. No responses yet.",
            key_themes=[],
            message_count=0
        )
        self.db.add(summary)
        
        if not survey_version.is_locked:
            survey_version.is_locked = True
        
        self.db.commit()
        
        logger.info(f"Session started: {session.id}")
        
        return {
            "session_id": str(session.id),
            "survey_name": survey_version.survey.name,
            "total_questions": len(questions),
            "first_question": self._format_question(questions[0])
        }
    
    async def submit_answer(
        self,
        session_id: UUID,
        question_id: Optional[UUID],
        answer_type: str,
        text: Optional[str],
        selected_option_id: Optional[UUID],
        parent_message_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Submit an answer and get next question or follow-up."""
        
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != 'active':
            raise ValueError(f"Session {session_id} is not active")
        
        if answer_type == "prefer_not_to_answer":
            return await self._handle_prefer_not_to_answer(session)
        
        if answer_type == "follow_up_answer":
            return await self._handle_followup_answer(session, text, parent_message_id)
        
        return await self._handle_regular_answer(
            session, question_id, answer_type, text, selected_option_id
        )
    
    async def _handle_regular_answer(
        self,
        session: SessionModel,
        question_id: UUID,
        answer_type: str,
        text: Optional[str],
        selected_option_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Handle regular survey question answer."""
        
        question = self.db.query(Question).filter(
            Question.id == question_id
        ).first()
        
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        answer_text = text or ""
        selected_option_text = None
        
        if selected_option_id:
            option = self.db.query(QuestionOption).filter(
                QuestionOption.id == selected_option_id
            ).first()
            if option:
                selected_option_text = option.option_text
                answer_text = selected_option_text
        
        sequence_number = self._get_next_sequence_number(session.id)
        
        answer_message = SessionMessage(
            id=uuid4(),
            session_id=session.id,
            message_type='user_answer',
            question_id=question_id,
            message_text=answer_text,
            selected_option_id=selected_option_id,
            is_follow_up=False,
            sequence_number=sequence_number
        )
        self.db.add(answer_message)
        self.db.flush()
        
        logger.info(f"Answer recorded: session={session.id}, question={question_id}")
        
        conversation_history = self._get_conversation_history(session.id, question_id)
        
        followup_decision = await self.followup_agent.should_ask_followup(
            question_text=question.question_text,
            question_type=question.question_type,
            user_answer=answer_text,
            selected_option_text=selected_option_text,
            conversation_history=conversation_history,
            probe_count=session.current_probe_count,
            session_id=str(session.id),
            db=self.db
        )
        
        if followup_decision["action"] == "ask_followup":
            followup_question = followup_decision["followup_question"]
            followup_reason = followup_decision["reason"]
            
            sequence_number = self._get_next_sequence_number(session.id)
            
            followup_message = SessionMessage(
                id=uuid4(),
                session_id=session.id,
                message_type='follow_up_question',
                question_id=question_id,
                message_text=followup_question,
                is_follow_up=True,
                parent_message_id=answer_message.id,
                followup_reason=followup_reason,
                sequence_number=sequence_number
            )
            self.db.add(followup_message)
            
            session.is_follow_up_pending = True
            session.current_probe_count += 1
            session.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Follow-up asked: session={session.id}, probe={session.current_probe_count}")
            
            return {
                "message_type": "follow_up_question",
                "question_text": followup_question,
                "is_follow_up": True,
                "reasoning": followup_reason,
                "progress": self._get_progress_info(session)
            }
        
        else:
            return await self._advance_to_next_question(session, question)
    
    async def _handle_followup_answer(
        self,
        session: SessionModel,
        text: str,
        parent_message_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Handle follow-up answer."""
        
        sequence_number = self._get_next_sequence_number(session.id)
        
        followup_answer = SessionMessage(
            id=uuid4(),
            session_id=session.id,
            message_type='follow_up_answer',
            question_id=session.current_question_id,
            message_text=text,
            is_follow_up=True,
            parent_message_id=parent_message_id,
            sequence_number=sequence_number
        )
        self.db.add(followup_answer)
        self.db.flush()
        
        question = self.db.query(Question).filter(
            Question.id == session.current_question_id
        ).first()
        
        conversation_history = self._get_conversation_history(session.id, question.id)
        
        followup_decision = await self.followup_agent.should_ask_followup(
            question_text=question.question_text,
            question_type=question.question_type,
            user_answer=text,
            selected_option_text=None,
            conversation_history=conversation_history,
            probe_count=session.current_probe_count,
            session_id=str(session.id),
            db=self.db
        )
        
        if followup_decision["action"] == "ask_followup" and session.current_probe_count < 3:
            followup_question = followup_decision["followup_question"]
            followup_reason = followup_decision["reason"]
            
            sequence_number = self._get_next_sequence_number(session.id)
            
            followup_message = SessionMessage(
                id=uuid4(),
                session_id=session.id,
                message_type='follow_up_question',
                question_id=question.id,
                message_text=followup_question,
                is_follow_up=True,
                parent_message_id=followup_answer.id,
                followup_reason=followup_reason,
                sequence_number=sequence_number
            )
            self.db.add(followup_message)
            
            session.current_probe_count += 1
            session.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "message_type": "follow_up_question",
                "question_text": followup_question,
                "is_follow_up": True,
                "reasoning": followup_reason,
                "progress": self._get_progress_info(session)
            }
        
        else:
            return await self._advance_to_next_question(session, question)
    
    async def _handle_prefer_not_to_answer(self, session: SessionModel) -> Dict[str, Any]:
        """Handle prefer not to answer."""
        
        sequence_number = self._get_next_sequence_number(session.id)
        
        message = SessionMessage(
            id=uuid4(),
            session_id=session.id,
            message_type='prefer_not_to_answer',
            question_id=session.current_question_id,
            message_text="Prefer not to answer",
            is_follow_up=False,
            sequence_number=sequence_number
        )
        self.db.add(message)
        self.db.flush()
        
        question = self.db.query(Question).filter(
            Question.id == session.current_question_id
        ).first()
        
        return await self._advance_to_next_question(session, question, skip_summary=True)
    
    async def _advance_to_next_question(
        self,
        session: SessionModel,
        current_question: Question,
        skip_summary: bool = False
    ) -> Dict[str, Any]:
        """Advance to next survey question."""
        
        if not skip_summary:
            await self._update_session_summary(session, current_question)
        
        questions = self.db.query(Question).filter(
            Question.survey_version_id == session.survey_version_id
        ).order_by(Question.position).all()
        
        session.current_probe_count = 0
        session.is_follow_up_pending = False
        
        next_position = session.current_question_position + 1
        
        if next_position >= len(questions):
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            session.last_activity_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Session completed: {session.id}")
            
            return {
                "message_type": "completed",
                "progress": self._get_progress_info(session)
            }
        
        next_question = questions[next_position]
        session.current_question_id = next_question.id
        session.current_question_position = next_position
        session.last_activity_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "message_type": "survey_question",
            "question": self._format_question(next_question),
            "is_follow_up": False,
            "progress": self._get_progress_info(session)
        }
    
    async def _update_session_summary(self, session: SessionModel, question: Question):
        """Update running session summary."""
        
        summary = self.db.query(SessionSummary).filter(
            SessionSummary.session_id == session.id
        ).first()
        
        messages = self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session.id,
            SessionMessage.question_id == question.id
        ).order_by(SessionMessage.sequence_number).all()
        
        user_answer = ""
        followup_questions = []
        followup_answers = []
        
        for msg in messages:
            if msg.message_type == 'user_answer':
                user_answer = msg.message_text
            elif msg.message_type == 'follow_up_question':
                followup_questions.append(msg.message_text)
            elif msg.message_type == 'follow_up_answer':
                followup_answers.append(msg.message_text)
        
        updated_summary = await self.summary_agent.update_summary(
            current_summary=summary.summary_text,
            question_text=question.question_text,
            user_answer=user_answer,
            followup_questions=followup_questions,
            followup_answers=followup_answers,
            session_id=str(session.id),
            db=self.db
        )
        
        summary.summary_text = updated_summary["summary"]
        summary.key_themes = updated_summary["key_themes"]
        summary.last_updated_at = datetime.utcnow()
        summary.message_count = len(messages)
        
        self.db.flush()
        
        logger.info(f"Summary updated: session={session.id}")
    
    def end_session(self, session_id: UUID, reason: str) -> Dict[str, Any]:
        """End session gracefully."""
        
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = 'completed'
        session.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        summary = self.db.query(SessionSummary).filter(
            SessionSummary.session_id == session_id
        ).first()
        
        message_count = self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id
        ).count()
        
        questions_count = self.db.query(Question).filter(
            Question.survey_version_id == session.survey_version_id
        ).count()
        
        duration_seconds = int(
            (session.completed_at - session.started_at).total_seconds()
        )
        
        logger.info(f"Session ended: {session.id}, reason={reason}")
        
        return {
            "status": "completed",
            "message": "Thank you for your time. Your responses have been recorded.",
            "summary": {
                "questions_answered": session.current_question_position,
                "total_questions": questions_count,
                "duration_seconds": duration_seconds,
                "summary_text": summary.summary_text if summary else None
            }
        }
    
    def _format_question(self, question: Question) -> Dict[str, Any]:
        """Format question for API response."""
        
        result = {
            "question_id": str(question.id),
            "question_type": question.question_type,
            "question_text": question.question_text,
            "position": question.position + 1,
            "is_required": question.is_required,
            "allow_prefer_not_to_answer": question.allow_prefer_not_to_answer
        }
        
        if question.question_type == 'single_choice':
            options = self.db.query(QuestionOption).filter(
                QuestionOption.question_id == question.id
            ).order_by(QuestionOption.position).all()
            
            result["options"] = [
                {
                    "option_id": str(opt.id),
                    "text": opt.option_text,
                    "score": opt.score
                }
                for opt in options
            ]
        
        return result
    
    def _get_next_sequence_number(self, session_id: UUID) -> int:
        """Get next sequence number for message."""
        
        max_seq = self.db.query(
            func.max(SessionMessage.sequence_number)
        ).filter(
            SessionMessage.session_id == session_id
        ).scalar() or 0
        
        return max_seq + 1
    
    def _get_conversation_history(
        self,
        session_id: UUID,
        question_id: UUID
    ) -> List[Dict[str, str]]:
        """Get conversation history for current question."""
        
        messages = self.db.query(SessionMessage).filter(
            SessionMessage.session_id == session_id,
            SessionMessage.question_id == question_id,
            SessionMessage.is_follow_up == True
        ).order_by(SessionMessage.sequence_number).all()
        
        history = []
        question_text = None
        
        for msg in messages:
            if msg.message_type == 'follow_up_question':
                question_text = msg.message_text
            elif msg.message_type == 'follow_up_answer' and question_text:
                history.append({
                    "question": question_text,
                    "answer": msg.message_text
                })
                question_text = None
        
        return history
    
    def _get_progress_info(self, session: SessionModel) -> Dict[str, Any]:
        """Get progress information."""
        
        questions_count = self.db.query(Question).filter(
            Question.survey_version_id == session.survey_version_id
        ).count()
        
        return {
            "current_position": session.current_question_position + 1,
            "total_questions": questions_count,
            "is_follow_up_pending": session.is_follow_up_pending
        }