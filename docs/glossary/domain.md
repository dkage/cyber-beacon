# Domain terms

Full definitions and `_Avoid_` synonyms are in [`CONTEXT.md`](../../CONTEXT.md). Use
these words in models, routes, issues and commits.

**Reference baseline:** explicit import, local worksheets, local completion and midnight
carry-forward are decided (parity ticket 13). Meeting checklists, calendar routing,
capacity/projections, recurrence, channels and weekly objectives remain open in the
[parity map](../../.plan/maps/sunsama-parity/map.md). Sunsama's start date means our
**Do date**. See [reference translation](./sunsama-reference.md).

## Work

| Term | Meaning | Don't say |
|---|---|---|
| **Task** | Something you intend to do, whether typed here or arrived from Notion | to-do, item, card |
| **Subtask** | A Task with a parent. Otherwise fully independent, with its own dates | child task, checklist item |
| **Priority** | Your own ordering. Upstream priority is consulted only when you have none | severity, urgency |
| **Backlog** | Every Task with no do date. A derived view, not a place | inbox, someday list |
| **Attachment** | A file you added to a Task or Calendar event. Never sent upstream | upload, media |
| **Estimate** | Your guess in minutes. Unrelated to upstream figures | story points, effort |

## Time

| Term | Meaning | Don't say |
|---|---|---|
| **Do date** | The day you intend to work on a Task. Having one puts it on a day | scheduled date, planned date |
| **Due date** | The day it is owed to someone else. Never moved by moving the do date | deadline, end date |
| **Start date** | Earliest day the Task is actionable | defer date |
| **Time block** | A span of clock time you committed. May have no Task | slot, appointment |
| **Time entry** | Time actually spent. Planned is Time block, actual is Time entry (not built yet) | session, log |
| **Calendar event** | A meeting from a connected calendar. Never a Task | meeting, booking |

All Task dates are **local calendar dates** (no time of day). Only a `TimeBlock` holds
instants.

## Provenance

| Term | Meaning | Don't say |
|---|---|---|
| **Provider** | A kind of service we can talk to (Google Calendar, Notion, Telegram) | integration, adapter |
| **Connection** | One authorised link to one account at one Provider. This is "the integration" you own | integration, account |
| **Mount** | One remote resource under a Connection: one calendar, one Notion data source, one Obsidian directory. Holds mapping, cursor, freshness | binding, feed, sync target |
| **Source** | The upstream record a Task was imported from, plus its Connection, identity and last raw payload. No Source means you created it | origin, external task |
| **Worksheet** | A Task imported from a remote record; a personal copy whose local fields are yours | mirror, projection |
| **Snapshot** | Latest count and short list for a Mount, so widgets never call a provider. Shown with `last_succeeded_at`. Latest only | cache, widget data |
| **Promotion** | Manual "make this a Task" on a widget item — one form of import. Yields an ordinary worksheet with an ordinary Source | convert, pin |
| **Mirrored field** | Owned by upstream. Sync overwrites it. Never written back | synced field |
| **Local field** | Owned by you (do date, Time blocks, priority, notes, attachments, completion). Sync never touches it | custom field, override |

**Task or widget (ticket 08).** A record is a Task only if it is yours, you could do-date
it, and done is your call. Everything else is widget-only. A Task-projecting Mount must
carry a filter (default "mine"), has a cap on open projected Tasks (~200) and needs
confirmation on first sync.

Connection vs Mount: the Connection is the permission, the Mount is what it is aimed at.
One Google Connection can have several Mounts.

## Daily rhythm

| Term | Meaning | Don't say |
|---|---|---|
| **Daily prep** | Morning ritual: settle yesterday, assign do dates, place Time blocks. **Missed** if unresolved past `prep_cutoff` | planning session |
| **Wrap-up** | Evening ritual: review the day, write the journal. **Resolved** when completed or skipped. Optional; does not gate carry-forward | review, retro |
| **Carry-forward** | System-only: an uncompleted Task moves to the next day at midnight, and the miss is recorded. A deliberate move is a **reschedule** | bump, rollover |
| **Activity** | Semantic history of a Task, written as things happen ("carried forward", not "column changed") | audit log, changelog |

Carry-forward happens at midnight, not gated by the wrap-up (parity ticket 13).

## Background work

| Term | Meaning | Don't say |
|---|---|---|
| **Job run** | The recorded outcome of one attempt at background work (sync, journal write, briefing, purge), with the error in plain words. Kept 30 days. The model is `JobRun`. Never call a background job a "task", which is reserved for the domain Task | task run, sync log, run log |
