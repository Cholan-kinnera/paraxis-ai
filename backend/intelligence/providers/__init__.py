"""
Model provider abstractions and adapters for Paraxis AI.
"""
from backend.intelligence.providers.base import (
    BaseModelClient,
    ModelResponse,
    ModelChunk,
    UsageMetadata,
)
from backend.intelligence.providers.mock_adapter import MockModelAdapter
from backend.intelligence.providers.gemini_adapter import GoogleGeminiAdapter
from backend.intelligence.providers.openai_adapter import OpenAIAdapter
from backend.intelligence.providers.factory import get_model_client

__all__ = [
    "BaseModelClient",
    "ModelResponse",
    "ModelChunk",
    "UsageMetadata",
    "MockModelAdapter",
    "GoogleGeminiAdapter",
    "OpenAIAdapter",
    "get_model_client",
]
