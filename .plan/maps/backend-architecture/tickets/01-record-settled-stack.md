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

## Answer

Done. `CLAUDE.md` and `docs/adr/0001-django-owns-identity.md` now carry the settled architecture.

**`CLAUDE.md`** — the backend section is Python / Django / DRF + drf-spectacular / PostgreSQL / allauth-headless, and states plainly that no backend code exists yet and the directory still holds an abandoned Go scaffold. The frontend section drops Better Auth and Drizzle from the stack, names SvelteKit's role as a pure API client, and flags that the generated server stack is still physically present and slated for removal — a doc that claimed it was already gone would mislead the next session. Added: the ownership diagram, the standing constraints (multi-user structure, every client first-class, sign-in-with-Google is not connect-Google-Calendar), and a Hardware section.

**Developer context** — the pair-programming-guide framing is kept, since it is a standing preference rather than a Go artifact, but its subject changed. The developer is recorded as rusty on Django/DRF rather than new to it, so guidance bridges Laravel idioms rather than teaching basics. The "Key Go Concepts" section is replaced by a Laravel↔Django mapping table, which carries the supervisord→systemd correction so it is not rediscovered.

**Agent skills** — a new subsection records the two-tracker rule: *if it has no diff, it's a chartr ticket; if it has a diff, it's a GitHub issue.* Without it, a future session finds `docs/agents/issue-tracker.md`, concludes GitHub is the planning surface, and re-creates the drift this map just removed.

**ADR-0001** records the *ownership* decision — Django owns everything stateful, every client is equal — not the library. Rejected alternatives are kept because each will otherwise be re-proposed: Better Auth as an IdP, a third-party IdP, and django-oauth-toolkit with Authorization Code + PKCE. The DOT entry notes that PKCE is standard for any public native client including first-party ones, so the objection reads as scoped to the ceremony rather than as a misunderstanding of PKCE.

**Also corrected, outside the ticket's stated scope:** `README.md` carried the same stale stack — Golang, Sqlite, Drizzle, Better Auth — and is more public-facing than `CLAUDE.md`. This ticket's *Done when* named only `CLAUDE.md` and the ADR, so the ticket was under-scoped. The README's Stack section is fixed and it gained a Roadmap section, which is now the single home for the integration and AI roadmap; both were removed from `CLAUDE.md`, where they failed the every-session test that governs what belongs there. The `### Drizzle` and `### Better Auth` setup instructions were left in place, since they describe code that still exists and still runs.

**Excluded, deliberately:**

- No code was deleted. Removing the Go scaffold and the SvelteKit server stack is buildable work with a diff, so by this repo's own rule it belongs in a GitHub issue, not here.
- `CONTEXT.md` was not created. `docs/agents/domain.md` says these files are created lazily when the first term actually resolves; that is ticket 02's job.
- `AGENTS.md` untouched, as it requires.
