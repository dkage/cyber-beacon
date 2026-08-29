---
type: grilling
blocked_by: [02]
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
