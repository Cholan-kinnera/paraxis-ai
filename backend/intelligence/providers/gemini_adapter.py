"""
Google Gemini Provider Adapter for Paraxis AI.
Leverages Gemini models for multimodal and structured operational reasoning.
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

logger = logging.getLogger("paraxis.providers.gemini")
T = TypeVar("T", bound=BaseModel)


class GoogleGeminiAdapter(BaseModelClient):
    """
    Adapter for Google Gemini API models (e.g. gemini-1.5-flash, gemini-2.0-flash).
    Supports structured JSON schema outputs and embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
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
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Context:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will operate within these operational constraints."}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        generation_config = {
            "temperature": temperature,
        }

        if schema:
            generation_config["response_mime_type"] = "application/json"
            generation_config["response_schema"] = schema.model_json_schema()

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        raw_text = ""
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            raw_text = "".join(p.get("text", "") for p in parts)

        parsed = None
        if schema and raw_text:
            try:
                parsed_json = json.loads(raw_text)
                parsed = schema.model_validate(parsed_json)
            except Exception as exc:
                logger.warning(f"Gemini structured output parsing failed: {exc}")

        usage_dict = data.get("usageMetadata", {})
        usage = UsageMetadata(
            prompt_tokens=usage_dict.get("promptTokenCount", 0),
            completion_tokens=usage_dict.get("candidatesTokenCount", 0),
            total_tokens=usage_dict.get("totalTokenCount", 0),
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
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload = {"contents": contents, "generationConfig": {"temperature": temperature}}

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_json = json.loads(line[6:])
                        parts = chunk_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        if text:
                            yield ModelChunk(text=text, is_final=False)
        yield ModelChunk(text="", is_final=True)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        from backend.intelligence.providers.base import validate_embeddings

        url = f"{self.base_url}/models/text-embedding-004:batchEmbedContents?key={self.api_key}"
        requests = [{"model": "models/text-embedding-004", "content": {"parts": [{"text": t}]}} for t in texts]
        payload = {"requests": requests}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        embeddings = [item["values"] for item in data.get("embeddings", [])]
        return validate_embeddings(embeddings)

