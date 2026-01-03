import json
import random
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.utils.logger import setup_logger
from app.models import ModelCall

logger = setup_logger(__name__)


class MockLLMClient:
    """
    Mock LLM client for testing without API costs.
    Simulates Anthropic Claude responses with realistic behavior.
    """
    
    def __init__(self):
        self.pricing = {
            "claude-sonnet-4-20250514": {"input": 0.00, "output": 0.00},
            "claude-haiku-3-5-20250514": {"input": 0.00, "output": 0.00},
        }
        logger.warning("="*60)
        logger.warning("🎭 MOCK LLM MODE ENABLED")
        logger.warning("No real API calls will be made - responses are simulated")
        logger.warning("Cost: $0.00 per session")
        logger.warning("="*60)
    
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
        """
        Mock LLM completion - returns realistic predefined responses.
        Simulates latency and token usage.
        """
        
        # Simulate API latency (50-150ms)
        start_time = time.time()
        await self._simulate_latency()
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"🎭 Mock LLM call: agent={agent_type}, model={model}")
        
        # Generate mock response based on agent type
        if agent_type == "follow_up":
            response_text = self._mock_followup_response(messages)
            input_tokens = self._estimate_tokens(messages[0]["content"]) if messages else 200
            output_tokens = self._estimate_tokens(response_text)
        elif agent_type == "summary":
            response_text = self._mock_summary_response(messages)
            input_tokens = self._estimate_tokens(messages[0]["content"]) if messages else 300
            output_tokens = self._estimate_tokens(response_text)
        else:
            response_text = '{"mock": "response"}'
            input_tokens = 100
            output_tokens = 50
        
        # Log to database (same as real LLM)
        if db:
            model_call = ModelCall(
                session_id=session_id,
                agent_type=agent_type,
                model_name=model,
                provider="mock",
                prompt_text=messages[0]["content"] if messages else "",
                system_prompt=system,
                temperature=temperature,
                max_tokens=max_tokens,
                response_text=response_text,
                finish_reason="stop",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=0.0
            )
            db.add(model_call)
            db.flush()
        
        logger.info(
            f"🎭 Mock response: tokens={input_tokens}/{output_tokens}, "
            f"latency={latency_ms}ms, cost=$0.00"
        )
        
        return {
            "content": [{"text": response_text}],
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            },
            "latency_ms": latency_ms,
            "cost_usd": 0.0
        }
    
    async def _simulate_latency(self):
        """Simulate realistic API latency."""
        import asyncio
        latency = random.uniform(0.05, 0.15)  # 50-150ms
        await asyncio.sleep(latency)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return max(10, len(text) // 4)
    
    def _mock_followup_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate mock follow-up agent response.
        Intelligently decides whether to ask follow-up based on answer length.
        """
        
        user_message = messages[0]["content"] if messages else ""
        
        # Check if user gave a short answer (likely needs follow-up)
        answer_length = len(user_message.split())
        probe_count = user_message.count("PROBE COUNT:")
        
        # Extract probe count if present
        current_probe = 0
        if "PROBE COUNT:" in user_message:
            try:
                probe_count_line = [line for line in user_message.split("\n") if "PROBE COUNT:" in line][0]
                current_probe = int(probe_count_line.split("/")[0].split(":")[-1].strip())
            except:
                current_probe = 0
        
        # Decision logic
        should_followup = False
        confidence = "high"
        
        if current_probe >= 3:
            # Max probes reached
            should_followup = False
            confidence = "high"
            reason = "Maximum probes reached"
        elif answer_length < 10:
            # Very short answer - likely needs follow-up
            should_followup = True
            confidence = "low"
            reason = "Answer appears surface-level, seeking deeper understanding"
        elif answer_length < 30:
            # Medium answer - 70% chance of follow-up
            should_followup = random.random() < 0.7
            confidence = "medium"
            reason = "Seeking clarification on key points mentioned" if should_followup else "Sufficient detail provided"
        else:
            # Long answer - 30% chance of follow-up
            should_followup = random.random() < 0.3
            confidence = "high"
            reason = "Exploring specific aspect mentioned" if should_followup else "Comprehensive response with clear motivation and preference"
        
        if should_followup:
            # Variety of neutral follow-up questions
            follow_up_questions = [
                "What factors led you to that perspective?",
                "Can you tell me more about what concerns you most about this?",
                "What would an ideal solution look like from your point of view?",
                "How do you think this affects people in your community?",
                "What experiences have shaped your thinking on this?",
                "Are there specific aspects of this that you find most important?",
                "What trade-offs do you see with different approaches?",
                "How do you balance the different considerations here?",
                "What would need to change for you to feel differently about this?",
                "Can you walk me through your reasoning on this?"
            ]
            
            # Select appropriate question based on context
            if "economic" in user_message.lower() or "cost" in user_message.lower():
                question = "How do economic considerations factor into your view on this?"
            elif "family" in user_message.lower() or "personal" in user_message.lower():
                question = "How have personal or family experiences influenced your perspective?"
            elif "security" in user_message.lower() or "safety" in user_message.lower():
                question = "What specific security or safety concerns are most important to you?"
            else:
                question = random.choice(follow_up_questions)
            
            return json.dumps({
                "action": "ask_followup",
                "followup_question": question,
                "reason": reason,
                "confidence": confidence,
                "probe_count": current_probe + 1
            })
        else:
            return json.dumps({
                "action": "move_on",
                "followup_question": None,
                "reason": reason,
                "confidence": confidence,
                "probe_count": current_probe
            })
    
    def _mock_summary_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate mock summary agent response.
        Creates contextually appropriate summaries.
        """
        
        user_message = messages[0]["content"] if messages else ""
        
        # Extract key themes from the message
        themes = []
        if "economic" in user_message.lower() or "cost" in user_message.lower() or "money" in user_message.lower():
            themes.append("economic concerns")
        if "family" in user_message.lower() or "personal" in user_message.lower():
            themes.append("personal values")
        if "security" in user_message.lower() or "safety" in user_message.lower():
            themes.append("security priorities")
        if "community" in user_message.lower() or "people" in user_message.lower():
            themes.append("community impact")
        if "positive" in user_message.lower() or "support" in user_message.lower():
            themes.append("supportive stance")
        if "negative" in user_message.lower() or "concern" in user_message.lower() or "worry" in user_message.lower():
            themes.append("critical perspective")
        if "balance" in user_message.lower() or "both" in user_message.lower():
            themes.append("balanced viewpoint")
        
        # Default themes if none detected
        if not themes:
            themes = ["general perspective", "personal reasoning"]
        
        # Generate contextual summary
        sentiment_words = ["expressed", "indicated", "stated", "articulated", "conveyed"]
        sentiment = random.choice(sentiment_words)
        
        # Template-based summary generation
        templates = [
            f"Respondent {sentiment} concerns rooted in {themes[0] if themes else 'personal experience'}, emphasizing practical considerations.",
            f"Participant demonstrated thoughtful perspective on the issue, citing {themes[0] if themes else 'multiple factors'} as primary influence.",
            f"Individual articulated views shaped by {themes[0] if themes else 'personal values'} with emphasis on real-world implications.",
            f"Response reflected nuanced understanding, balancing {themes[0] if themes else 'different considerations'} in their reasoning.",
        ]
        
        summary = random.choice(templates)
        
        # Limit themes to 2-3 most relevant
        themes = themes[:3] if len(themes) > 3 else themes
        if not themes:
            themes = ["personal perspective"]
        
        return json.dumps({
            "summary": summary,
            "key_themes": themes
        })
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Mock cost calculation - always returns 0."""
        return 0.0