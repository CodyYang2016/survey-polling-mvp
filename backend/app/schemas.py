from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# ============================================================================
# SURVEY INGESTION SCHEMAS (for loading survey definitions)
# ============================================================================

class SkipLogic(BaseModel):
    """Skip logic for conditional questions"""
    condition: str
    target_question: Optional[str] = None
    
    class Config:
        extra = "allow"


class OptionDefinition(BaseModel):
    """Survey question option definition"""
    text: str
    position: int
    score: Optional[int] = None


class QuestionDefinition(BaseModel):
    """Survey question definition for ingestion"""
    type: str  # 'multiple_choice', 'text', 'scale', etc.
    prompt: str
    required: bool = True
    allow_prefer_not_to_answer: bool = False
    options: Optional[List[OptionDefinition]] = None
    skip_logic: Optional[SkipLogic] = None
    metadata: Optional[Dict[str, Any]] = None


class SurveyMetadata(BaseModel):
    """Survey metadata for ingestion"""
    name: str
    description: Optional[str] = None


class SurveyDefinition(BaseModel):
    """Complete survey definition for ingestion"""
    survey: SurveyMetadata
    questions: List[QuestionDefinition]


# ============================================================================
# SESSION & RESPONSE SCHEMAS (for runtime operations with respondent_id)
# ============================================================================

class SessionCreate(BaseModel):
    """Create a new survey session"""
    survey_id: str  # Can be UUID or survey name
    respondent_id: Optional[str] = None  # Auto-generated if not provided


class SessionResponse(BaseModel):
    """Survey session response"""
    id: int
    survey_version_id: UUID
    respondent_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    current_question_index: int

    class Config:
        from_attributes = True


class ResponseCreate(BaseModel):
    """Create a new question response"""
    answer: str


class ResponseData(BaseModel):
    """Question response data"""
    id: int
    session_id: int
    question_id: UUID
    respondent_id: str
    answer: str
    answered_at: datetime

    class Config:
        from_attributes = True


class ConversationTurnData(BaseModel):
    """Conversation turn data"""
    id: int
    session_id: int
    respondent_id: str
    speaker: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SURVEY & QUESTION SCHEMAS (for retrieving survey data)
# ============================================================================

class QuestionOptionData(BaseModel):
    """Question option data"""
    id: UUID
    question_id: UUID
    option_text: str
    position: int
    score: Optional[int]

    class Config:
        from_attributes = True


class QuestionData(BaseModel):
    """Question data"""
    id: UUID
    survey_version_id: UUID
    question_type: str
    question_text: str
    position: int
    is_required: bool
    allow_prefer_not_to_answer: bool
    skip_logic: Optional[Dict[str, Any]]
    metadata_json: Optional[Dict[str, Any]]
    options: Optional[List[QuestionOptionData]] = None

    class Config:
        from_attributes = True


class SurveyVersionData(BaseModel):
    """Survey version data"""
    id: UUID
    survey_id: UUID
    version_number: int
    is_current: bool
    created_at: datetime
    questions: Optional[List[QuestionData]] = None

    class Config:
        from_attributes = True


class SurveyData(BaseModel):
    """Survey data"""
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    versions: Optional[List[SurveyVersionData]] = None

    class Config:
        from_attributes = True


# ============================================================================
# ADMIN SCHEMAS (for admin endpoints)
# ============================================================================

class SessionListItem(BaseModel):
    """Session list item for admin"""
    session_id: int
    survey_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    message_count: int


class SessionDetail(BaseModel):
    """Detailed session info for admin"""
    session_id: int
    survey_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    summary: Optional[str]
    key_themes: Optional[List[str]]
    messages: List[Dict[str, Any]]
    llm_calls_count: int
    total_tokens: int
    total_cost_usd: float


# ============================================================================
# SESSION API SCHEMAS (for session endpoints)
# ============================================================================

class SessionStartRequest(BaseModel):
    """Request to start a new session"""
    survey_id: str
    respondent_id: Optional[str] = None
    anonymous_id: Optional[str] = None  # For backwards compatibility


class QuestionOption(BaseModel):
    """Question option for response"""
    option_id: str
    text: str


class QuestionResponse(BaseModel):
    """Question data for response"""
    question_id: UUID
    question_type: str
    question_text: str
    position: int
    options: Optional[List[QuestionOption]] = None


class SessionStartResponse(BaseModel):
    """Response when starting a session"""
    session_id: int
    total_questions: int
    first_question: QuestionResponse
    message_type: str = "survey_question"


class AnswerRequest(BaseModel):
    """Request to submit an answer"""
    question_id: Optional[UUID] = None
    answer_type: str  # 'single_choice', 'free_text', 'follow_up_answer', 'prefer_not_to_answer'
    text: Optional[str] = None
    selected_option_id: Optional[str] = None
    parent_message_id: Optional[UUID] = None


class NextQuestionResponse(BaseModel):
    """Response after submitting an answer"""
    message_type: str  # 'survey_question', 'follow_up_question', 'completed'
    question: Optional[QuestionResponse] = None
    question_text: Optional[str] = None  # For follow-up questions
    parent_message_id: Optional[UUID] = None  # ADD THIS LINE
    summary: Optional[Dict[str, Any]] = None  # For completion


class SessionEndRequest(BaseModel):
    """Request to end a session"""
    reason: str = "user_requested"


class SessionEndResponse(BaseModel):
    """Response when ending a session"""
    message_type: str = "completed"
    summary: Dict[str, Any]