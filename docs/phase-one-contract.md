# First usable day: implementation contract

This bounded contract resolves Phase 1 implementation choices under the developer's
2026-11-18 instruction to develop the full release autonomously. It supplements the
owning planning tickets; it does not close their broader Sunsama parity questions.

## Tasks, concurrent writes and deletion

All task fields are local, including imported title, notes, dates and completion.
Each Task has an integer `version` and `deleted_at`. PATCH, DELETE and restore require
`If-Match: "<version>"`; missing preconditions return 428 and stale ones return 412.
The client preserves drafts, refreshes canonical state and asks the user to retry;
there is no automatic offline replay. A user row lock serializes their mutations,
including order, timer, imports and carry-forward. Day reads return an ordered list;
reorder submits the entire day's IDs and versions, rejecting membership/version drift.

Deletion means trash, retaining provenance, Activity and actual time. Owner-only
restore restores the Task, without publishing anything. Phase 1 has no automatic
Task purge: retaining history is safer than introducing irreversible loss. Parent
relationships are same-owner, acyclic and protected. Subtasks schedule independently;
actual totals are direct per Task, never silently rolled up twice. Integration
disconnection retains personal worksheets and history, disables its Mounts and clears
credentials. Reconnect never changes a Task or restores trash automatically. This
supersedes the older disconnect-deletes-worksheets premise in backend ticket 03.

## Import and provider boundaries

A TaskSource is a per-worksheet protected provenance row, not a globally unique remote
record. Multiple intentional imports are allowed. Each import requires a UUID command
key unique per user. Retrying it with the same payload returns the original Task;
reusing it for different input returns 409. Database and record identities are scoped
to their Connection. Browsing and fetching source previews never create Tasks.

Notion reads data sources and page properties with API version 2025-09-03. The database
picker discovers its data sources; the selected data source is the Mount target.
Title and a readable property summary are copied on explicit import, raw properties
remain in Source. No provider completion, write-back, automatic projection or background
Notion content synchronization is in Phase 1. Google and Outlook request read-only
calendar access, read selected calendars, materialize timed/all-day event occurrences
and never create Tasks. Each connected account can select its own calendar Mounts.
Their day windows are bounded and refreshed periodically. Pagination,
rate limits, failed refreshes and reauthorization are visible; credentials never leave
Django. OAuth uses expiring one-use state bound to the authenticated owner and session.
Microsoft delegated OAuth requests Calendars.Read and offline_access for refresh tokens.

## Capacity and order

Work hours are a single daily start/end window plus selected weekdays in the user's
IANA timezone. No overnight work window in Phase 1. Capacity is elapsed work-window
minutes minus the union of opaque timed meeting intersections, floored at zero.
All-day events are visible but do not consume capacity. Overlapping meetings count once;
transparent/cancelled/declined events do not block. Estimates sum incomplete Tasks on
the requested do date; missing estimates count zero and have a separate visible count.
Capacity remains a workload comparison, not projections or committed Time blocks.

## Actual time and carry-forward

Only one running TimeEntry per user, enforced by a partial unique constraint. Start
on the already running Task and repeated stop are idempotent. Starting another Task
returns 409. Complete/delete stops its running timer in the same transaction. Entries
hold authoritative start/end instants. Daily totals intersect each entry with the
requested local day's UTC boundaries, handling DST and midnight; cumulative per-Task
totals sum its own entries. Sleep and browser restarts do not stop time. No inferred
actuals, manual corrections, parallel timers or focus rituals in Phase 1.

A code-owned minute schedule carries every overdue incomplete Task forward to the
user's current local date, preserving each missed date in semantic Activity. It is
safe to repeat, catches up after outages, leaves backlog/completed/trash alone and
never changes due/start dates. DST/weekends use calendar dates, with no wrap-up gate.

## Planner, static delivery and kiosk

Today, date navigation, task editor, sources/connections, settings and kiosk are
responsive static SvelteKit routes. Forms retain failed drafts, expose pending/error
states and provide keyboard buttons for order. Django serves the SPA shell only for
known client routes; unknown API/static paths remain 404. Vite proxies API and allauth
paths in development. CSRF bootstrap returns a masked token; unsafe same-origin calls
send X-CSRFToken. Re-bootstrap after login/logout rotation. Sessions are HttpOnly,
SameSite=Lax, Secure outside DEBUG; no browser bearer token for normal planner use.

Kiosk uses a device-pairing code approved by a signed-in planner. The device receives
an opaque 90-day read-only credential; only a hash is stored server-side. It can call
only the kiosk summary endpoint: date, task titles/completion/estimates, meeting titles
and times, freshness, never notes/raw Sources/credentials. Owners can revoke devices.
Poll failure retains the last redacted summary in browser storage with stale time; revoked/expired
credentials clear data and require pairing. A service worker caches only the app shell,
never authenticated API responses. The passive summary survives reloads and is cleared on an observed revocation. Richer privacy
controls remain follow-up work; no editable offline planner.

## Validation boundaries

Tests use real PostgreSQL and controlled HTTP provider responses. Real OAuth consent,
TrueNAS/Zoraxy deployment and TV distance calibration require operator credentials
and hardware; they are not claimed by automated tests.
