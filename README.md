# Cyber Beacon

A self-hosted personal planner with a retrofuturist identity and a read-only TV display.
Django owns the domain, identity, credentials and jobs; static SvelteKit is an API client.

## First usable day

Phase 1 implements local Tasks/Today, versioned edits, estimates/order/capacity, one
running timer, actual time, midnight carry-forward, Notion worksheet import, read-only
Google Calendar events and paired kiosk access. AI briefing is a placeholder. Calendar
projections, timeboxing and auto-scheduling are the next release (#20–#24).

[Release contract](docs/phase-one-contract.md) documents the bounded decisions.
[Verification and limitations](docs/phase-one-delivery.md) records what was checked.

## Run locally

Install Docker Compose, Python 3.13 with uv, and Bun 1.3.14.

```sh
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Open http://localhost:8000 and sign in with the email/password you just created.
All four services run locally; only web and PostgreSQL bind loopback ports. Data is in
the `cyber-beacon_postgres-data` volume. Do not delete that volume to update the app.

For native development, keep PostgreSQL in Docker and stop the web/workers if running
the same processes locally:

```sh
docker compose up -d postgres
cd backend
uv sync --frozen
uv run --env-file ../.env python manage.py migrate
uv run --env-file ../.env python manage.py createcachetable
uv run --env-file ../.env python manage.py ensure_schedules
uv run --env-file ../.env python manage.py runserver
```

In separate terminals:

```sh
cd frontend
bun install --frozen-lockfile
bun run dev
```

```sh
cd backend
uv run --env-file ../.env python manage.py qcluster
```

The default worker runs carry-forward and Calendar refresh schedules. The separate AI
worker has no AI workload in this release. Vite proxies `/api` and `/_allauth` to Django
on port 8000. Use one browser hostname consistently so session and CSRF cookies agree.

## Connect Providers

Create your own public Notion integration and Google OAuth web application. Configure
client IDs, secrets and exact callback URLs in `.env`; see `.env.example`. For Google,
enable the Calendar API and grant `calendar.readonly`. Notion needs read-content access
to the data sources you select. These connections never become sign-in credentials.

Generate a Fernet key once and save it as `FERNET_KEYS` in `.env`:

```sh
cd backend
uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Back up this key separately from PostgreSQL. Rotation prepends a new comma-separated
key while retaining older keys until credentials have been re-saved. After changing
configuration, recreate the containers. In Connections, connect the Provider, attach a
data source/calendar, then explicitly import Notion records or refresh meetings.
Notion browsing/import and Calendar sync have automated provider fixtures; live OAuth
consent still needs your credentials and acceptance check.

## Kiosk

Open `/kiosk` on the display. On your signed-in planner, use Settings → Pair a display
and enter its code. The device receives a 90-day read-only credential, restricted to a
redacted summary. Revoke it in Settings. The app shell and last summary survive outages;
revocation clears stored data when the display next reaches the server. Text size is
adjustable on the display. Notes, raw Source payloads and integration credentials are
excluded from the kiosk API.

## Verify

Backend commands run from `backend/` with `uv run --env-file ../.env`:

```sh
uv run --env-file ../.env ruff check .
uv run --env-file ../.env ruff format --check .
uv run --env-file ../.env pytest
uv run --env-file ../.env python manage.py check
uv run --env-file ../.env python manage.py makemigrations --check --dry-run
uv run --env-file ../.env python manage.py spectacular --validate --fail-on-warn --file openapi.yaml
```

Frontend commands run from `frontend/`:

```sh
bun run generate:api
bunx prettier --write src/lib/schema.d.ts
bun run check
bun run lint
bunx playwright install chromium
bun run test:unit --run
bun run test:e2e
bun run build
bun run build-storybook
```

Playwright creates its own temporary PostgreSQL database and removes it on shutdown;
it never uses live Provider credentials. PostgreSQL must be running, and the local
role must be allowed to create test databases. CI runs these checks on pull requests.
The HTTP API schema is at `/api/v1/`; its API explorer is `/api/v1/docs/`.

## Deploy on the homelab

Set `DEBUG=false`, a random `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS=https://your-hostname` before using real data. Configure HTTPS
through Zoraxy and WireGuard access; keep the database private. Use the same origin for
static pages, `/api` and `/_allauth`. Back up PostgreSQL and the Fernet keys. TrueNAS,
Zoraxy and actual TV hardware need operator verification; this work verifies local
containers, not that deployment.

See [CLAUDE.md](CLAUDE.md), [CONTRIBUTING.md](CONTRIBUTING.md) and
[COMMITS.md](COMMITS.md) for engineering guidance. Product decisions live in
[the planning maps](.plan/maps/); build work lives in GitHub Issues.
