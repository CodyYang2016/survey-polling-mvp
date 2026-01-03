from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Survey, SurveyVersion, Question, QuestionOption
from app.schemas import SurveyDefinition
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SurveyService:
    def __init__(self, db: Session):
        self.db = db
    
    def ingest_survey(self, survey_def: SurveyDefinition) -> UUID:
        """Ingest a survey definition and persist to database."""
        try:
            survey = self.db.query(Survey).filter(
                Survey.name == survey_def.survey.name
            ).first()
            
            if not survey:
                survey = Survey(
                    id=uuid4(),
                    name=survey_def.survey.name,
                    description=survey_def.survey.description,
                    is_active=True
                )
                self.db.add(survey)
                self.db.flush()
                logger.info(f"Created new survey: {survey.name}")
            
            max_version = self.db.query(
                func.max(SurveyVersion.version_number)
            ).filter(
                SurveyVersion.survey_id == survey.id
            ).scalar() or 0
            
            survey_version = SurveyVersion(
                id=uuid4(),
                survey_id=survey.id,
                version_number=max_version + 1,
                is_current=True,
                json_definition=survey_def.dict()
            )
            self.db.add(survey_version)
            self.db.flush()
            
            self.db.query(SurveyVersion).filter(
                SurveyVersion.survey_id == survey.id,
                SurveyVersion.id != survey_version.id
            ).update({"is_current": False})
            
            for idx, q_def in enumerate(survey_def.questions):
                question = Question(
                    id=uuid4(),
                    survey_version_id=survey_version.id,
                    question_type=q_def.type,
                    question_text=q_def.prompt,
                    position=idx,
                    is_required=q_def.required,
                    allow_prefer_not_to_answer=q_def.allow_prefer_not_to_answer,
                    skip_logic=q_def.skip_logic.dict() if q_def.skip_logic else None,
                    metadata_json=q_def.metadata
                )
                self.db.add(question)
                self.db.flush()
                
                if q_def.options:
                    for opt_def in q_def.options:
                        option = QuestionOption(
                            id=uuid4(),
                            question_id=question.id,
                            option_text=opt_def.text,
                            position=opt_def.position,
                            score=opt_def.score
                        )
                        self.db.add(option)
            
            self.db.commit()
            logger.info(
                f"Survey ingested: {survey.name} v{survey_version.version_number} "
                f"with {len(survey_def.questions)} questions"
            )
            
            return survey_version.id
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Survey ingestion failed: {e}")
            raise
    
    def get_current_survey_version(self, survey_id: str) -> SurveyVersion:
        """Get current version of a survey by UUID or by name."""
        q = self.db.query(Survey)

        try:
            survey_uuid = UUID(str(survey_id))
            survey = q.filter(Survey.id == survey_uuid).first()
        except ValueError:
            survey = q.filter(Survey.name == survey_id).first()

        if not survey:
            raise ValueError(f"Survey {survey_id} not found")

        survey_version = self.db.query(SurveyVersion).filter(
            SurveyVersion.survey_id == survey.id,
            SurveyVersion.is_current.is_(True),
        ).first()

        if not survey_version:
            raise ValueError(f"No active version for survey {survey_id}")

        return survey_version