# Cyber Beacon

A personal scheduling dashboard: work is pulled in from the services that already
hold it, placed onto a day, and pushed back out to a calendar and an always-on
display. This glossary fixes the vocabulary that everything — models, API routes,
issues, commit messages — should use.

## Reference baseline

The developer has selected Sunsama's planning workflows as the product baseline, with
Cyber Beacon identity and added dashboard. The [reference audit](docs/research/sunsama/README.md)
and [parity map](.plan/maps/sunsama-parity/map.md) record the findings. Four reversals of
the earlier model are decided and reflected below:

- **Explicit import, not automatic projection.** Connecting a source does not fill the
  task list. Remote records are browsed and deliberately imported as local worksheets.
- **Local worksheets.** An imported Task is a personal worksheet linked to its remote
  record; local fields (title, notes, dates, priority, estimate, completion) are owned here.
- **Local completion.** Completing a Task here does not write back to the provider by
  default; upstream status changes do not complete the local worksheet. Remote actions are
  separate, explicit commands.
- **Midnight carry-forward.** Unfinished work moves to the next day at midnight; shutdown
  is an optional review and does not gate rollover.

Sunsama's “start date” means our **Do date**, not our earliest-actionable **Start date**.
Capacity, ordered work, projections, pin-to-commit, auto-schedule and calendar routing are
decided in [parity ticket 05](.plan/maps/sunsama-parity/tickets/05-capacity-projections-and-timeboxing.md)
(Decisions 1–6). Meeting checklist representations are decided in shape there, with
day-lifecycle detail owned by parity 04. Still open: recurrence, channels, weekly
objectives, AI boundaries and the per-field/action matrix. Update this document and its
glossary index together when they resolve.

## Language

### Work

**Task**:
Something you intend to do. A Task is the same kind of thing whether you typed it
here or it arrived from Notion; where it came from is recorded separately and
never changes what a Task is.
_Avoid_: To-do, item, card, issue, ticket.

**Subtask**:
A Task that has a parent Task. It is an ordinary Task in every other respect — it
carries its own dates and can be scheduled on its own day, independently of its
parent.
_Avoid_: Child task, step, checklist item.

**Priority**:
Your own ordering of what matters, set by you and never by an upstream service. A
Source may carry the priority its provider assigned, which is consulted only when
you have expressed no opinion of your own.
_Avoid_: Severity, urgency, importance.

**Backlog**:
Every Task you have not committed to a day — that is, every Task with no do date.
It is a derived view, not a place a Task is moved into.
_Avoid_: Inbox, someday list, unscheduled list.

**Day order**:
The sequence of Tasks on a day, owned per-day and per-user and persisted
server-side. The projection walks it in order; you can reorder freely and auto-
arrange is always an explicit action, never silent.
_Avoid_: Queue, sort order, sequence.

**Pin**:
Locking a Task's position in the day order so re-sort, auto-arrange or carry-
forward leave it where you put it. A pin wins over every automatic ordering rule.
_Avoid_: Locked, frozen, fixed slot.

**Attachment**:
A file you have added to a Task or a Calendar event from this application — a
photo, a recording, a document. Attachments are yours; they are never sent to the
provider the thing came from.
_Avoid_: Upload, media, file.

### Time

**Do date**:
The day you intend to work on a Task. It is a claim you make on your own time, is
independent of every other date, and having one is what puts a Task on a day.
_Avoid_: Scheduled date, planned date, work date.

**Due date**:
The day a Task is owed to someone else. Moving a do date never moves a due date —
that independence is the point of having both.
_Avoid_: Deadline, end date, target date.

**Start date**:
The earliest day a Task becomes actionable. Before it, the Task is real but not
yet yours to act on.
_Avoid_: Defer date, available from, activation date.

**Time block**:
A span of clock time you have committed to something. One Task may occupy several,
and a Time block may belong to no Task at all — an hour held for rest is still an
hour held.
_Avoid_: Slot, appointment, calendar entry, booking.

**Time entry**:
A record of time actually spent. A Time block is what you *planned*; a Time entry
is what *happened*. Keeping them apart is what makes it possible to ask what your
estimates are worth.
_Avoid_: Time block, session, log.

**Projection**:
A deterministic, local-only preview of where a day's ordered remaining work would
land around meetings and work hours. It is derived from committed inputs, never
stored as a Time block, and never commits itself — only an explicit pin does.
_Avoid_: Forecast, suggested schedule, auto-plan.

**Meeting checklist**:
A local read-model of a Calendar event on the day's list: it contributes to
workload, can auto-complete when the event ends (paused while a timer runs), and
removing it never deletes the event. It is never a Task and cannot merge or hold
real subtasks.
_Avoid_: Imported meeting, event task, meeting task.

**Calendar event**:
A meeting or appointment belonging to a calendar you have connected. It is never
a Task: you do not do-date it or own it, and it can only appear on the day through a
**Meeting checklist** read-model, never as a worksheet. It shares the day's timeline
with Time blocks and nothing else.
_Avoid_: Meeting, booking, appointment.

**Estimate**:
How long you think a Task will take. Stated by you, in minutes, and unrelated to
any figure an upstream service carries.
_Avoid_: Story points, effort, size.

### Provenance

**Provider**:
A service this application knows how to speak to — Google Calendar, Notion,
Telegram. A Provider is a kind of thing, not a thing you own; what you own is a
Connection to it.
_Avoid_: Integration, service, adapter.

**Connection**:
One authorised link to one account at one Provider. You may hold several to the
same Provider — a personal calendar and a work calendar are two Connections — and
losing one never affects the others or your ability to sign in.
_Avoid_: Integration, account, credential.

**Mount**:
One remote resource attached through a Connection: a single calendar, a single
Notion database view, a single Obsidian directory. A Connection is the permission;
a Mount is what that permission is aimed at. A Mount says how the remote thing's
fields correspond to ours, and it can be detached without the Connection being
lost. For calendars a Mount carries four independent flags: **enabled**, **visible**,
**importable** and **scheduling-blocking**; visible, importable and blocking do not
imply one another.
_Avoid_: Binding, feed, channel, subscription, sync target.

**Source**:
The upstream record a Task was imported from, and everything known about that
record: which Connection it came through, its identity there, and the untouched
payload last received. A Task you created yourself has no Source.
_Avoid_: Origin, external task, remote task, integration.

**Worksheet**:
A Task imported from a remote record. It is a personal copy: its local fields —
title, notes, dates, priority, estimate, completion — are yours, while the remote
record remains visible as a source preview. Importing the same record again is a
deliberate new worksheet, not a sync conflict.
_Avoid_: Mirror, projection, synced task.

**Snapshot**:
The latest summary of a Mount — a count and a short list — kept so the dashboard
never has to ask the provider. It is how an integration appears as a widget without
becoming Tasks, and it is shown with the time it last succeeded, so a provider outage
reads as stale rather than blank. Only the latest is kept.
_Avoid_: Cache, widget data, metric, stats.

**Promotion**:
A deliberate "make this a Task" on a dashboard item that is not one. The resulting
Task is an ordinary one with an ordinary Source; nothing about it marks it as
second-class afterwards.
_Avoid_: Convert, import, pin.

**Mirrored field**:
A field an upstream provider owns. Syncing overwrites it, and this application
never writes it back.
_Avoid_: Remote field, synced field.

**Local field**:
A field you own, on a thing that may have come from elsewhere. Your do date, your
Time blocks, your priority, your notes, your attachments, your completion. Syncing
must never touch one.
_Avoid_: Custom field, user field, override.

### The daily rhythm

**Daily prep**:
The morning ritual: settle what happened yesterday, then decide what today is for
by giving Tasks a do date and placing Time blocks. It may be skipped, and is
**missed** if still unresolved past the user's prep cutoff.
_Avoid_: Planning session, daily planning, standup.

**Wrap-up**:
The evening counterpart: review what was and was not finished, and write the day's
journal entry. It is **resolved** when completed or skipped; a skip the system makes
after the wrap-up limit is an **auto-skip**. It is an optional review and does not
gate carry-forward.
_Avoid_: Review, retro, end of day.

**Carry-forward**:
What happens to a Task that had a do date for a day and was not completed — at
midnight it moves to the next day, and the fact that it was planned and missed is
kept. Only the system carries forward; a deliberate move to another day is a
reschedule. Repeated carry-forwards are a signal about the Task, not noise to be
tidied away.
_Avoid_: Bump, rollover, postpone, reschedule.

**Shutdown**:
A per-day configurable moment when work ends. It is an informational scheduling
boundary — nothing is planned past it without explicit overtime — and never gates
carry-forward.
_Avoid_: End of day, cutoff, wrap-up.

**Capacity**:
The available work minutes on a day: the work window minus the union of blocking
meeting intersections, floored at zero. Personal/private work and non-blocking
calendars do not consume it.
_Avoid_: Free time, availability, workload.

**Workload**:
Planned work against capacity: the predicted finish (walking ordered committed
sessions) and the advisory threshold warning when the plan exceeds the window.
Advisory only; it never blocks planning.
_Avoid_: Overbooked, busy, over-committed.

**Activity**:
The recorded history of a Task, written as things happen and never derived after
the fact. It says what an occurrence *meant* — that a Task was carried forward, not
that a column changed — because meaning cannot be recovered from a diff later.
_Avoid_: Audit log, changelog, task event, history entry.

### Background work

**Job run**:
The recorded outcome of one attempt at a piece of background work — a sync, a journal
write, a briefing, a purge. It is written by the system and read by people: it is what
the red indicator opens to say why something failed, in plain words, and it is kept for
thirty days. Activity says what happened to a Task; a Job run says what happened to the
machinery. Never call a background job a "task": that word is reserved for the thing
you intend to do, even though the queue library uses it.
_Avoid_: Task run, sync log, run log, audit log.

## First usable day implementation boundary

[Phase 1 contract](docs/phase-one-contract.md) specifies versioned local writes,
retained trash, independent worksheet provenance, single running Time entry, local-day
actual totals, basic capacity and read-only paired kiosk access. Disconnection retains
worksheets. Broader parity remains with its planning tickets.
