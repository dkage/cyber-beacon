# Cyber Beacon

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

Then: Outlook (personal and work tenants), Gmail, Jira, GitHub, Sentry, Obsidian (fleeting-note count), Telegram (notifications).

### AI

- Daily briefing generated once the day's schedule is finalized
- Task priority analysis
- Later: agent-executed tasks — a briefing item you can hand off to an agent to actually carry out

### Surfaces

- Web dashboard, responsive from phone to a 4K TV in kiosk mode
- A native iOS client is designed *for* — the API treats every consumer as a first-class client — but is not committed to

Planning for the backend architecture is tracked as a [chartr map](.plan/maps/backend-architecture/map.md).

## Getting Started

### Frontend

```bash
cd frontend
bun run dev --open
```

Hit `Ctrl-C` to stop the dev server.

## Add-on Setup

### Playwright
- Run `npx playwright install` to download browsers
- Visit `/demo/playwright` to see the demo page
- Run `npm run test:e2e` to execute the example tests

### Drizzle
- Check `DATABASE_URL` in `.env` and adjust it to your needs
- Run `bun run db:push` to update your database schema

### Better Auth
- Run `bun run auth:schema` to generate the auth schema
- Run `bun run db:push` to update your database
- Check `ORIGIN` & `BETTER_AUTH_SECRET` in `.env` and adjust to your needs
- Visit `/demo/better-auth` to view the demo

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for commit conventions and guidelines.

Stuck? Visit https://svelte.dev/chat