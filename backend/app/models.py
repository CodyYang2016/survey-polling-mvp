from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, Float,
    ForeignKey, Index, CheckConstraint, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    versions = relationship("SurveyVersion", back_populates="survey")
    
    __table_args__ = (
        Index('idx_surveys_active', 'is_active'),
    )


class SurveyVersion(Base):
    __tablename__ = "survey_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    json_definition = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    survey = relationship("Survey", back_populates="versions")
    questions = relationship("Question", back_populates="survey_version")
    sessions = relationship("Session", back_populates="survey_version")
    
    __table_args__ = (
        Index('idx_survey_versions_current', 'survey_id', 'is_current'),
    )


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_version_id = Column(UUID(as_uuid=True), ForeignKey("survey_versions.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    allow_prefer_not_to_answer = Column(Boolean, default=True)
    skip_logic = Column(JSONB)
    metadata_json = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    survey_version = relationship("SurveyVersion", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question")
    
    __table_args__ = (
        CheckConstraint("question_type IN ('single_choice', 'free_text', 'multiple_choice')"),
        Index('idx_questions_version_position', 'survey_version_id', 'position'),
    )


class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(500), nullable=False)
    position = Column(Integer, nullable=False)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    question = relationship("Question", back_populates="options")
    
    __table_args__ = (
        Index('idx_question_options_question', 'question_id', 'position'),
    )


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_version_id = Column(UUID(as_uuid=True), ForeignKey("survey_versions.id"), nullable=False)
    anonymous_id = Column(String(255))
    status = Column(String(50), default='active')
    current_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    current_question_position = Column(Integer, default=0)
    current_probe_count = Column(Integer, default=0)
    is_follow_up_pending = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(Text)
    ip_address = Column(INET)
    
    survey_version = relationship("SurveyVersion", back_populates="sessions")
    messages = relationship("SessionMessage", back_populates="session", order_by="SessionMessage.sequence_number")
    summary = relationship("SessionSummary", back_populates="session", uselist=False)
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'abandoned')"),
        Index('idx_sessions_status', 'status'),
        Index('idx_sessions_survey_version', 'survey_version_id'),
    )


class SessionMessage(Base):
    __tablename__ = "session_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(50), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    message_text = Column(Text, nullable=False)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("question_options.id"))
    is_follow_up = Column(Boolean, default=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("session_messages.id"))
    followup_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sequence_number = Column(Integer, nullable=False)
    
    session = relationship("Session", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint(
            "message_type IN ('survey_question', 'user_answer', 'follow_up_question', "
            "'follow_up_answer', 'system_message', 'prefer_not_to_answer')"
        ),
        Index('idx_session_messages_session', 'session_id', 'sequence_number'),
    )


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    key_themes = Column(ARRAY(String))
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="summary")


class ModelCall(Base):
    __tablename__ = "model_calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    agent_type = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    provider = Column(String(50), default="anthropic")
    prompt_text = Column(Text, nullable=False)
    system_prompt = Column(Text)
    temperature = Column(Float)
    max_tokens = Column(Integer)
    response_text = Column(Text, nullable=False)
    finish_reason = Column(String(50))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    latency_ms = Column(Integer)
    cost_usd = Column(Float)
    reasoning_trace = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("agent_type IN ('follow_up', 'summary', 'exit_detector')"),
        Index('idx_model_calls_session', 'session_id', 'created_at'),
        Index('idx_model_calls_agent', 'agent_type', 'created_at'),
    )