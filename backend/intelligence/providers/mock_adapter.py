"""
Deterministic Mock AI Provider Adapter for Testing and CI.
Allows offline test execution without requiring third-party API keys or incurring costs.
"""
import hashlib
import json
from typing import Optional, Type, TypeVar, List, AsyncIterator
from pydantic import BaseModel
from backend.intelligence.providers.base import (
    BaseModelClient,
    ModelResponse,
    ModelChunk,
    UsageMetadata,
)

T = TypeVar("T", bound=BaseModel)


class MockModelAdapter(BaseModelClient):
    """
    Deterministic mock AI provider for CI test runs and offline development.
    Parses prompt keywords to synthesize realistic structured operational outputs.
    """

    def __init__(self, model_name: str = "mock-paraxis-v1"):
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> ModelResponse:
        content = self._generate_mock_content(prompt, schema)
        parsed = None

        if schema:
            try:
                if isinstance(content, str):
                    parsed_dict = json.loads(content)
                    parsed = schema.model_validate(parsed_dict)
                elif isinstance(content, dict):
                    parsed = schema.model_validate(content)
                    content = json.dumps(content)
            except Exception:
                # Construct default instance of the Pydantic schema
                parsed = self._synthesize_schema_instance(schema, prompt)
                content = parsed.model_dump_json()

        usage = UsageMetadata(
            prompt_tokens=len(prompt.split()) * 2,
            completion_tokens=len(content.split()) * 2,
            total_tokens=(len(prompt.split()) + len(content.split())) * 2,
        )

        return ModelResponse(
            content=content,
            parsed=parsed,
            usage=usage,
            model_name=self.model_name,
            raw={"provider": "mock", "prompt_snippet": prompt[:80]},
        )

    async def stream(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[ModelChunk]:
        content = self._generate_mock_content(prompt, schema)
        if not isinstance(content, str):
            content = json.dumps(content)

        words = content.split(" ")
        for i, word in enumerate(words):
            is_final = i == len(words) - 1
            chunk_text = word if is_final else word + " "
            yield ModelChunk(text=chunk_text, is_final=is_final)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        import math
        from backend.intelligence.providers.base import validate_embeddings, PARAXIS_EMBEDDING_DIMENSION

        embeddings = []
        for text in texts:
            # Deterministic pseudo-embedding using SHA-256 seed hashing across 768 dimensions
            vec = []
            for i in range(24):  # 24 * 32 = 768 dimensions
                h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).digest()
                vec.extend([(b / 255.0) * 2.0 - 1.0 for b in h])
            # Normalize to unit length
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            norm_vec = [round(x / norm, 6) for x in vec[:PARAXIS_EMBEDDING_DIMENSION]]
            embeddings.append(norm_vec)
        return validate_embeddings(embeddings)


    def _generate_mock_content(self, prompt: str, schema: Optional[Type[T]]) -> str:
        prompt_lower = prompt.lower()

        # Entity Extraction schema handling
        if schema and schema.__name__ == "EntityResolution":
            category = "IT_NETWORK"
            if any(k in prompt_lower for k in ["leak", "pipe", "water", "plumb"]):
                category = "PLUMBING"
            elif any(k in prompt_lower for k in ["ac", "hvac", "cool", "warm air", "chiller"]):
                category = "HVAC"
            elif any(k in prompt_lower for k in ["light", "power", "switch", "spark", "electric"]):
                category = "ELECTRICAL"
            elif any(k in prompt_lower for k in ["fire", "hazard", "gas", "smoke", "danger", "emergency"]):
                category = "SAFETY"

            building = "Engineering Block" if "engineering" in prompt_lower or "seb" in prompt_lower else "Science Block"
            room = "204" if "204" in prompt_lower else ("101" if "101" in prompt_lower else "General Facility")
            asset = "Wi-Fi AP-204" if "ap" in prompt_lower or "wifi" in prompt_lower or "wi-fi" in prompt_lower else "Core Facility Asset"

            return json.dumps({
                "category": category,
                "building_id": None,
                "building_name": building,
                "room_id": None,
                "room_number": room,
                "asset_id": None,
                "asset_name": asset,
                "confidence": 0.96,
            })

        # Action Proposal schema handling
        if schema and schema.__name__ == "ActionProposal":
            is_critical = any(k in prompt_lower for k in ["fire", "gas", "smoke", "hazard", "critical", "danger"])
            is_high_cost = any(k in prompt_lower for k in ["replace core switch", "transformer replacement", "expensive", "high cost"])

            estimated_cost = 1200.0 if is_high_cost else (50.0 if not is_critical else 200.0)
            priority = "CRITICAL" if is_critical else ("HIGH" if "high" in prompt_lower or "ap" in prompt_lower else "MEDIUM")

            return json.dumps({
                "action_type": "CREATE_TASK",
                "department_id": "dept-it",
                "priority": priority,
                "assigned_user_id": None,
                "estimated_cost": estimated_cost,
                "action_justification": f"Operational remediation dispatched for {priority} severity incident.",
            })

        # Generic default mock response
        return "Paraxis AI Operational Intelligence: Incident processed and categorized successfully."

    def _synthesize_schema_instance(self, schema: Type[T], prompt: str) -> T:
        fields = {}
        for name, field in schema.model_fields.items():
            if field.annotation is str or field.annotation == Optional[str]:
                fields[name] = f"mock_{name}"
            elif field.annotation is int or field.annotation == Optional[int]:
                fields[name] = 1
            elif field.annotation is float or field.annotation == Optional[float]:
                fields[name] = 1.0
            elif field.annotation is bool or field.annotation == Optional[bool]:
                fields[name] = True
            elif field.annotation is list or getattr(field.annotation, "__origin__", None) is list:
                fields[name] = []
            elif field.annotation is dict or getattr(field.annotation, "__origin__", None) is dict:
                fields[name] = {}
            else:
                fields[name] = None
        return schema.model_validate(fields)
