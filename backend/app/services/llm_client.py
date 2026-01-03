from typing import Dict, Any, List, Optional
import time
from anthropic import Anthropic
from app.config import settings
from app.utils.logger import setup_logger
from app.models import ModelCall
from sqlalchemy.orm import Session

logger = setup_logger(__name__)


class LLMClient:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.pricing = {
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "claude-haiku-3-5-20250514": {"input": 0.80, "output": 4.00},
        }
    
    async def complete(
        self,
        model: str,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        agent_type: str = "unknown",
        session_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Call Anthropic API and log to database."""
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=model,
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
            
            if db:
                model_call = ModelCall(
                    session_id=session_id,
                    agent_type=agent_type,
                    model_name=model,
                    provider="anthropic",
                    prompt_text=messages[0]["content"] if messages else "",
                    system_prompt=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_text=response.content[0].text,
                    finish_reason=response.stop_reason,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    cost_usd=cost_usd
                )
                db.add(model_call)
                db.flush()
            
            logger.info(
                f"LLM call completed: model={model}, agent={agent_type}, "
                f"tokens={input_tokens}/{output_tokens}, latency={latency_ms}ms, "
                f"cost=${cost_usd:.6f}"
            )
            
            return {
                "content": response.content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                },
                "latency_ms": latency_ms,
                "cost_usd": cost_usd
            }
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        if model not in self.pricing:
            return 0.0
        
        pricing = self.pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost