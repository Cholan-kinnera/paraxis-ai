"""
Factory for resolving and instantiating AI model provider clients.
Adheres to ADR-008.
"""
import logging
from typing import Optional
from backend.intelligence.config import settings
from backend.intelligence.providers.base import BaseModelClient
from backend.intelligence.providers.mock_adapter import MockModelAdapter
from backend.intelligence.providers.gemini_adapter import GoogleGeminiAdapter
from backend.intelligence.providers.openai_adapter import OpenAIAdapter

logger = logging.getLogger("paraxis.providers.factory")

_default_client: Optional[BaseModelClient] = None


def get_model_client(provider_name: Optional[str] = None) -> BaseModelClient:
    """
    Returns an instantiated AI model client based on configuration or explicit parameter.
    Falls back gracefully to MockModelAdapter if required API keys are missing.
    """
    global _default_client

    target_provider = (provider_name or settings.AI_DEFAULT_PROVIDER or "mock").lower()

    if target_provider == "google":
        if settings.GOOGLE_API_KEY:
            return GoogleGeminiAdapter(api_key=settings.GOOGLE_API_KEY)
        logger.info("GOOGLE_API_KEY not configured. Falling back to MockModelAdapter.")
        return MockModelAdapter()

    elif target_provider == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
        logger.info("OPENAI_API_KEY not configured. Falling back to MockModelAdapter.")
        return MockModelAdapter()

    elif target_provider == "mock":
        return MockModelAdapter()

    else:
        logger.warning(f"Unknown provider '{target_provider}'. Defaulting to MockModelAdapter.")
        return MockModelAdapter()
