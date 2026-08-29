---
type: task
---

# Record the settled stack in CLAUDE.md and ADR-0001

## Question

Not a decision — the decisions are already made. This is the manual work that makes them durable, and until it lands every session that reads `CLAUDE.md` is misled about the stack.

`CLAUDE.md` is the declared source of truth for all agents; `AGENTS.md` exists only to point at it and states it must never be modified. `CLAUDE.md` currently describes:

- a **Go** backend on **SQLite**, module `schedule-dashboard`
- a developer *"learning Go through this project"*, plus a "Key Go Concepts to Introduce Progressively" section
- a frontend owning **Better Auth** and **Drizzle**

All of that is now wrong.

The work:

1. Rewrite the stack sections to the settled architecture in the map's Notes — Python / Django / DRF / drf-spectacular / PostgreSQL / allauth-headless, SvelteKit as a pure client.
2. Replace the Go-learning developer context. The pair-programming-guide framing may still hold, but its subject changes and the Go concepts section goes.
3. Create `docs/adr/` and write **ADR-0001: Django owns identity; every client is equal.** Record the *ownership* decision, not the library — allauth-vs-django-oauth-toolkit is an implementation note inside it, and is reversible. Capture the alternatives actually weighed (django-oauth-toolkit with Authorization Code + PKCE; a third-party IdP) and why each lost.
4. Leave `AGENTS.md` untouched.

## Done when

- `CLAUDE.md` names no Go, no SQLite, and no Better Auth or Drizzle in the backend or frontend stack sections.
- `CLAUDE.md`'s developer-context section reflects Python/Django rather than Go, and the Go concepts section is gone.
- `docs/adr/0001-django-owns-identity.md` exists, states the decision, and names the rejected alternatives with reasons.
- `git diff AGENTS.md` is empty.
- The `## Answer` records what changed and links the ADR.
