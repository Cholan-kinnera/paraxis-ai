"""
OpenAI Provider Adapter for Paraxis AI.
"""
import json
import logging
from typing import Optional, Type, TypeVar, List, AsyncIterator
import httpx
from pydantic import BaseModel
from backend.intelligence.providers.base import (
    BaseModelClient,
    ModelResponse,
    ModelChunk,
    UsageMetadata,
)

logger = logging.getLogger("paraxis.providers.openai")
T = TypeVar("T", bound=BaseModel)


class OpenAIAdapter(BaseModelClient):
    """
    Adapter for OpenAI API models (e.g. gpt-4o, gpt-4o-mini).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> ModelResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        raw_text = choices[0]["message"]["content"] if choices else ""

        parsed = None
        if schema and raw_text:
            try:
                parsed_json = json.loads(raw_text)
                parsed = schema.model_validate(parsed_json)
            except Exception as exc:
                logger.warning(f"OpenAI structured output parsing failed: {exc}")

        usage_dict = data.get("usage", {})
        usage = UsageMetadata(
            prompt_tokens=usage_dict.get("prompt_tokens", 0),
            completion_tokens=usage_dict.get("completion_tokens", 0),
            total_tokens=usage_dict.get("total_tokens", 0),
        )

        return ModelResponse(
            content=raw_text,
            parsed=parsed,
            usage=usage,
            model_name=self.model,
            raw=data,
        )

    async def stream(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[ModelChunk]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "user", "content": prompt}]
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "stream": True}

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and not line.strip().endswith("[DONE]"):
                        chunk_json = json.loads(line[6:])
                        choices = chunk_json.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {}).get("content", "")
                            if delta:
                                yield ModelChunk(text=delta, is_final=False)
        yield ModelChunk(text="", is_final=True)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "text-embedding-3-small", "input": texts}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return [item["embedding"] for item in data.get("data", [])]
