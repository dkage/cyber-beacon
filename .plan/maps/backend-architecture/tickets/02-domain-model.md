---
type: grilling
---

# The domain model: do-date, due-date, and what a Task is

## Question

**What is a Task, and what does it mean for one to be scheduled?**

This is the root of the map. Django models get written early and migrations are awkward to unwind, so this decides the shape of the schema, the API contract, and the calendar write-back.

The sharpest known constraint, and the thing that most motivated this project: **do-date and due-date are different.** From the developer's own product research — *"If I organized things by when they're due, like every app wants, rather than when I intend to do them, as is normal behavior, I would be up all night every night."* That is a statement about what a Task **is**, not a feature request.

To resolve:
1
- The entities and their names. `Task`, and whatever represents "this task occupies 14:00–15:30 on Thursday" — a scheduled block, a time block, something else. One task may occupy several; the research explicitly asks for splitting a task across multiple blocks.
- **Do-date vs due-date vs start-date.** Which exist, which are optional, and what each means when absent.
- **Timezone semantics, deliberately.** `USE_TZ=True` with UTC storage is the easy half. The hard half: a *do-date* is a local calendar date, not an instant, and so is a due-date. Modelling them as timestamps is a trap that surfaces months later as tasks landing on the wrong day across DST or travel. A scheduled block, by contrast, genuinely is an interval of instants.
- **Task provenance.** A task pulled from Jira or Notion is a projection of something someone else owns. What is locally editable, what stays authoritative upstream, and what happens on conflict.
- Subtasks and hierarchy, and whether they schedule independently of their parent.
- Where completion lives, and whether completing locally writes back to the source.

## Evidence

Verbatim from the developer's product research, quoted here so this ticket stands alone. Each line constrains the model rather than requesting a feature.

**The do-date / due-date split — the motivating constraint:**

> "If I organized things by when they're due, like every app wants, rather than when I intend to do them, as is normal behavior, I would be up all night every night"

> "I desperately need this for planning homework and time blocking for study. I want to know when it's due but I want to plan it for days to study it without changing the initial due date"

> **Do/Due Date Distinction**: This is by far one of the most requested features — separating when you plan to work on a task from when it's actually due

**A precise invariant, and the sharpest test of whether the split is modelled correctly:**

> **Don't change end date when postponing** — Postponing a task should not shift the deadline

If moving a task's do-date drags its due-date along, the two fields are not actually independent and the model is wrong.

**A third date, distinct from both:**

> **Start date / "Start On"** — For tasks that aren't actionable until a future date

**One task, several blocks:**

> Split tasks into multiple time blocks

> **Time estimation in calendar view** — Including splitting a task into multiple time blocks

This is why a scheduled block cannot simply be two columns on `Task`.

**Hierarchy and dependency, which may or may not be in scope for a first model:**

> **Sequential/dependent tasks within projects** — Arrange tasks that depend on one or more previous tasks

> **Subtask time repeats with parent** — When a parent task repeats, subtask times should follow

> **Display parent task name** — Option to show the parent task context when viewing subtasks


## Done when

- Every entity is named, with its fields and their nullability.
- Each date-bearing field is explicitly classified as a local date or an instant, with the reasoning recorded.
- The rule for a task whose upstream source disagrees with local state is stated.
- Subtask scheduling behaviour is decided.
- `CONTEXT.md` exists at the repo root containing the resolved terms, per `docs/agents/domain.md`.
- The `## Answer` states what was decided and what was deliberately excluded.

## Answer

Settled through a grilling session. The model below is what the first Django app
can be built against; the vocabulary is now recorded in [`CONTEXT.md`](../../../CONTEXT.md)
at the repository root, which is the authority on the terms and takes precedence
over the prose here if the two ever drift.

### The spine: local fields and mirrored fields

One rule answers most of this ticket, and it applies identically to a Task pulled
from Notion and to a meeting mirrored from a calendar:

> Every mirrored thing has a **mirrored field set** and a **local field set**.
> Synchronisation writes only the mirrored set, ever.

On a Task, upstream owns `title` and `due_date`; you own `do_date`, your time
blocks, `priority`, `notes`, attachments, and completion. A sync therefore cannot
touch your schedule by construction rather than by discipline — the enforcement
point is a single `save(update_fields=MIRRORED_FIELDS)` in the sync path, and
nothing else is permitted to write from a payload.

**Mirrored fields are read-only.** Retitling a Notion-sourced task here does not
push to Notion. Write-back is per-provider surface area with per-provider failure
modes, and for the calendar specifically it is already ticket 03's question.

A distinction that read-only does *not* cover, and which matters because it is the
product's core loop: a **time block is ours**, not a mirrored thing. Dragging a
task onto Thursday at 14:00 creates a time block, and we create, update and delete
the corresponding event in Google Calendar freely — because we are its author.
That is not write-back; it is publishing our own record. It is what makes the
schedule visible on a phone after the desk is left behind.

Those calendar writes must be stamped with a marker of our own — Google Calendar's
`extendedProperties.private` is the mechanism — so that a later sync can tell our
own blocks from genuine meetings and never re-imports our schedule as foreign
events. Without it every round trip risks duplicating the day.

### Entities

**`Task`** — something you intend to do.

| field | type | null | notes |
| --- | --- | --- | --- |
| `user` | FK | no | multi-user in structure from day one |
| `parent` | self-FK | yes | subtask; schedules independently of its parent |
| `title` | text | no | mirrored when sourced |
| `notes` | text | yes | local |
| `due_date` | **local date** | yes | mirrored when sourced; absent means no deadline |
| `start_date` | **local date** | yes | absent means actionable now |
| `do_date` | **local date** | yes | absent means the task is in the backlog |
| `priority` | small int | yes | local; consulted before any upstream priority |
| `estimated_minutes` | int | yes | the planned half of planned-versus-actual |
| `completed_at` | **instant** | yes | local; never written upstream |

No status column and no source columns. Status is derived — `do_date IS NULL` is
the backlog, a set `do_date` is planned, a set `completed_at` is done — because a
status enum beside those fields is a second source of truth that drifts from them
within a month.

**`TaskSource`** — provenance, zero-or-one per Task: the connection it arrived
through, `external_id`, `url`, `upstream_version`, `upstream_status`,
`upstream_priority`, `raw` (JSONB), `last_synced_at`, `deleted_upstream_at`.

**`TimeBlock`** — a span of clock time committed to something: `user`, nullable
`task`, `title`, `starts_at` and `ends_at` as **instants**, plus a nullable
reference to the calendar event it wrote upstream. Many per task.

**`CalendarEvent`** — a mirrored meeting: the connection, `external_id`, `title`,
`location`, `organizer`, `response_status`, `raw`, `deleted_upstream_at`, and a
**local** `notes` field. Its times are split deliberately, matching what the
Google Calendar API actually sends: `starts_at`/`ends_at` as **instants** for
timed events, `start_date`/`end_date` as **local dates** for all-day ones.

**`TaskActivity`** — the append-only history of a task: `task`, `kind`,
`occurred_at`, `actor` (a person, or the integration that acted), `payload`
(JSONB).

**`Attachment`** — a file added here: nullable `task`, nullable `calendar_event`,
`uploaded_by`, `file`, `original_filename`, `content_type`, `size_bytes`,
nullable `caption`, `uploaded_at`. A `CheckConstraint` enforces that exactly one
parent is set.

**`User`** gains a `timezone` (IANA string). Local dates are meaningless without
knowing whose day it is, and the bump job needs to know when a day ended.

### Dates: which are calendar dates and which are instants

Every date on a `Task` is a **local calendar date** with no time component
whatsoever. Time of day exists only on a `TimeBlock`.

The reasoning, recorded because it is the trap this decision exists to avoid: a
do-date is the answer to *"which day's list does this appear in"*, which is a
human-calendar fact. Stored as a timestamp it silently lands on the wrong day
across a DST boundary or a flight, months after anyone remembers choosing the
type. A time block, by contrast, genuinely is an interval of instants — 14:00 on
Thursday is a moment, and it must survive being read from another timezone. All-day
calendar events follow the same logic and are stored as dates, which is why
`CalendarEvent` carries both pairs.

The three dates are three different people's claims on you: `due_date` is someone
else's, `start_date` is the world's, `do_date` is **yours**. They are independent
columns with no derivation between them, which makes the sharpest requirement in
the ticket — *postponing must not shift the deadline* — structurally impossible to
violate rather than a rule somebody has to remember.

`completed_at` is an **instant**, since both "completed today" and the evening
wrap-up need the moment rather than the day.

### Why a task's origin is a separate row

`TaskSource` exists so the canonical `Task` never branches on where it came from,
and so that synchronisation has somewhere to diff against that is not the model
every other feature reads. Table-per-provider was rejected outright: it fails this
map's own success test for ticket 03, that adding the eighth integration should be
boring.

The projection is **lossy on purpose**. Only the handful of fields the canonical
model needs are mapped; everything else stays in `raw` as JSONB. That blob buys
replayability — deciding a year from now to surface some property means
re-projecting from payloads already held, without re-fetching from an API that is
rate-limited. The blob is not a dumping ground but a staging area, and the rule for
leaving it is explicit: **a field is promoted out of `raw` into a real column when
a query needs to sort or filter on it.** `upstream_priority` is the first such
promotion, normalised per provider at sync time so that ordering can be a single
indexable `COALESCE(task.priority, source.upstream_priority)`.

Local priority winning over upstream is the same argument as do-date versus
due-date, in a different costume: their urgency is not your urgency. A ticket
marked highest priority by a company does not outrank a medical appointment, and a
model that cannot express that is wrong.

### Completion, and what happens to an unfinished day

Completion is local. `completed_at` is set here and the upstream service is not
told, because transitioning an issue is not setting a boolean — it is a workflow
transition carrying per-project rules, required fields and permissions that fail in
ways the interface would have to surface. "I finished my part" and "the ticket
closed" are also frequently different events, and seeing both is more useful than
forcing them to agree. Sunsama's behaviour here — offering the upstream statuses an
issue may transition to and letting you pick — is the considered exception to
revisit later, not a gap.

A task with a do-date for a day that ends without completion is **bumped**: its
`do_date` is cleared, it returns to the backlog, and a `TaskActivity` row records
that it was planned for that day and missed. The initial instinct in this session
was that nothing should ever auto-move a plan, on the grounds that it destroys the
record of what was intended — the history is what makes the move safe, and the
record now survives in the only place that can hold it honestly. The next morning's
prep surfaces "unfinished from yesterday" as a query over that history, so a task
is in the backlog and in the prep list at once with no contradiction.

Meetings are exempt for free: a meeting is a `CalendarEvent`, has no `do_date`, and
therefore cannot be bumped. That falls out of the entity split rather than needing
a rule.

### Why the history is semantic

`TaskActivity` records **domain events**, not row snapshots, and is written
explicitly by application code rather than by a generic history library. A
snapshot library can reconstruct *"do_date changed from Tuesday to null"* but can
never recover that this meant *"avoided again"* — and the bump count, the decay
display, and the prep list all depend on the meaning rather than the diff. Meaning
has to be written at the moment it happens.

It is a dedicated table with a real foreign key rather than a generic
content-type-based activity log, so that referential integrity holds and the
history endpoint can `select_related`. Bump counts are derived with `annotate`
rather than stored, and a counter cache is a later optimisation if the kiosk proves
it necessary.

### Naming

`TaskEvent` was the working name and was renamed to **`TaskActivity`** while
writing the glossary. `Event` was already taken by `CalendarEvent`, and a codebase
carrying both terms for unrelated things confuses every reader of it. "Activity" is
also the word GitHub and Linear use for this exact surface.

### Excluded deliberately

Each of these was considered and postponed with a reason. None require a
cardinality change to add — all are reachable by adding a nullable foreign key,
which is the cheap kind of change; the expensive kind was spent where it mattered.

- **Recurrence.** A rule, materialised instances, and per-instance exceptions is
  its own hard problem, and a half-designed version contaminates the schema
  everywhere. A recurrence rule *generates* tasks, and generated tasks are ordinary
  tasks, so nothing here blocks it. Recurring meetings are unaffected — they arrive
  already handled from the provider, which is ticket 03's concern.
- **`Project`, and local statuses.** Grouping in the first model comes from
  `TaskSource` and from the `parent` self-FK. A local project entity plus
  project-scoped statuses, for a personalised kanban, is a nullable FK away.
  Designing local-versus-upstream project reconciliation before feeling the problem
  produces a worse answer than waiting.
- **`TimeEntry` — actual time tracked, with start and pause.** Explicitly named
  here because the distinction is what the glossary exists to protect: a
  `TimeBlock` is what you planned, a `TimeEntry` is what happened. Start/pause is
  many-per-task, so `started_at`/`finished_at` columns on `Task` would be the same
  trap that two scheduling columns would have been.
- **Block categories.** The dimension that would let the dashboard answer "this
  week held six hours for rest". Its prerequisite — blocks that need no task — is
  built; the category itself is not.
- **Attachment storage backend.** `FileField` stores a relative key, and where the
  bytes live is a storage backend swapped in settings with no migration. Added to
  ticket 04 instead, with the concrete input that meeting audio is large and the
  Pi's SD card is the wrong home for it.
- **Write-back of completion and status.** Above.

### A finding for ticket 03

The developer's company migrated from Jira to Notion during this session, so Notion
is now the work task source and Jira is deprioritised. The map's choice of Notion
and Google Calendar as the two providers that stress the abstraction in opposite
directions is unaffected and, if anything, reinforced.

But Notion changes the *shape* of projection rather than only its order. Jira has
fixed fields, so mapping upstream to canonical is code. A Notion database has
arbitrary user-defined properties, so *which property is the due date* and *which
is the priority* is *per-connection configuration*. Everything settled here still
holds; it means `TaskSource`'s field promotion is config-driven for Notion, and
that is ticket 03's problem to solve rather than this one's.
