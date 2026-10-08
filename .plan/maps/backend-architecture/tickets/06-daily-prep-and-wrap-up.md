---
type: grilling
blocked_by: [02]
claimed_by: s65f97c43fb6d
claimed_at: 2026-10-08T06:05:59Z
---

# The daily prep and wrap-up flow

## Question

**What are the steps of the morning prep and the evening wrap-up, what does each
one read and write, and what happens on the days they are skipped?**

Graduated from fog once [the domain model](./02-domain-model.md) resolved. It was
unspecifiable before: the flow is defined almost entirely by what it reads and
writes, and until Task, do-date, bump and activity existed there was nothing to
name. Now there is.

This is the product's core loop, not a feature beside it. The developer pays for
Sunsama and keeps it specifically for this ritual, so the bar is a known one.

### What the domain model already settled, and this ticket must not re-decide

- A task is committed to a day by being given a **do date**. A task can hold a do
  date with no time block at all — that is the day's list, distinct from the
  calendar.
- A task whose do-dated day ends without completion is **bumped**: its do date is
  cleared, it returns to the backlog, and the miss is recorded as activity. Prep
  surfaces "unfinished from yesterday" as a query over that history, so a task is
  in the backlog and in the prep list at once without contradiction.
- Meetings are `CalendarEvent`s, not tasks, and cannot be bumped.
- Every meaningful occurrence is written to `TaskActivity` as it happens, with an
  actor. Anything this flow does on the user's behalf is an actor in that log.

### To resolve

- **The steps of each ritual, in order**, and which are skippable. From the
  developer's own product research, prep begins with the previous day's wrap-up if
  that was not already done, then opens the planning view.
- **Who runs the bump, and when.** A scheduled job at local midnight, or lazily on
  the first read of a new day? The first needs the scheduler and needs to know
  every user's timezone; the second means "yesterday" is computed on read and a
  day may sit un-bumped indefinitely. This is a real input to
  [the worker and scheduler ticket](./05-worker-and-scheduler.md), so it is worth
  settling in terms rather than leaving implied.
- **The journal write.** Wrap-up ends in a journal entry that lands in an Obsidian
  note in the developer's personal journal directory. What writes it, when, and
  what happens if Obsidian is unreachable — that integration is not built and this
  flow must degrade rather than block.
- **Skipped days.** What the state is when prep never happened: whether yesterday's
  plan simply persists, whether the day is marked as skipped, and what the kiosk
  shows. The research is explicit that a forgotten morning prep should be
  *conspicuous* — the display is expected to demand attention rather than fail
  quietly.
- **Whether a prep session is a stored thing.** A `DailyPrep` record — the day it
  covers, when it started, when it completed, the journal text — or purely derived
  from task activity? The journal entry alone is evidence that something must be
  stored, but that may be all of it.
- **What the API looks like.** Prep is a multi-step stateful flow across a web
  client and eventually a native one; whether it is a resource clients drive or a
  sequence of ordinary task and block writes with the ordering held client-side.
  This bears directly on the first-class-client constraint: a flow that only the
  web app can perform breaks it.

## Done when

- The steps of prep and of wrap-up are listed in order, each naming what it reads
  and what it writes.
- The bump's trigger and timing are decided, in a form ticket 05 can schedule.
- The journal write's mechanism and its failure behaviour are settled.
- The state of a skipped day is defined, including what the kiosk displays.
- Whether prep is persisted as its own entity is decided, and if so its fields are
  named and added to `CONTEXT.md`.
- The API shape is settled well enough that a native client could drive the same
  flow.

## Answer

Settled through a grilling session. Vocabulary is recorded in [`CONTEXT.md`](../../../CONTEXT.md), which takes precedence over this prose if the two drift.

### The bump is gated by the wrap-up, not by the clock

Ticket 02 says a task is bumped when its do-dated day "ends without completion". This ticket defines "ends" as **the wrap-up for that day being resolved**: completed, skipped, or auto-skipped. The task list stays pinned to the **pending day** until then, like Sunsama, and the day's dates keep showing as the previous day.

`bump_day(user, date)` is one idempotent function. It runs on wrap-up completion, a manual skip, or an auto-skip, and nowhere else. It clears `do_date` on every uncompleted task do-dated on or before that day and writes `bumped` activity (actor: the system, `for_date` the day each task was stranded on).

A clock fallback exists: `User.wrap_up_limit` (default 24h, measured from when the wrap-up became due at the rollover time). Past it, a periodic sweep records an **auto-skip**. One sweep collapses a multi-day gap.

### Per-user settings

- `day_rollover` — local time the day turns over, default 00:00 (the developer intends 02:00). Everything saying "today" resolves through it. It decides when a wrap-up becomes due, not when tasks move.
- `prep_cutoff` — local time, default 10:00. Past it, with the wrap-up resolved and no prep completed or skipped, prep is **missed**.
- `wrap_up_limit` — duration, default 24h.

### Stored entities

- `DailyPrep(user, date, started_at, completed_at, skipped_at)`
- `WrapUp(user, date, started_at, completed_at, skipped_at, auto, journal_text, journal_written_at)`

Each is unique on `(user, date)`; a row is **resolved** if `completed_at` or `skipped_at` is set. There is one `WrapUp` row per calendar day: on a gap, the real wrap-up lands on the latest unresolved day and each earlier day gets a row with `skipped_at` set and `auto=true`. There is no `bumped_through` column; the watermark is the latest resolved `WrapUp.date`. An implicit skip of prep is never stored; it is the absence of a row past the cutoff.

New activity kinds: `rescheduled` (a deliberate do-date change by a person or the ritual, with from and to) and `bumped`. Only the system bumps, so bump counts measure unattended days. Whether chains of `rescheduled` also feed decay is left to the decay feature.

### Steps

Only **Finish** is required. Step order is client UX; the server records only started and completed (no per-step persistence). An empty journal is allowed.

**Wrap-up** (user-initiated):
1. Review the day. Reads: today's do-dated tasks, completions, time blocks against estimates.
2. Per unfinished task: move to a day (`rescheduled`), return to backlog, or mark done. Writes: `do_date`, `completed_at`, activity.
3. Journal. Writes `journal_text`.
4. Finish. Writes `completed_at`, enqueues the journal write.

**Prep** (gated behind the wrap-up):
0. If the previous wrap-up is unresolved, do it first. Bump has not yet run, so the choices are the same as above, shown against the pending day.
1. Unfinished from yesterday. Reads `bumped` activity.
2. Gather. Reads backlog, due-soon tasks, today's `CalendarEvent`s.
3. Plan. Writes `do_date` and `TimeBlock`s, including the calendar publish.
4. Finish. Writes `completed_at` and fires the hook where the AI briefing will attach.

### Completion time

Marking a task done in a wrap-up lets the user enter the time they finished; it becomes `completed_at`, validated to fall within the day being wrapped and no later than now. The default is a plain check meaning **now**. In a same-day wrap-up the time input is an optional section; in a retroactive one it is shown by default. If the user cannot remember, they choose "now": `completed_at` is the real instant of recording and the activity payload carries `for_date` (the credited day) and `time_unknown`. Per-day completion totals count by `for_date` where present.

### Journal write

`WrapUp.journal_text` in Postgres is the source of truth. Completing a wrap-up never touches Obsidian. It enqueues a worker job that writes through the Obsidian Mount, **idempotently, retried with backoff until it succeeds**; `journal_written_at` stays null until it lands, and the Connection shows a health warning meanwhile. The vault is assumed to sit **on the same machine as the backend**, as a local path in the Obsidian Connection's credential blob (ADR-0003). Putting the vault in a git repo or another sync is deferred. Layout, chosen by the grill as a reversible default and not confirmed by the developer: one note per day at `<journal_dir>/YYYY-MM-DD.md`, written inside a delimited managed block so a retry replaces the block and never touches text around it.

### Skipped days and the kiosk

An explicit skip is stored (`skipped_at`) for both rituals. A skip bumps exactly like a completed wrap-up with no per-task decisions, carries no journal and enqueues no Obsidian write. An auto-skip additionally sets `auto`, with the system as actor in activity.

While a wrap-up is pending, the kiosk's task list renders the **pending day**, labelled with its date, while the calendar and clock show the real today. Two **screen-level** alerts apply, per the design brief's attention model (dismissible from the phone, never a full-screen strobe): a wrap-up pending past its due time, and prep missed past the cutoff. A skip silences the matching alert.

### API

Task and block changes made during a ritual are **ordinary task and block writes**, ordered by the client, so a half-finished ritual keeps its progress and no second write path exists. The ritual resources hold state and the journal only:

- `POST /api/v1/wrap-ups` (start, idempotent per `(user, date)`), `PATCH /api/v1/wrap-ups/{id}` (journal), `POST .../complete`, `POST .../skip`
- the same four under `/api/v1/daily-preps`
- `GET /api/v1/day-state` — the single read-model: the pending day, wrap-up state (due / resolved / auto-skipped), prep state (locked / in progress / resolved), and `prep_missed`. Clients compute none of this.

Enforcement is server-side and narrow: `POST /api/v1/daily-preps` returns `409` while a wrap-up is unresolved. Nothing else is ever blocked, so integrations and the API are never wedged by a ritual state. Nothing here is web-specific, so a native client can drive the same flow.

### For ticket 05

One idempotent periodic sweep (about every 15 minutes: auto-skip wrap-ups past their limit, which runs `bump_day`) and one retried Obsidian write job. No per-user cron entries; day boundaries come from `User.timezone` and `day_rollover`.

### Flags and omissions

- **Ticket 02's bump wording** is read as "the wrap-up resolves", which the developer confirmed in this session. Flagged here because only a human may reopen a settled decision.
- **Not specified:** a timezone change during a pending gap (travel), and an offline client replaying a ritual call; the latter is already fog on the map. How the AI briefing consumes the prep-finish hook, and notification delivery for the two alerts, belong to their own tickets.
- A month-by-month **daily log** view was raised and parked in the developer's private notes; the stored fields above already support it.

