# Dwella Suite

Dwella Suite is the new Python-first monorepo for the Dwella property management product under EG Labs.

The old `dwellasuiteadmin` project is being replaced by this repo. The suite now lives in one monorepo with a Django backend, a React dashboard frontend, and one root `.env`.

## Structure

```text
dwella-suite/
  .env                 # local root environment, not committed
  .env.example         # shared environment contract
  backend/             # Django + DRF modular monolith
  frontend/            # React/Vite admin dashboard frontend
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

The frontend uses the React version of the Viho dashboard template as its base and reads its public API base URL from the root `.env`.

When adding dashboard UI, adapt components from the full React template first:

```text
C:\Users\OMEN\Desktop\EGLabs\react.zip
C:\Users\OMEN\Desktop\EGLabs\.template_compare\react-theme\Viho-Vite-React
```

## Local Development

Copy `.env.example` to `.env` if needed, then edit values at the repository root only.

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_demo
python manage.py runserver
```

Demo login after `bootstrap_demo`:

```text
admin@dwella.local
admin12345
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Docker infrastructure:

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
```

## Product Docs

- `docs/DWELLA_PROPERTY_MANAGEMENT_REQUIREMENTS.md`
- `docs/EG_LABS_BACKEND_ARCHITECTURE_RECOMMENDATION.md`
- `docs/EG_LABS_POS_INVENTORY_REQUIREMENTS.md`
- `docs/FRONTEND_TEMPLATE_REFERENCE.md`
- `docs/FRONTEND_DATA_FLOW.md`

## Production Deployment

Production uses Docker Compose behind host Nginx:

```bash
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml up -d --build
```

The expected public routing is:

```text
dwella.properties          -> 127.0.0.1:8122   marketing site (separate dwella-site repo)
www.dwella.properties      -> 127.0.0.1:8122
app.dwella.properties      -> 127.0.0.1:8121   this app (frontend container)
api.dwella.properties      -> 127.0.0.1:8120   Django API
```

Pushing to `main` deploys to production. Day-to-day work happens on `develop`
(or feature branches off it) and reaches `main` only through a reviewed merge.

`.env.prod` needs at least `APP_ALLOWED_HOSTS=api.dwella.properties`, CORS for
`https://app.dwella.properties` and `https://dwella.properties`, secure cookies,
and `APP_TRUSTED_PROXY_COUNT=1` so rate limits use the real client address.

Keep `.env.prod` on the server only. The production compose file persists PostgreSQL, Redis, uploaded media, and collected static files across deployments.
