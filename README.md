# call insight

Quality control for sales calls. A call is transcribed, checked against the company checklist by
an LLM, scored, and every verdict comes with a quote from the conversation as evidence. Managers
see scores per operator, checklist item and day, confirm verdicts, and similar calls with
human-confirmed scores are fed back to the model as examples.

Multi-tenant: every company has its own team, checklist, calls and API keys, and each role sees
only what it is allowed to.

## Features

- **Analysis pipeline**: upload → transcript → embedding → LLM verdicts with quotes → weighted score,
  processed by a Celery worker with retries
- **Retrieval-augmented scoring**: similar calls with human-verified scores (pgvector) are passed to
  the model as calibration examples
- **Companies and roles**: owner, admin, manager, operator; data is filtered in SQL, foreign
  resources return 404
- **Auth**: registration with email verification, invitations, JWT, API keys for integrations
- **Statistics**: per operator, per checklist item and per day, each in a single aggregate query,
  sortable on every metric
- **Protection**: Redis sliding-window rate limits per IP, user, API key and login email
- **Email**: SMTP, file or log delivery, queued through Celery
- **Read-only demo** account for a quick look without registration
- **Frontend**: Next.js 16 + TypeScript, see [frontend/README.md](frontend/README.md)

## Stack

Python 3.13 · FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL 16 + pgvector · Redis ·
Celery + RabbitMQ · Pydantic v2 · Anthropic API · Voyage embeddings · pytest · Ruff ·
Next.js 16 · React 19 · Docker Compose · GitHub Actions

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres redis rabbitmq mailpit

python -m venv .venv
.venv/Scripts/activate            # Windows; source .venv/bin/activate elsewhere
pip install -r requirements.txt

alembic upgrade head
python -m app.fixtures.seed
uvicorn app.main:app --port 8090  # http://localhost:8090/docs
celery -A app.workers.celery_app worker --loglevel=info
```

Frontend:

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3100
```

Without `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` the worker uses deterministic fake analyzers and
embeddings, so the whole flow runs locally for free.

Seeded users (password `devpass123`): `admin@example.com` (owner), `manager@example.com`,
`nastia@example.com`, `artem@example.com`.

## Demo data

```bash
python -m app.fixtures.demo demo --create "Demo Company" --login --calls 60
```

Creates a company with a manager, operators of different skill and a month of scored calls.
Set `DEMO_ENABLED=true` to enable the read-only demo button on the login page.

## Email

Local: set `SMTP_HOST=localhost`, `SMTP_PORT=1025`, `SMTP_USE_TLS=false` and open mailpit at
http://localhost:8025. With an empty `SMTP_HOST`, messages are written to `MAIL_DIR`.
Check a real SMTP account with `python -m app.integrations.mail.check you@example.com`.

## Tests

```bash
pytest -q
ruff check .
```

The suite needs PostgreSQL with pgvector and Redis. CI runs linting, migration checks
(single head, `alembic check`, downgrade to base and back) and tests for the backend, and lint,
type checking and a production build for the frontend.

## Project layout

```
app/
  api/            routers, dependencies, rate limit guards
  core/           settings, database, security, permissions, limits, sorting
  models/         SQLAlchemy models
  repositories/   queries; visibility rules in scope.py
  services/       business logic
  schemas/        request and response models
  integrations/   LLM, embeddings, mail
  workers/        Celery tasks
  fixtures/       seed and demo data
alembic/          migrations
tests/            API and service tests
frontend/         Next.js application
```

Design decisions are described in [ARCHITECTURE.md](ARCHITECTURE.md).

## Roadmap

- Real speech-to-text; the worker currently takes transcripts from `app/fixtures/dialogues.py`
- Telephony webhook ingestion
- Checklist management from the UI
- Live status updates while a call is processed
