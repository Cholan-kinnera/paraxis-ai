# Paraxis AI — Intelligence Platform (`backend/intelligence`)

The cognitive reasoning, agentic workflow, and operational RAG engine for Paraxis AI, built with **FastAPI** and **LangGraph**.

## Responsibilities
- **Agent Orchestration**: Stateful LangGraph graphs executing the 13-node incident workflow.
- **Model Gateway**: Pluggable provider adapters (Google Gemini, OpenAI, Anthropic, Mock).
- **Operational RAG**: Semantic similarity matching with PostgreSQL `pgvector`.
- **Typed Tool Registry**: Validates inputs/outputs for all 11 registered operational tools.
- **Deterministic Policy Bridge**: Gating proposed actions before physical execution.
- **Real-time Telemetry**: Streaming step-by-step agent decisions to clients via Server-Sent Events (SSE).

## Booting Locally
```bash
# Ensure virtual environment is active
pip install -r requirements.txt
uvicorn backend.intelligence.main:app --host 0.0.0.0 --port 8001 --reload
```
Health probe available at: `http://localhost:8001/api/v1/health`
