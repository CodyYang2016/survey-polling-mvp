from typing import Dict, Any, List, Optional
import time
import asyncio
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
from app.config import settings
from app.utils.logger import setup_logger
from app.models import ModelCall
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = setup_logger(__name__)


class LLMClient:
    def __init__(self):
        self.client = Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.api_timeout_seconds
        )
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
        db: Optional[Session] = None,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """Call Anthropic API and log to database."""
        if max_retries is None:
            max_retries = settings.api_max_retries
            
        start_time = time.time()
        last_exception = None
        
        # Check session cost budget before making call
        if db and session_id:
            total_cost = db.query(func.sum(ModelCall.cost_usd))\
                .filter(ModelCall.session_id == session_id)\
                .scalar() or 0.0
            
            if total_cost > settings.max_cost_per_session_usd:
                logger.error(f"Session {session_id} exceeded cost limit: ${total_cost:.4f}")
                raise Exception(f"Session cost limit exceeded: ${total_cost:.4f}")
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=model,
                    system=system,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # SUCCESS - Process the response
                latency_ms = int((time.time() - start_time) * 1000)
                
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                # Around line 50-60
                cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
                cost_usd_cents = int(cost_usd * 100)  # ADD THIS - convert to cents

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
                        cost_usd=cost_usd_cents  # CHANGED - store cents not dollars
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
                
            except RateLimitError as e:
                last_exception = e
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
                
            except APITimeoutError as e:
                last_exception = e
                wait_time = min(2 ** attempt, 30)
                logger.warning(f"API timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
                
            except APIError as e:
                # For other API errors, check if they're retryable
                if e.status_code >= 500:  # Server errors are retryable
                    last_exception = e
                    wait_time = min(2 ** attempt, 30)
                    logger.warning(f"API error {e.status_code}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Client errors (400, 401, 403) should not be retried
                    logger.error(f"LLM call failed with non-retryable error: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"LLM call failed with unexpected error: {e}")
                raise
        
        # If we've exhausted all retries
        logger.error(f"LLM call failed after {max_retries} attempts: {last_exception}")
        raise last_exception
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        if model not in self.pricing:
            logger.warning(f"Unknown model '{model}', cost tracking unavailable")
            return 0.0
        
        pricing = self.pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost