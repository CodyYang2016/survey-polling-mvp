from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime


class SurveyInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    version: str
    metadata: Optional[Dict[str, Any]] = None


class QuestionOption(BaseModel):
    id: str
    text: str
    score: Optional[int] = None
    position: int


class QuestionDefinition(BaseModel):
    id: str
    type: str
    prompt: str
    required: bool = True
    allow_prefer_not_to_answer: bool = True
    options: Optional[List[QuestionOption]] = None
    skip_logic: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class SurveyDefinition(BaseModel):
    survey: SurveyInfo
    questions: List[QuestionDefinition]


class SessionStartRequest(BaseModel):
    survey_id: str
    anonymous_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class QuestionResponse(BaseModel):
    question_id: UUID4
    question_type: str
    question_text: str
    options: Optional[List[Dict[str, Any]]] = None
    position: int
    is_required: bool
    allow_prefer_not_to_answer: bool


class SessionStartResponse(BaseModel):
    session_id: UUID4
    survey_name: str
    total_questions: int
    first_question: QuestionResponse


class AnswerRequest(BaseModel):
    question_id: Optional[UUID4] = None
    answer_type: str
    text: Optional[str] = None
    selected_option_id: Optional[UUID4] = None
    parent_message_id: Optional[UUID4] = None


class ProgressInfo(BaseModel):
    current_position: int
    total_questions: int
    is_follow_up_pending: bool


class NextQuestionResponse(BaseModel):
    message_type: str
    question: Optional[QuestionResponse] = None
    question_text: Optional[str] = None
    is_follow_up: bool = False
    reasoning: Optional[str] = None
    progress: ProgressInfo


class SessionEndRequest(BaseModel):
    reason: str = "user_requested"


class SessionEndResponse(BaseModel):
    status: str
    message: str
    summary: Dict[str, Any]


class SessionListItem(BaseModel):
    session_id: UUID4
    survey_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    message_count: int


class SessionDetail(BaseModel):
    session_id: UUID4
    survey_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    summary: Optional[str]
    key_themes: Optional[List[str]]
    messages: List[Dict[str, Any]]
    llm_calls_count: int  # Changed from model_calls_count
    total_tokens: int
    total_cost_usd: float