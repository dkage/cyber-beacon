# First usable day delivery

Implemented on `feat/phase-one`, 2026-11-18, against GitHub issues #8–#19.
This report distinguishes local implementation evidence from live-service acceptance.

## Delivered scope

| Issues | Implementation |
|---|---|
| #8 | Django 5.2 LTS/Python 3.13, DRF/OpenAPI, PostgreSQL, allauth headless, Postgres-backed Django-Q2 and two isolated queues |
| #9, #12 | Static SvelteKit client in the Django image; same-origin session cookies/CSRF; Vite proxy; nested-route refresh |
| #10, #11 | Owner-scoped Task lifecycle, independent local dates, semantic Activity, protected Subtasks, integer version preconditions, retained trash/restore |
| #13 | Responsive Today view, editor, date navigation, keyboard/click reorder, completion, basic Backlog access |
| #14 | Separate encrypted Notion OAuth Connection, resource discovery, paginated record browsing/search, explicit idempotent worksheet import and Source preview |
| #15 | Google readonly OAuth Connection, Calendar Mounts, paginated recurring-event expansion, timed/all-day events, leased refresh, retained stale data and freshness/error display |
| #16 | Estimates, persisted order, work hours/weekdays/timezone, overlap-safe meeting capacity |
| #17 | One running timer per user, repeat-safe start/stop, completion/deletion stops, Task/day actual totals and DST/midnight attribution |
| #18 | Code-owned minute schedule, local-midnight carry-forward and outage catch-up, repeat-safe semantic Activity |
| #19 | Paired 90-day read-only device credentials, redacted kiosk summary, stale last-good display, offline shell cache, TV text scaling and revocation clearing |

Broader parity decisions remain open. The implemented slice is specified in
[the Phase 1 contract](phase-one-contract.md). No AI execution, timeboxing, calendar
publishing, projections or auto-scheduling is included.

## Local verification

- **31 PostgreSQL backend tests** pass: real allauth session/CSRF rotation, ownership,
  dates, stale writes, real concurrent writers, reorder conflicts, timer uniqueness,
  carry-forward/DST, scheduler recovery, encrypted credentials/key rotation, Notion
  import idempotency, OAuth state, provider HTTP contracts, Google token refresh,
  calendar failure recovery, populated day serialization and device permissions.
- **7 frontend/unit/component tests** pass, including Storybook states, same-origin
  CSRF transport, rejected/non-JSON responses, unsafe URL rejection and local dates.
- **4 Playwright journeys** pass against a real Django server and isolated PostgreSQL:
  daily work through logout; mobile/deep-link/failed-draft behavior; stale-client
  conflict recovery retaining unrelated remote edits; kiosk pairing/offline hard reload/revocation, including exclusion of API responses from the service-worker cache.
- Type/Svelte checks report zero errors or warnings; Prettier/ESLint, Ruff, Django
  system checks, migration drift and warning-free OpenAPI validation pass.
- The production static build, Storybook build and Docker image build pass. Local
  Compose starts healthy web/Postgres plus distinct `default` and `ai` workers, with
  scheduled jobs observed in the default queue. The AI queue has no AI workload yet.
- Direct HTTP checks against the container return the real app shell on `/login`,
  `/today?date=…`, `/connections` and `/kiosk`, JavaScript for `/service-worker.js`,
  and proper 404s for unknown API and missing asset paths. Today was visually checked.
- Browser-test teardown removes the uniquely named test database explicitly because
  runner shutdown can bypass the server process's normal cleanup.

CI now runs these checks for pull requests and master pushes; semantic release waits
for the checks. The hosted workflow itself has not run from this local branch.

## Operator acceptance and follow-up

No live Notion/Google credentials, TrueNAS configuration, Zoraxy configuration or Pi
hardware were changed. Initial account creation and real OAuth client/key setup belong
to the operator; commands are in the root README. These checks are tracked in
[#25](https://github.com/dkage/cyber-beacon/issues/25).

The Google mirror currently covers 30 days back and 90 days forward. Capacity uses
stored meeting data; last-success/errors are visible, while explicit coverage and
provisional-capacity indicators are tracked in
[#27](https://github.com/dkage/cyber-beacon/issues/27).

Time correction/forgotten-timer recovery is deliberately later work in
[#26](https://github.com/dkage/cyber-beacon/issues/26). Offline kiosk data cannot learn of
revocation until reconnect; retention/privacy controls are tracked in
[#28](https://github.com/dkage/cyber-beacon/issues/28).

Phase 1 issues remain open for review/merge and operator acceptance. Calendar planning
continues in #20–#24; no duplicate implementation issues were created for that release.

## Reference checks

Implementation consulted the official [allauth headless configuration](https://docs.allauth.org/en/latest/headless/configuration.html),
[Django-Q2 configuration](https://django-q2.readthedocs.io/en/master/configure.html),
[Svelte static adapter](https://svelte.dev/docs/kit/adapter-static),
[Notion data-source query](https://developers.notion.com/reference/query-a-data-source),
[Google Calendar event listing](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)
and [Google web-server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server).
The official Svelte MCP autofixer reports no issues or suggestions on the new components.
