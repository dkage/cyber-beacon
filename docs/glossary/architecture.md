# Architecture and infrastructure

Source: `CLAUDE.md`, [ADR-0001](../adr/0001-django-owns-identity.md), ticket 04, ticket 06.

## Stack

| Layer | Choice |
|---|---|
| Backend | Python, Django modular monolith, DRF, drf-spectacular (OpenAPI from day one) |
| Auth | django-allauth headless, the sole account system |
| Database | PostgreSQL |
| Frontend | SvelteKit + TypeScript, Bun, Tailwind. A **pure API client**, no auth or business logic |
| Background work | Django-Q2 on the Postgres ORM broker. See [background-work.md](./background-work.md) |

## Principles

| Term | Meaning |
|---|---|
| **Django owns everything stateful** | Users, auth, OAuth credentials, integration state, migrations, jobs |
| **First-class client** | Every API consumer is equal. The web app has no privileged position. A Swift iOS app is designed for, not built |
| **Sign in vs connect** | Different scopes, consent and lifecycle. Revoking calendar access never logs anyone out |
| **Kiosk** | The always-on TV dashboard. Secondary surface, glanceable widgets |
| **Multi-user in structure** | One user in practice, SaaS-plausible later |

## API conventions

- Versioned routes under `/api/v1/`.
- `GET /api/v1/day-state` is the single read-model for ritual state. Clients compute
  none of it.
- Rituals: `/api/v1/wrap-ups` and `/api/v1/daily-preps` (start, `PATCH`, `complete`,
  `skip`). Task and block changes during a ritual are ordinary writes.
- `POST /api/v1/daily-preps` returns `409` while a wrap-up is unresolved. That is the
  only gate.

## Deployment (ticket 04)

| Term | Meaning |
|---|---|
| **Homelab** | 64GB Xeon TrueNAS box. Hosts the backend and Postgres in containers, 24/7 |
| **Pi** | Raspberry Pi 5, 8GB. Thin kiosk, runs only Chromium |
| **Prod services** | `web` (gunicorn), `worker`, `worker-ai`, `postgres`, `vault-sync`, `frontend` (nginx static). No Redis. Ticket 05 amended this list |
| **Dev** | Only Postgres in Docker. Django and Bun run natively on the Mac |
| **Zoraxy** | Shared TLS terminator outside the stack. Routes `/api` to Django and `/` to the frontend on one hostname, so cookies stay same-origin |
| **Access** | WireGuard only. Nothing is public. TLS from Let's Encrypt DNS-01 via Cloudflare |
| **Stale banner** | The TV's service worker keeps the last good data and shows "stale since HH:MM" when the homelab is down |
| **`vault-sync`** | Own container running Obsidian Headless Sync. The only read-write holder of the vault. The backend gets the vault read-only plus a writable `Journal/` |
| **Uploads** | A ZFS dataset through Django local storage, with a relative key |
| **Backups** | Hourly ZFS snapshots, a nightly encrypted `pg_dump` to S3, Cloud Sync for uploads. 24h off-box loss accepted |
| **Irreplaceable** | Local fields, uploaded files, the credential-encryption key |
| **Re-syncable** | Mirrored fields and tasks pulled from integrations |

## Credentials (ADR-0003)

OAuth credentials are encrypted at rest as an opaque JSON blob. User content is not
field-encrypted. Disk-level encryption is the deployment's job.

## Tracking

Planning decisions live in `.plan/maps/` (chartr). Anything with a diff is a GitHub
issue on `dkage/cyber-beacon`.
