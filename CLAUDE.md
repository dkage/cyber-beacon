# Cyber Beacon — Agent Instructions

This is the shared instruction source for all agents. `AGENTS.md` points here and
must remain unchanged. Put shared instruction updates in this file.

## Product and current state

Cyber Beacon is a self-hosted personal planner following Sunsama's planning workflows,
with its own retrofuturist identity and an always-on kiosk dashboard. Both surfaces
consume the same server-owned domain.

The intended workflow is to create local Tasks or explicitly import remote records as
personal worksheets, assign work to a day, estimate and order it, plan around meetings,
and record actual time. Calendar timeboxing follows the first usable day. AI briefing,
plan drafting and agent execution have separate, unresolved boundaries; AI is not a
prerequisite for using the planner.

**Implementation is still at the scaffold stage.** `backend/` contains abandoned Go
code, not the planned Django backend. `frontend/` contains the generated SvelteKit app
with Better Auth, Drizzle and SQLite still awaiting removal. Scaffold code and installed
add-ons describe what exists, not the intended architecture. Inspect the working tree
and live issues before reporting implementation progress.

## Architecture

| Layer | Settled direction |
|---|---|
| Backend | Python, Django modular monolith, Django REST Framework |
| API | Versioned `/api/v1/...` routes; drf-spectacular OpenAPI from day one |
| Database | PostgreSQL locally and in production |
| Identity | django-allauth headless, the sole account system |
| Background work | Django-Q2, Postgres ORM broker, `worker` and `worker-ai` clusters; no Redis |
| Web | SvelteKit + TypeScript, Bun, TailwindCSS; pure API client |
| Frontend tools | Playwright, Vitest, Storybook, Prettier and ESLint |
| Hosting | Containers on TrueNAS; Raspberry Pi as thin kiosk; WireGuard access, Zoraxy TLS |

- Django owns users, authentication, authorization, credentials, integration state,
  migrations, domain rules and background jobs. The frontend renders state and handles
  interactions, including login UI, without owning an account system or database.
- Every API consumer is first-class. Design for a future native client; building Swift
  iOS, native desktop or general offline editing is not currently committed scope.
- Structure data and permissions per user from day one, even with one user in practice.
- Signing in with a provider and connecting its services have separate scopes and
  lifecycles. A user can connect several accounts per Provider; disconnecting one must
  not log the user out.
- Integration credentials stay server-side and are encrypted at rest. Read
  [ADR-0002](docs/adr/0002-integration-connections-separate-from-identity.md) and
  [ADR-0003](docs/adr/0003-credential-encryption-at-rest.md) before integration work.

**Static web delivery is the implementation target, with validation outstanding.**
Issues #9 and #12 cover the static build and browser session/CSRF flow.
[Backend ticket 12](.plan/maps/backend-architecture/tickets/12-static-frontend-and-packaging.md)
owns the packaging proof, deep-link refresh and development proxy behavior.
[ADR-0001](docs/adr/0001-django-owns-identity.md) retains older SvelteKit BFF wording;
reconcile it when that proof lands rather than treating either approach as implemented.

## Planning and implementation

Two trackers serve different purposes:

- **Decisions** live in versioned chartr maps under `.plan/maps/`. A planning ticket
  resolves a question into prose; it does not implement production code.
- **Buildable work** lives in [GitHub Issues](https://github.com/dkage/cyber-beacon/issues).
  These issues already exist. A slice can proceed when its relevant decisions are
  settled; the entire planning effort need not finish first.

Both maps are active:

- [Backend architecture](.plan/maps/backend-architecture/map.md) records stack,
  deployment, integration and API decisions, including historical answers superseded
  by the newer product baseline.
- [Sunsama parity](.plan/maps/sunsama-parity/map.md) owns behavioral reconciliation,
  remaining feature contracts and release disposition. Read the relevant ticket before
  implementing affected behavior. Numeric blockers are local to each map.

For planning sessions, follow the map's grilling workflow; use domain modeling when
settling vocabulary or models. `CHARTR.md` describes the local workflow when present.
It is generated per machine, uncommitted, and may legitimately be absent.

### Agreed product baseline

[CONTEXT.md](CONTEXT.md) and
[parity ticket 13](.plan/maps/sunsama-parity/tickets/13-baseline-reversals.md) record four
approved changes to the earlier model:

1. Source browsing and explicit import are the default; connecting a Provider does not
   automatically populate the task list.
2. Imported Tasks are local worksheets. Title, notes, dates, priority, estimate and
   completion belong to the user here; source data is a separate preview.
3. Completion is local by default in both directions. Provider actions are separate,
   explicit commands with their own permissions.
4. Unfinished work carries forward at midnight. Wrap-up is optional and does not gate it.

Do, due and start dates are local calendar dates. Time blocks are committed intervals
of instants; Time entries record actual time. Proposed task placement is distinct from
both. Exact projection, calendar routing, meeting checklist, timer, recurrence and
day-state contracts remain with their planning tickets. The
[Sunsama audit](docs/research/sunsama/README.md) supplies evidence, not automatic approval
to implement every reference feature.

### Release sequence

The [project board](https://github.com/users/dkage/projects/6) tracks these releases;
read live issue status and acceptance criteria when choosing work.

| Release | Issues | Intended result |
|---|---|---|
| First usable day | #8–#19 | Django foundation, static client, auth, local Tasks/Today, Notion import, read-only Calendar meetings, estimates/order/capacity, timer, carry-forward and kiosk |
| Calendar planning | #20–#24 | Internal calendar, projections, pin-to-commit with undo, calendar semantics/channel routing, auto-scheduling |

Start with the backend scaffold (#8) and frontend cleanup (#9), then establish the
authenticated local task loop (#10–#13). Calendar planning is the next release and a
high priority once that foundation can support it; its design gate is parity ticket 05.
Capacity in #16 also depends on that ticket. Priority labels alone do not override
dependencies or open design gates.

Before Task migrations/API work, consult backend ticket 09 for unresolved stale-write
and deletion rules. Before import/sync, consult parity 02/03; for day lifecycle, 04;
for timers, 06; for planner surfaces, 09. Kiosk authentication remains backend ticket 11.
Check issue blockers and linked planning gates: an open issue is not proof its design
is ready. Keep changes within the settled slice and update its acceptance criteria
when a missing contract is resolved.

## Documentation and delivery

- **Backend work:** before changing models, APIs, authentication, jobs or backend tests,
  read [Django API conventions](docs/agents/django.md).
- **Domain work:** read [CONTEXT.md](CONTEXT.md), applicable [ADRs](docs/adr/), and
  [domain documentation rules](docs/agents/domain.md). CONTEXT owns vocabulary; ADRs own
  architecture decisions. [The glossary](docs/glossary/README.md) is a lookup index.
- **Decision changes:** update the owning ticket, affected earlier answers, CONTEXT and
  glossary together. Check the glossary whenever a map, ADR or CONTEXT changes; amend
  every changed term, model or infrastructure name. Preserve unresolved questions as
  unresolved rather than silently replacing them with implementation assumptions.
- **Issue operations:** use `gh` for `dkage/cyber-beacon`; follow
  [issue-tracker conventions](docs/agents/issue-tracker.md). For triage, read
  [label conventions](docs/agents/triage-labels.md).
- **Commits:** before writing any commit message, read [COMMITS.md](COMMITS.md).
  Its format applies to all commits in this repository.
- **Navigation:** [docs/README.md](docs/README.md) indexes the documentation. Inspect
  package scripts and configuration for current commands instead of assuming the
  planned stack is runnable.

## Developer context

The developer is a senior PHP/Laravel engineer with previous Django/DRF experience.
Explain Python/Django behavior and ecosystem differences when useful, without teaching
general programming concepts. Useful bridges: DRF serializers cover API Resources and
FormRequests; ViewSets/routers cover resource controllers/routes; permission classes
cover policies; Django ORM covers Eloquent; `manage.py` covers Artisan. Production
workers are Compose services with restart policies.

## Private research

The gitignored personal scratch directory may be read for context. Keep it uncommitted
and ignored. Committed artifacts, including commit messages, must stand alone without
references to private scratch paths. Include required findings inline and attribute
them generically to the developer's product research.

## AWS access

Use the AWS MCP server for all AWS operations. Never invoke the AWS CLI from a shell,
including through wrappers, absolute paths or nested shells. Local credentials carry
permissions that bypass the MCP-specific mutation restriction. If AWS MCP is unavailable,
stop AWS work and report that; any command requiring direct execution belongs to the
operator.
