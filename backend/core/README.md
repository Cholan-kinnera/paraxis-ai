# Paraxis AI — Core Platform (`backend/core`)

The sovereign domain authority and persistent platform for Paraxis AI, built with **Django 5+** and **Django REST Framework**.

## Responsibilities
- **Canonical Business State**: Organizations, Campuses, Users, Roles, Permissions, Incidents, Tasks, SLAs, Approvals.
- **Relational Persistence**: PostgreSQL 16 schema and migrations.
- **Tenancy Enforcement**: Cryptographic JWT validation and automatic `campus_id` ORM query filtering.
- **Audit Logging**: Append-only immutable record of all operational state mutations.
- **Transactional APIs**: `/api/v1/` for external clients and `/internal/v1/` for internal service requests.

## Booting Locally
```bash
# Ensure virtual environment is active
pip install -r requirements.txt
python manage.py check
python manage.py runserver 0.0.0.0:8000
```
Health probe available at: `http://localhost:8000/api/v1/health/`
