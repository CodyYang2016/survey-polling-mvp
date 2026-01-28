from typing import Dict, Any, List, Optional
import json
from sqlalchemy.orm import Session
from anthropic import APIError, RateLimitError, APITimeoutError


from app.services.llm_client import LLMClient
from app.agents.prompts import (
    FOLLOWUP_AGENT_SYSTEM_PROMPT,
    render_followup_prompt
)
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


class FollowUpAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.max_probes = settings.max_followup_probes
    def _extract_text(self, response: dict) -> str:
        content0 = response["content"][0]
        if isinstance(content0, dict):
            return content0.get("text")
        return content0.text

    
    async def should_ask_followup(
        self,
        question_text: str,
        question_type: str,
        user_answer: str,
        selected_option_text: Optional[str],
        conversation_history: List[Dict[str, str]],
        probe_count: int,
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Determine if a follow-up question should be asked."""
        
        if "prefer not to answer" in user_answer.lower():
            logger.info(f"Skipping follow-up: user opted not to answer")
            return {
                "action": "move_on",
                "followup_question": None,
                "reason": "Respondent opted not to answer",
                "confidence": "high",
                "probe_count": probe_count
            }
        
        if probe_count >= self.max_probes:
            logger.info(f"Skipping follow-up: max probes ({self.max_probes}) reached")
            return {
                "action": "move_on",
                "followup_question": None,
                "reason": "Maximum probes reached",
                "confidence": "medium",
                "probe_count": probe_count
            }
        
        user_message = render_followup_prompt(
            question_text=question_text,
            question_type=question_type,
            user_answer=user_answer,
            selected_option_text=selected_option_text,
            conversation_history=conversation_history,
            probe_count=probe_count
        )
        
        try:
            response = await self.llm_client.complete(
                model="claude-sonnet-4-20250514",
                system=FOLLOWUP_AGENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=150,
                temperature=0.7,
                agent_type="follow_up",
                session_id=session_id,
                db=db
            )
            
            content0 = response["content"][0]

            text = self._extract_text(response)
            result = json.loads(text)

            
            logger.info(
                f"FollowUpAgent decision: action={result['action']}, "
                f"confidence={result['confidence']}, probe_count={result['probe_count']}"
            )
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {
                "action": "move_on",
                "followup_question": None,
                "reason": f"JSON parsing error: {e}",
                "confidence": "low",
                "probe_count": probe_count
            }
        except Exception as e:
            logger.error(f"FollowUpAgent error: {e}")
            # Instead of raising, return a safe fallback
            return {
                "action": "move_on",
                "followup_question": None,
                "reason": "System temporarily unavailable",
                "confidence": "low",
                "probe_count": probe_count
            }