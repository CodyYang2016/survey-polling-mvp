from typing import Dict, Any, List
import json
from sqlalchemy.orm import Session
from anthropic import APIError, RateLimitError, APITimeoutError


from app.services.llm_client import LLMClient
from app.agents.prompts import (
    SUMMARY_AGENT_SYSTEM_PROMPT,
    render_summary_prompt
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SummaryAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def update_summary(
        self,
        current_summary: str,
        question_text: str,
        user_answer: str,
        followup_questions: List[str],
        followup_answers: List[str],
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Update the running session summary."""
        
        user_message = render_summary_prompt(
            current_summary=current_summary,
            question_text=question_text,
            user_answer=user_answer,
            followup_questions=followup_questions,
            followup_answers=followup_answers
        )
        
        try:
            response = await self.llm_client.complete(
                model="claude-3-haiku-20240307",
                system=SUMMARY_AGENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=200,
                temperature=0.5,
                agent_type="summary",
                session_id=session_id,
                db=db
            )
            
            result = json.loads(response["content"][0].text)
            
            logger.info(f"SummaryAgent updated: themes={result.get('key_themes', [])}")
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in SummaryAgent: {e}")
            return {
                "summary": current_summary,
                "key_themes": []
            }
        except Exception as e:
            logger.error(f"SummaryAgent error: {e}")
            return {
                "summary": current_summary,
                "key_themes": []
                }
        except APIError as e:
            logger.error(f"API error in SummaryAgent: {e.status_code} - {e.message}")
            return {
                "summary": current_summary,
                "key_themes": [],
                "error": "temporary_issue"  # Frontend can show a gentle message
            }