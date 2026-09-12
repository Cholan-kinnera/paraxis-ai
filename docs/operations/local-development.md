# Local Development Guide — Paraxis AI

> **Purpose**: Developer setup, environment configuration, container lifecycle, and debugging guides.

---

## 1. Prerequisites
- Python 3.12+ (Host system verified: `3.14.6`)
- Node.js 20+ (Host system verified: `v26.4.0`)
- Docker & Docker Compose (`v5.3+`)

---

## 2. Step-by-Step Setup

```bash
# 1. Clone repository & enter directory
git clone https://github.com/Cholan-kinnera/paraxis-ai.git
cd paraxis-ai

# 2. Copy environment variables template
make setup

# 3. Start local PostgreSQL (pgvector) and Redis
make docker-up

# 4. Verify running database & extension status
docker compose ps
docker compose exec postgres psql -U paraxis_user -d paraxis_dev -c "\dx"

# 5. Run foundation verification
make verify-foundation
```

---

## 3. Running Services Locally

- **Core Backend (Django)**:
  ```bash
  cd backend/core
  python manage.py runserver 0.0.0.0:8000
  ```
- **Intelligence Backend (FastAPI)**:
  ```bash
  cd backend/intelligence
  uvicorn main:app --port 8001 --reload
  ```
- **Web Frontend (Next.js)**:
  ```bash
  cd frontend
  npm run dev
  ```
