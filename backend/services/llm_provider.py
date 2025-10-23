"""
LLM Provider Abstraction

Supports multiple LLM providers with automatic fallback:
- AI/ML API (200+ models, generous free tier)
- Google Gemini (free tier)
- OpenAI (paid)

Priority: AI/ML API > Gemini > OpenAI
"""

import os
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Multi-provider LLM client with automatic fallback
    """

    def __init__(self):
        """Initialize LLM providers in priority order"""
        self.providers = []

        # Priority 1: AI/ML API (best free tier, 200+ models)
        aimlapi_key = os.getenv("AIMLAPI_KEY")
        if aimlapi_key:
            try:
                self.aimlapi_client = OpenAI(
                    api_key=aimlapi_key,
                    base_url="https://api.aimlapi.com/v1"
                )
                self.providers.append("aimlapi")
                logger.info("✅ AI/ML API initialized")
            except Exception as e:
                logger.warning(f"⚠️ AI/ML API init failed: {e}")

        # Priority 2: Gemini (free tier)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_api_key)
                self.gemini_client = genai
                self.providers.append("gemini")
                logger.info("✅ Gemini initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini init failed: {e}")

        # Priority 3: OpenAI (paid)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                self.providers.append("openai")
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI init failed: {e}")

        if not self.providers:
            logger.error("❌ No LLM providers available!")

        logger.info(f"🤖 Active providers: {', '.join(self.providers)}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate chat completion with automatic provider fallback

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (auto-selects best for provider)
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            Generated text response
        """

        # Try each provider in order
        for provider in self.providers:
            try:
                if provider == "aimlapi":
                    return await self._aimlapi_chat(messages, model, temperature, max_tokens)
                elif provider == "gemini":
                    return await self._gemini_chat(messages, model, temperature, max_tokens)
                elif provider == "openai":
                    return await self._openai_chat(messages, model, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"⚠️ {provider} failed: {e}, trying next provider...")
                continue

        raise Exception("All LLM providers failed")

    async def _aimlapi_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """AI/ML API chat completion"""
        # Default to GPT-4o (best free model on AI/ML API)
        if not model:
            model = "gpt-4o"

        logger.info(f"🤖 Using AI/ML API with {model}")

        response = self.aimlapi_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    async def _gemini_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Gemini chat completion"""
        # Default to Gemini 2.0 Flash
        if not model:
            model = "gemini-2.0-flash-exp"

        logger.info(f"🤖 Using Gemini with {model}")

        # Convert messages to Gemini format
        gemini_model = self.gemini_client.GenerativeModel(model)

        # Combine messages into single prompt
        prompt = "\n\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])

        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )

        return response.text

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI chat completion"""
        # Default to GPT-4o-mini (cheapest)
        if not model:
            model = "gpt-4o-mini"

        logger.info(f"🤖 Using OpenAI with {model}")

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content


# Global instance
llm_provider = None


def get_llm_provider() -> LLMProvider:
    """Get or create global LLM provider instance"""
    global llm_provider
    if llm_provider is None:
        llm_provider = LLMProvider()
    return llm_provider
