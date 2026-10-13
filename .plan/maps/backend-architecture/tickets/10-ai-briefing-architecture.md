---
type: grilling
blocked_by: [05, 06, 08]
---

# AI briefing architecture

## Question

**What triggers a daily briefing, what goes into it, and where does the result live?**

The briefing is step 3 of the core loop: an LLM reads the finalised schedule and writes a
one-page report of what needs doing, ordered by priority from context. From the developer's
brainstorm, quoted so this ticket stands alone: *"An LLM will be connected to the
application. It will read everything — tasks, GitHub PRs and issues, calendar, etc. It will
then generate a brief for the day."* The kiosk shows it as a widget, and the brainstorm
leaves open whether it *"updates every hour, or just the first time after daily prep
scheduling"*.

Inputs now exist. [Ticket 08](./08-task-or-widget.md) settled that Tasks and per-Mount
**Snapshots** are what the briefing reads, and nothing calls a provider at generation time.
[Ticket 05](./05-worker-and-scheduler.md) gave AI work its own `worker-ai` cluster and a
`JobRun` table. [Ticket 06](./06-daily-prep-and-wrap-up.md) defines the moments a briefing
could hang off: Daily prep completion, a skipped prep, the Pending day.

### What is already settled and must not be re-decided

- AI jobs run on the separate `worker-ai` Django-Q2 cluster; every attempt writes a `JobRun`
  ([ticket 05](./05-worker-and-scheduler.md)).
- Widgets read Snapshots and stored data, never a live provider call
  ([ticket 08](./08-task-or-widget.md)).
- Integration tokens never leave the server; the briefing is generated server-side.
- Journal text lives in Postgres ([ticket 06](./06-daily-prep-and-wrap-up.md)).

### To resolve

- The trigger: on Daily prep completion, on a schedule, on demand, or a combination, and
  what happens when prep is skipped or missed.
- Whether and when a briefing regenerates after the schedule changes mid-day.
- Context assembly: which Tasks, Time blocks, Calendar events and Snapshots, in what shape,
  and a token budget so a large Backlog cannot blow it.
- Provider and model, a cost-per-run estimate, and a spend ceiling.
- Where the output lives (a stored `Briefing` row per day, its fields, and its history), how
  the kiosk reads it when generation failed, and how a failure shows through `JobRun`.
- Whether the briefing is allowed to *propose* schedule changes, or only describe the day.
  Agent-executed tasks stay out of scope here.

## Done when

- The trigger, regeneration and failure behaviours are written down.
- The context contract is specified well enough to write the prompt builder against.
- The stored shape and the cost estimate are decided.
