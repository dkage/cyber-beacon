# Cyber Beacon

A self-hosted personal planner with a retrofuturist identity and a read-only TV display.
Django owns the domain, identity, credentials and jobs; static SvelteKit is an API client.

## First usable day

Phase 1 implements local Tasks/Today, versioned edits, estimates/order/capacity, one
running timer, actual time, midnight carry-forward, Notion and GitHub worksheet import,
read-only Google and Outlook Calendar events, and paired kiosk access. AI briefing is a
placeholder. Calendar projections, timeboxing and auto-scheduling are the next release
(#20–#24).

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

Create a Notion integration, Google OAuth web application, Microsoft Entra application
and GitHub App. Configure client IDs, secrets and exact callback URLs in `.env`; see
`.env.example`. For Google, enable Calendar API and grant `calendar.readonly`. Configure
the Microsoft app for personal and organization accounts and delegated `Calendars.Read`.
Grant the GitHub App repository permissions `Issues: read-only` and `Metadata: read-only`;
repository browse/import never writes to GitHub. Notion needs read-content access to the
data sources you select. These connections never become sign-in credentials.

Generate a Fernet key once:

```sh
cd backend
uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

For local development, save the key as `FERNET_KEYS` in `.env`. To load keys from a
credential file, set `FERNET_KEYS_FILE` to its absolute path. With systemd, you can
instead use `LoadCredential=fernet-keys:/path/to/fernet-keys`. Django reads
`fernet-keys` under `CREDENTIALS_DIRECTORY` when `FERNET_KEYS_FILE` is unset. The
configured file takes precedence over `FERNET_KEYS`; a missing or unreadable file
prevents startup.

Give the web and worker processes read access to the same file. For containers, mount
it read-only and use the path inside each container. Back up the keys separately from
PostgreSQL. To rotate, prepend the new key and retain older keys until credentials have
been re-saved. Separate keys with commas or, in a file, newlines. Restart the processes
after changing keys, or recreate the containers if their configuration changed.

In Connections, connect the Provider, attach a
data source/repository/calendar, then explicitly import Notion or GitHub Issues, or
refresh calendar meetings. Provider browsing, import and sync have automated fixtures;
live OAuth consent still needs your credentials and acceptance check.

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
uv run --env-file ../.env mypy
uv run deptry .
uv run --env-file ../.env pytest
uv run --env-file ../.env python manage.py check
uv run --env-file ../.env python manage.py makemigrations --check --dry-run
uv run --env-file ../.env python manage.py spectacular --validate --fail-on-warn --file openapi.yaml
```

Mypy loads `config.settings` and checks the planner models, serializers, services and
viewsets, including unannotated function bodies. Imported modules still provide type
information. Diagnostics in other backend apps, settings, migrations and tests are
deferred while this baseline is established. The serializer suppressions cover DRF's
declarative fields and `many=True` constructor behavior, which the stubs cannot express.

Deptry uses the uv environment and the dependency groups in `backend/pyproject.toml`.
Its unused-dependency exceptions cover Django's string-registered allauth and WhiteNoise,
the PostgreSQL driver loaded by Django, and Gunicorn in the production entrypoint.

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
