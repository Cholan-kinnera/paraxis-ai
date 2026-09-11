# ADR-008: Pluggable AI Model Gateway and Provider Abstraction

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI relies on Large Language Models (LLMs) for natural-language intent understanding, entity extraction, operational reasoning, and synthesis. The AI market evolves rapidly, and relying on a single closed proprietary API creates vendor lock-in, uptime vulnerability, and enterprise procurement blockers.

## Problem
Hardcoding proprietary SDK calls (e.g., direct OpenAI or Google client invocations scattered across node logic) makes swapping models difficult, hinders local offline testing with mock or local models (Ollama/vLLM), and prevents cost-based dynamic routing.

## Decision
Implement a **unified Model Gateway abstraction** within `apps/intelligence`:
1. **Interface Contract**: A unified `BaseModelClient` interface specifying:
   - `generate(prompt, schema=None, temperature=0.1) -> ModelResponse`
   - `stream(prompt, schema=None) -> AsyncIterator[ModelChunk]`
   - `embed(texts: List[str]) -> List[List[float]]`
2. **Pluggable Adapters**:
   - `GoogleGeminiAdapter` (Primary recommended: fast, cost-effective multimodal).
   - `OpenAIAdapter` (Alternative fallback).
   - `AnthropicAdapter` (Alternative reasoning engine).
   - `MockModelAdapter` (Deterministic fixture for unit testing and CI without API keys).
3. **Structured Outputs**: Use Pydantic v2 schemas across all adapters to enforce strictly validated JSON outputs.

## Alternatives Considered
1. **Direct SDK usage in each agent node**:
   - *Rejected*: Creates tight coupling and makes offline unit testing impossible.
2. **Third-party Heavy AI Gateways (Portkey, LiteLLM proxy)**:
   - *Deferred*: Adds extra proxy infrastructure and potential single point of failure; lightweight internal adapter pattern is sufficient and easily maintained.

## Consequences
- **Positive**:
  - Tests run deterministically in CI without hitting paid external APIs.
  - Effortless switching between models based on latency and cost.
- **Negative**:
  - Requires maintaining normalization logic across provider response quirks.

## Security Implications
API keys are loaded via environment variables and never logged. Prompts and completions are sanitized to avoid leaking sensitive credentials.
