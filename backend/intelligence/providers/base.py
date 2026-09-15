"""
Unified AI Model Gateway and Provider Abstraction for Paraxis AI.
Adheres to ADR-008.
"""
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, List, Dict, Any, AsyncIterator
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class UsageMetadata(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelResponse(BaseModel):
    content: str = ""
    parsed: Optional[Any] = None
    usage: UsageMetadata = Field(default_factory=UsageMetadata)
    model_name: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)


class ModelChunk(BaseModel):
    text: str = ""
    is_final: bool = False


class BaseModelClient(ABC):
    """
    Abstract interface for AI model providers.
    Supports structured Pydantic outputs, token streaming, and vector embeddings.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> ModelResponse:
        """
        Generates completion for a prompt.
        If `schema` is provided, guarantees output conforms to the Pydantic model.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[ModelChunk]:
        """Streams completion tokens incrementally."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for input texts."""
        pass
