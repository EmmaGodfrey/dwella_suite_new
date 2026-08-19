# Dwella Suite

Dwella Suite is the new Python-first monorepo for the Dwella property management product under EG Labs.

The old `dwellasuiteadmin` Nuxt project is preserved as the frontend starting point, but the suite now lives in one repo with a Django backend and one root `.env`.

## Structure

```text
dwella-suite/
  .env                 # local root environment, not committed
  .env.example         # shared environment contract
  backend/             # Django + DRF modular monolith
  frontend/            # Nuxt admin/dashboard frontend
  docs/                # product and architecture specs
  deploy/              # local Docker/dev infrastructure
```

## Backend Shape

The backend follows the architecture documents:

- Django + Django REST Framework
- PostgreSQL
- Redis + Celery
- modular monolith
- organization-scoped data access
- serializers, managers/querysets, permissions, services, tasks, and tests per module

## Frontend Shape

The frontend remains Nuxt for now and reads its public API base URL from the root `.env`.

## Local Development

Copy `.env.example` to `.env` if needed, then edit values at the repository root only.

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
yarn install
yarn dev
```

Docker infrastructure:

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
```

## Product Docs

- `docs/DWELLA_PROPERTY_MANAGEMENT_REQUIREMENTS.md`
- `docs/EG_LABS_BACKEND_ARCHITECTURE_RECOMMENDATION.md`
- `docs/EG_LABS_POS_INVENTORY_REQUIREMENTS.md`
