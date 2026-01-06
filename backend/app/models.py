from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base


class Survey(Base):
    """Base survey entity"""
    __tablename__ = "surveys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    versions = relationship("SurveyVersion", back_populates="survey", cascade="all, delete-orphan")


class SurveyVersion(Base):
    """Versioned survey definition"""
    __tablename__ = "survey_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)
    json_definition = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    survey = relationship("Survey", back_populates="versions")
    questions = relationship("Question", back_populates="survey_version", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="survey_version", cascade="all, delete-orphan")


class Question(Base):
    """Survey question linked to a specific version"""
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_version_id = Column(UUID(as_uuid=True), ForeignKey("survey_versions.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    allow_prefer_not_to_answer = Column(Boolean, default=False)
    skip_logic = Column(JSON)
    metadata_json = Column(JSON)
    
    survey_version = relationship("SurveyVersion", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    """Options for multiple choice questions"""
    __tablename__ = "question_options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    score = Column(Integer)
    
    question = relationship("Question", back_populates="options")


class Session(Base):
    """Survey response session"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_version_id = Column(UUID(as_uuid=True), ForeignKey("survey_versions.id", ondelete="CASCADE"), nullable=False)
    respondent_id = Column(String, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    current_question_index = Column(Integer, default=0)
    status = Column(String, default="in_progress")  # 'in_progress', 'completed', 'abandoned'
    
    survey_version = relationship("SurveyVersion", back_populates="sessions")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")
    conversation_history = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")


class Response(Base):
    """Individual question response"""
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    respondent_id = Column(String, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="responses")
    question = relationship("Question", back_populates="responses")


class ConversationTurn(Base):
    """Conversation history for follow-up questions"""
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    respondent_id = Column(String, nullable=False, index=True)
    speaker = Column(String, nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="conversation_history")


class SessionMessage(Base):
    """Individual messages in a session"""
    __tablename__ = "session_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    message_text = Column(Text, nullable=False)
    is_follow_up = Column(Boolean, default=False)
    followup_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", foreign_keys=[session_id])


class SessionSummary(Base):
    """Session summary generated at completion"""
    __tablename__ = "session_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    key_themes = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", foreign_keys=[session_id])


class ModelCall(Base):
    """LLM API call tracking"""
    __tablename__ = "model_calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String, nullable=False)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Integer)  # Store as cents to avoid float precision issues
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", foreign_keys=[session_id])