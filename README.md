# Cyber Beacon

A self-hosted daily planner following Sunsama's proven workflows, with Cyber Beacon's
own visual identity, API-first architecture, AI briefing and always-on kiosk dashboard.

## Stack

### Backend

- Python + Django, as a modular monolith
- Django REST Framework, with drf-spectacular for OpenAPI
- PostgreSQL
- django-allauth (headless) — owns all authentication

> Not yet written. `backend/` still holds an abandoned Go scaffold from before the stack change.

### Frontend

Packages installed using Bun

- SvelteKit + TypeScript
- TailwindCSS
- Playwright
- Storybook

The frontend is a **pure API client** — no database, no auth logic, no business logic. Django owns everything stateful.

> The generated Better Auth + Drizzle + SQLite server stack is still present and slated for removal.

## Roadmap

### Integrations

**Google Calendar** and **Notion** come first, deliberately: Calendar is bidirectional (scheduling writes back to it), while Notion is read-heavy behind a ~3 req/sec rate limit. Between them they stress an integration abstraction in opposite directions, so building against both produces a contract that survives the rest.

Notion carries extra weight beyond that: it is the work task source, so it is where the day actually gets planned from.

Then: Outlook (personal and work tenants), Gmail, GitHub, Sentry, Obsidian (fleeting-note count), Telegram (notifications).

Jira is deprioritised. The work it tracked has moved to Notion, so the integration serves old references rather than daily use.

### AI

- Daily briefing generated once the day's schedule is finalized
- Task priority analysis
- Later: agent-executed tasks — a briefing item you can hand off to an agent to actually carry out

### Surfaces

- Interactive planner: daily preparation, ordered work, capacity, calendar timeboxing,
  Today/Board/Focus views and source selection — behavior is being reconciled against
  Sunsama before implementation
- Web dashboard, responsive from phone to a 4K TV in kiosk mode
- A native iOS client is designed *for* — the API treats every consumer as a first-class client — but is not committed to

Planning lives in two linked chartr maps:

- [Backend architecture](.plan/maps/backend-architecture/map.md): stack, domain,
  integrations, workers, identity and deployment.
- [Sunsama parity](.plan/maps/sunsama-parity/map.md): the behavioral baseline and explicit
  decisions for the [110-feature gap inventory](docs/research/sunsama/feature-inventory.md).

The [reference audit](docs/research/sunsama/README.md) records how Sunsama imports issues,
Notion pages, mail and meetings, its provider-specific sync rules, and what is **not**
known about its private implementation. Earlier domain decisions remain documented but
affected policies must be reconciled before their first migrations.

## Getting Started

### Backend

Not yet scaffolded (`#8`). See [Django API conventions](./docs/agents/django.md) and
[CLAUDE.md](./CLAUDE.md) for the planned backend stack and conventions.

### Frontend

```bash
cd frontend
bun install
bun run dev --open
```

Hit `Ctrl-C` to stop the dev server. Available frontend checks (see `frontend/package.json`):

- `bun run check` — SvelteKit sync and TypeScript check
- `bun run lint` — Prettier and ESLint
- `bun run test:unit -- --run` — Vitest unit tests
- `bun run test:e2e` — Playwright end-to-end tests (`npx playwright install` on first run)
- `bun run storybook` — Storybook on port 6006

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) and [COMMITS.md](./COMMITS.md) for commit
conventions and guidelines.