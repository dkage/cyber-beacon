# Cyber Beacon

A personal scheduling dashboard: work is pulled in from the services that already
hold it, placed onto a day, and pushed back out to a calendar and an always-on
display. This glossary fixes the vocabulary that everything — models, API routes,
issues, commit messages — should use.

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

**Calendar event**:
A meeting or appointment belonging to a calendar you have connected. It is never a
Task: you do not complete it, do-date it, or own it. It shares the day's timeline
with Time blocks and nothing else.
_Avoid_: Meeting, booking, appointment.

**Estimate**:
How long you think a Task will take. Stated by you, in minutes, and unrelated to
any figure an upstream service carries.
_Avoid_: Story points, effort, size.

### Provenance

**Connection**:
One authorised link to one account at one provider. You may hold several to the
same provider — a personal calendar and a work calendar are two Connections — and
losing one never affects the others or your ability to sign in.
_Avoid_: Integration, account, credential.

**Source**:
The upstream record a Task is a projection of, and everything known about that
record: which Connection it came through, its identity there, and the untouched
payload last received. A Task you created yourself has no Source.
_Avoid_: Origin, external task, remote task, integration.

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
by giving Tasks a do date and placing Time blocks.
_Avoid_: Planning session, daily planning, standup.

**Wrap-up**:
The evening counterpart: review what was and was not finished, and write the day's
journal entry.
_Avoid_: Review, retro, end of day.

**Bump**:
What happens to a Task that had a do date for a day which ended without it being
completed — it returns to the Backlog, and the fact that it was planned and missed
is kept. Repeated bumps are a signal about the Task, not noise to be tidied away.
_Avoid_: Rollover, carry over, postpone, reschedule.

**Activity**:
The recorded history of a Task, written as things happen and never derived after
the fact. It says what an occurrence *meant* — that a Task was bumped, not that a
column changed — because meaning cannot be recovered from a diff later.
_Avoid_: Audit log, changelog, task event, history entry.
