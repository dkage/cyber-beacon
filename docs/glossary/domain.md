# Domain terms

Full definitions and `_Avoid_` synonyms are in [`CONTEXT.md`](../../CONTEXT.md). Use
these words in models, routes, issues and commits.

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
| **Source** | The upstream record a Task projects, plus its Connection, identity and last raw payload. No Source means you created it | origin, external task |
| **Mirrored field** | Owned by upstream. Sync overwrites it. Never written back | synced field |
| **Local field** | Owned by you (do date, Time blocks, priority, notes, attachments, completion). Sync never touches it | custom field, override |

Connection vs Mount: the Connection is the permission, the Mount is what it is aimed at.
One Google Connection can have several Mounts.

## Daily rhythm

| Term | Meaning | Don't say |
|---|---|---|
| **Daily prep** | Morning ritual: settle yesterday, assign do dates, place Time blocks. Gated behind the previous Wrap-up. **Missed** if unresolved past `prep_cutoff` | planning session |
| **Wrap-up** | Evening ritual: review the day, write the journal. **Resolved** when completed or skipped. A system skip after the limit is an **auto-skip** | review, retro |
| **Pending day** | The day whose Wrap-up is unresolved. The task list stays pinned to it | stale day, yesterday |
| **Bump** | System-only: an uncompleted Task of a resolved day loses its do date and returns to the Backlog, and the miss is recorded. A deliberate move is a **reschedule**, not a bump | rollover, carry over |
| **Activity** | Semantic history of a Task, written as things happen ("bumped", not "column changed") | audit log, changelog |

The bump is gated by the wrap-up, not the clock (ticket 06).
