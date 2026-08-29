# Backend architecture and domain model

## Destination

Locked architectural decisions plus a domain spec the first backend vertical slice can be built against — the point where someone can start writing Django code without another decision needing to be made first.

## Notes

**Domain.** Personal productivity scheduling, Sunsama-shaped: pull tasks from integrations, drag them onto a day timeline that syncs to the calendar, generate an AI briefing from the finalised schedule. The secondary surface is an always-on kiosk dashboard. Full product brainstorm in `notes/01-brainstorm.md`; the frontend dashboard is already specified in `notes/02-initial-prompt-claude-design.md`.

**This map plans, it does not build.** Every ticket resolves a decision. No production code is produced here.

**Skills.** Use `grill` every session, and a domain-modeling skill where one is available.

**Duplicate tracker warning.** This effort was first charted as GitHub issues — map `dkage/cyber-beacon#2`, tickets `#3`–`#7` — before the chartr convention was adopted. Both describe the same effort and will drift. Pick one as canonical before working any ticket; if this file is canonical, close the GitHub issues.

### Settled architecture

The premise of this map, decided before it existed — not steps along its route:

- **Python + Django** modular monolith. The backend was originally Go; switched for the AI/LLM ecosystem and integration library breadth, having judged that a CPU-light, I/O-bound workload gains little from Go.
- **Django REST Framework**, with **drf-spectacular** wired in from day one so the OpenAPI schema exists before there are endpoints to retrofit onto. DRF over Django Ninja for legibility: it maps cleanly onto Laravel (Serializer/API Resource, ViewSet/Resource Controller, Permission/Policy).
- **PostgreSQL** from the start, locally and in production. Not SQLite — concurrent web and worker processes writing one file is a contention problem Postgres does not have.
- **Django owns identity.** Users, auth, authorization, OAuth credentials, integration state, migrations, background jobs. Integration tokens never leave the server.
- **django-allauth headless** as the sole account system — not django-oauth-toolkit, whose third-party-developer machinery this project has no use for. Web uses HttpOnly session cookies; a future native client uses allauth's token strategy, preferring the opaque revocable one over JWT until statelessness actually pays. `socialaccount` for Google sign-in; `mfa` later.
- **SvelteKit is a pure API client.** Its generated Drizzle / Better Auth / SQLite server stack comes out.

### Standing constraints

- **Multi-user in structure from day one**, single-user in practice for months, SaaS-plausible later. Schema, auth, and credential storage all assume more than one human.
- **Every API consumer is a first-class client.** The web frontend holds no privileged position; no auth or business logic lives in SvelteKit. A native iOS client is designed *for*, not built.
- **"Sign in with Google" and "connect Google Calendar" are different things**, with different scopes, consent, and lifecycles. Revoking calendar access must not log anyone out.
- **Hardware.** An 8GB Raspberry Pi 5 drives a 4K TV; a 64GB Xeon TrueNAS homelab is also available.

## Decisions so far

<!-- one gisted, linked line per resolved ticket -->

## Not yet specified

- **The remaining integrations.** Outlook (personal *and* work tenant — the work tenant may not permit third-party app registration, which nobody has checked), Jira, Gmail, GitHub, Sentry, Obsidian, Telegram. Each needs its own shape only once the generic provider contract exists. <clears-with: 03>
- **AI briefing architecture.** What triggers generation, how context is assembled, which model, what it costs per run, and where the output lives.
- **Agent-executed tasks.** The n8n / Hermes dispatch described as "Development 2" in the brainstorm — a task the AI can perform on the user's behalf, triggered from the briefing.
- **Notification system.** Telegram, email, and the TV's attention/alerting model for overdue work and skipped daily prep.
- **Widget data contracts.** What the dashboard actually asks the API for, per widget, and at what refresh cadence.
- **Daily-prep flow mechanics.** The morning ritual itself as a sequence of steps, including the previous day's wrap-up and its Obsidian journal write.

## Out of scope

- **Frontend design and build.** `notes/02-initial-prompt-claude-design.md` already specifies it in full — design tokens, five viewport profiles, widget catalog, mock data layer. Not fog; charted elsewhere.
- **The Swift iOS app.** The API is designed so it can exist; building it is a separate effort and is not confirmed.
- **Kiosk hardware setup.** TV mounting, orientation, and Pi provisioning.
