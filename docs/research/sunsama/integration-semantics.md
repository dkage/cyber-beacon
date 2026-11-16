# How Sunsama maps and synchronizes external work

Observed source set and limitations: [audit](./README.md), [source manifest](./sources.md).
Unless explicitly marked inference/recommendation, these are **first-party documented
product semantics**, not observed private server implementation. Each provider name
links to the source owning the claims in its row/section.

## 1. The common interaction, and the identities it requires

1. Connect an account/workspace with access to the desired resources. This is separate
   from signing in; Gmail and Google Calendar, and Outlook mail and calendar, are
   independently connected surfaces.
2. Browse the provider in the right panel, select a resource, filter/search/group/sort,
   and inspect a record. Browsing does not by itself commit work to the daily list.
3. Drag a record into a day, select a date, or drop it on the calendar. The last option
   creates both a local worksheet and a working session. Many connectors hide already
   imported records by default and offer an explicit show-imported switch.
4. The worksheet links back to the record and can expose an embedded remote preview.
   Local notes, time tracking, comments and subtasks remain local. Editing the remote
   preview is different from editing the worksheet and may write upstream immediately.
5. Import, completion, explicit preview actions and continuous sync each have different
   rules. They are not all implementations of “mirror this Task.”

See [task creation](https://help.sunsama.com/docs/usage-guides/tasks/creating-tasks),
[URL import](https://help.sunsama.com/docs/usage-guides/tasks/add-via-url) and the provider guides.

**Cyber Beacon design implication, not Sunsama's disclosed database:** distinguish
remote identity `(provider, account/resource context, external id[, occurrence])`
from the local worksheet ID and import-operation idempotency key. One upstream item
can support multiple intentional personal work units (explicitly documented for Jira).
Do not deduplicate retries by prohibiting all future imports of that record. A Mount's
current filter describes discovery, not necessarily the continued validity of a
worksheet imported earlier. Cross-Mount overlap must not multiply imports accidentally.

### Translation of dates

| Sunsama language | Cyber Beacon language | What must stay separate |
|---|---|---|
| Start date (day shown on task list) | **Do date** | Not our earliest-actionable Start date |
| Due date | **Due date** | Not necessarily provider due date; rules vary below |
| Planned time | **Estimate / daily planned time**, to be reconciled | Task estimate vs day allocation vs sum of committed blocks |
| Working session | **Time block** | Not Calendar event source, fluid projection or actual time |
| Tracked actual time | **Time entry** | Not inferred automatically from block duration |

Never map a field because its name looks the same. Todoist's “due date” is the
particularly sharp counterexample: Sunsama links it to its start/do date.

## 2. Per-provider issue/task/page rules

“Local → remote completion” means behavior when completing the local worksheet,
not a permission for the background reader to write arbitrary properties. Reopening,
deleting and remote completion are distinct directions and must be specified separately.

| Provider | Browsing / imported contents | Dates / estimate | Completion and remote actions |
|---|---|---|---|
| [GitHub](https://help.sunsama.com/docs/integrations/github) | Issues, PRs, Projects; repo, open/closed, assignee, PR review state and search filters; recent repos first. Local worksheet linked to issue/PR; URL import also supports discussions | No documented continuous planning-day or due-date link | **Independent both ways.** Remote close/merge does not finish worksheet; worksheet completion does not close/merge. Preview shows state, description, timeline, PR checks/reviewers/branch. Current GitHub App is read-only; older grants may edit labels; comment in GitHub |
| [Jira](https://help.sunsama.com/docs/integrations/jira) | Jira Cloud only; project, favorites, My open, Reported, Watched, Sprint and JQL; hide imported; same issue may be imported repeatedly with different titles | Due date and remaining estimate copied **once** at import; no later sync. Planning day selected locally | Import/completion prompts offer status change; completion alone does not change Jira. Preview can change status, self-assignment, priority, dates and (current feature guide) post comments. Scope docs disagree on commenting; verify grant/version |
| [Notion](https://help.sunsama.com/docs/integrations/notion) | Shared workspace/database pages only, not arbitrary prose; property display, groups, filter groups, sort, imported toggle. Up to 300 pages loaded; Notion saved views not exposed | **Only title imported**; Notion date properties not linked to local start/do or due dates | No reverse worksheet sync; completion has no effect unless automation configured. Preview changes supported select/multi-select/checkbox/date properties, removes people, ticks page to-dos, reads/posts comments; other content read-only. Database-scoped ordered import/completion automations set properties; conditional local channel assignment |
| [Linear](https://help.sunsama.com/docs/integrations/linear) | My issues (assigned/created/subscribed), custom/personal views; sort/group; priority copied | Neither due date nor planning date linked | No automatic completion link. Import and completion status prompts on by default; preview can change status/labels/priority/due/description, comments read-only |
| [Asana](https://help.sunsama.com/docs/integrations/asana) | My Tasks, projects/sections, assignee/completion/due/subtask filters; open subtasks copied and individually linked | Due date copied once; subsequent dates independent | Asana completion finishes local; local completion finishes Asana if Complete in Asana enabled (default on). Completion section prompt default on; optional import self-assignment and channel mapping. Preview supports completion/reopen, assignee, date, tags, section, plain description and comments |
| [ClickUp](https://help.sunsama.com/docs/integrations/clickup) | Home/Everything or space/folder/list, assignee/imported/done filters | Due date **bidirectional** by default; local do date independent; remote start date not synced | Completion **bidirectional** by default. Optional import assign/status prompt. Completion prompt and automatic completion mutually exclusive. Preview edits status/checklists/assignees/priority/dates/tags/description/comments |
| [Todoist](https://help.sunsama.com/docs/integrations/todoist) | Projects/sections/labels/filters, source subtasks, imported toggle | Provider due date ↔ local **do date**, only updates an existing remote due date; remote deadline not linked to local due date. Recurrence exception below | Completion bidirectional by default. Four default-on toggles: import update date, complete remotely, sync date, sync completion. To stop local completion writing remote, both completion toggles must be off. Preview edits tasks/subtasks/dates/deadline/project/labels/description/comments |
| [Trello](https://help.sunsama.com/docs/integrations/trello) | Boards/lists, title search, imported toggle | Due copied once; no later date sync | Remote completion doesn't finish worksheet. Local completion can complete remote due date (default on, reopening reverses), prompt/move list, move next column or archive. Import can self-assign/map channel/prompt/move. Preview edits lists/labels/dates/checklists/description/comments |
| [Monday](https://help.sunsama.com/docs/integrations/monday) | Boards, groups, person/status/imported filters; personal token; no equivalent of My work view | No date link | Neither completion nor dates inherently sync. Import/completion prompts default on, target arbitrary status columns. Preview changes supported status/checkbox/date columns and posts updates; write-token permission required |
| [Google Tasks](https://help.sunsama.com/docs/integrations/google-tasks) | Lists, title search, due-soon/subtask/completion/imported filters; source subtasks copied | No date link; API exposes due day, not time | Local completion/reopen → remote by default; no reverse completion sync stated. Preview edits title/details/due/completion/subtasks; older read-only grants need consent upgrade |
| [Microsoft To Do](https://help.sunsama.com/docs/integrations/microsoft-to-do) | Lists, importance/due sorts; steps copied | No date link | Local completion/reopen → remote by default; reverse completion not linked. Preview edits importance/steps/reminder/dates/note/completion. My Day unavailable through its API; moving lists may change remote ID and break links |
| [Microsoft Planner](https://help.sunsama.com/docs/integrations/microsoft-planner) | Group → plan → bucket, My Tasks/My Day views; checklist copied | No date link | Local completion/reopen → remote by default; remote completion doesn't finish local. Preview edits progress/priority/dates/notes/checklists; assignees/labels/bucket/comments handled in Planner; Graph tenant approval may be needed |
| [Apple Reminders](https://help.sunsama.com/docs/integrations/apple-reminders) | macOS desktop-only browsing via local Apple API; lists, incomplete/imported/filter/sort; title/notes/priority/due copied | Due copied once; no later date sync | Completion both ways while macOS bridge runs; local completion also supported in iOS. Optional destructive delete-on-import (off); recurring reminder completes occurrence instead. Auto-import per list every minute while app open/focused; not recurring/Today/Scheduled. API lacks advanced fields/smart lists |

### Recurring and duplicated upstream work

Todoist imports **one occurrence**, does not link its planning date, and completes that
occurrence upstream so the next appears. Sunsama-native recurrence is unavailable on
source-linked Tasks. Reimport/duplicate of a Todoist task can produce competing date
updates; Sunsama's documented workaround disables date sync for the whole connection.
That is a failure case to design around, not a behavior to copy uncritically.

For imported tasks merged as subtasks, source linkage, notes and timing survive; the
provider preview and timer remain available. Merge directly from a source panel is
supported. **Imported calendar-event tasks are an exception: they cannot merge in
either direction or have real subtasks.**

Sources: [Todoist](https://help.sunsama.com/docs/integrations/todoist),
[recurrence](https://help.sunsama.com/docs/usage-guides/tasks/recurring-tasks),
[merge](https://help.sunsama.com/docs/usage-guides/tasks/merge-tasks).

## 3. Email is a conversation-backed worksheet plus mail commands

### Gmail

Source: [Gmail guide](https://help.sunsama.com/docs/integrations/gmail).

- Multiple accounts. Label selection is one label unless Cmd/Ctrl multi-select; multiple
  labels intersect (AND). Filters include archived, spam/trash and already imported.
  A **new reply on an imported thread always appears**. Do not confuse new activity
  with permission to make a second local Task automatically.
- Subject becomes worksheet title. Local task links to the **Gmail thread**. Import
  to day/backlog or directly timebox. Opening a source preview marks it read.
- Embedded thread supports read/unread, archive/inbox, star, spam, trash/restore and
  labels. Locked controls request more access. These are real Gmail changes.
- Reply/reply-all/forward, autosaved drafts, send and a **10-second undo-send window**.
  Gmail signature can be included, preference per account in that browser. Forwarding
  omits original attachments; use Gmail for attachment forwarding.
- Per-account import and completion automations can archive, trash, mark read/unread,
  star/unstar, important/not-important, add/remove labels; multiple actions and an
  optional per-email prompt. Example: remove Inbox/add In progress when importing,
  then archive/remove In progress when completing.
- Local notes, time, subtasks and worksheet comments **do not sync to the mail thread**.
  Mobile opens the mail app rather than the embedded web/desktop composer.
- GitHub notification pills identify the underlying issue/PR/discussion. Already-imported
  filtering can hide notifications about an imported item until a new notification.

### Outlook mail

Source: [Outlook guide](https://help.sunsama.com/docs/integrations/outlook).

- Multiple accounts; folder and All/Focused/Other views. Filters: all, unread, flagged,
  attachments and imported; new messages on imported email remain visible.
- Subject → title; worksheet links to the **Outlook message**, while preview shows
  the conversation. This is not proof that its stored identity is a conversation ID.
- Preview marks read; embedded controls edit read/unread, flags and categories.
  Archive/delete happen via automation or Outlook, not the same inline controls as Gmail.
- Reply/reply-all/forward with saved draft and 10-second undo-send. Forward **includes**
  original attachments; Outlook signature is **not** available. Sending needs additional
  consent. Until granted, Save & open in Outlook hands off the draft. Admin approval
  may be required. Mail.Read alone cannot implement these features.
- Per-account import/completion actions: read/unread, add flag, flag complete, clear flag,
  delete, archive; optional prompt and multiple actions. Local worksheet content stays local.
- Microsoft 365 Autoplan toggle covers Outlook, To Do and Planner together; do not assume
  that every connected product gets an independent AI permission switch in Sunsama.

### Email forwarding is a different ingestion channel

Source: [forwarding](https://help.sunsama.com/docs/usage-guides/email-forwarding).

Two secret addresses target today or backlog (`+backlog`). Forward, reply, CC or BCC
works; subject required and becomes title; body stays in private email preview, not
notes. Attachments excluded; messages over 35MB fail. Today uses the user's timezone;
default channel applies. Anyone holding the address can add work; changing workspace
name changes the addresses. This does **not** establish a synchronized mailbox source
or support sending replies. For Cyber Beacon it also requires an inbound mail path
that does not silently expose the WireGuard-only application.

## 4. Calendar sync is not task-source sync

Sources: [calendar](https://help.sunsama.com/docs/integrations/calendar),
[meeting import](https://help.sunsama.com/docs/usage-guides/importing-meetings),
[calendar selection](https://help.sunsama.com/docs/usage-guides/timeboxing/timeboxing-choosing-calendar),
[playlist](https://help.sunsama.com/docs/usage-guides/playlisting),
[scheduling](https://help.sunsama.com/docs/usage-guides/timeboxing/timeboxing-auto-scheduling).

### Separate layers

1. **Remote calendar event**: meeting/appointment with organizer, attendees, response,
   times and remote write permission. Create/edit/delete from Sunsama affects remote.
2. **Imported meeting checklist representation**: tied to the event; includes workload,
   notes and completion. Removing from checklist does not delete remote. Auto-completion
   options Always/Never/Only with invitees; default documented Always, except while a
   timer is running. Manual removal suppresses auto-reimport; changing settings normally
   adds/removes representations, except manually removed ones and those with edited actuals.
3. **Task projection**: deterministic preview of ordered remaining work around blocking
   events and hours. No remote event, not locked, not AI. Adjacent Parallel tasks share
   an interval; a Focused task breaks the run. Active timer first; fixed routines constrain order.
4. **Working session**: committed task block created by drag/pin/auto-schedule. Can live
   on an internal private calendar or an external writable one. Many per worksheet/day.
5. **Actual time**: tracked/manual entries, not meetings or planned sessions. These and
   completion markers can have separate calendar layers.

### Import filtering

Calendar enablement, visual visibility, meeting-import selection and scheduling blocking
are independent. Exclusions cover solo events (own connected accounts don't count as
other invitees), free events, OOO/HOLD titles, unconfirmed attendance, multi-day all-day
and optionally single-day all-day events. New-account Auto-sync vs prompt default is
inconsistent between current meeting article and FAQ; verify instead of hard-coding it.

### Scheduling details

- Target selection: channel-linked calendar → task default → internal calendar; separate
  default for new appointments. Private/personal channel tasks publish private; configurable
  busy/free and default/none reminders. Not a single publish target per user.
- Working hours per weekday, channel override and one-day override; gaps None/5/10/15m.
  Default unsized task duration 30m (15/30/45/60 configurable).
- Auto-scheduling `X` commits existing projections or finds room today without using past
  time. Remaining planned duration; ≤1h tasks split only if necessary, longer tasks fit
  gaps in at most 3 blocks; Shift-X requests one block.
- No room: schedule outside hours, find another day (up to month), defer tomorrow or cancel.
- Collision/early finish auto-rescheduling affects **only owned working sessions**, never
  meetings/past days. Early finish closes the session and pulls contiguous subsequent
  work forward until a gap ≥30m. Undo can revert the dependent moves without undoing
  the user's triggering drag. Separate toggles default on; Shift-drag skips once.
- Local non-blocking calendar policy does not change remote free/busy. Event override
  wins over calendar policy. Detailed guide says declined, all-day and Google Focus time
  events do not block; imported/specific calendar-event edge cases need live verification.

**Unknown implementation:** no evidence of remote ETag strategy, push channel renewal,
retry dedupe, event ownership markers, or offline race resolution. Keep our ticket 03
ETag/remote-wins mechanics labelled as **our proposed guarantee**, not Sunsama's.

## 5. Exports and the rest of the connector catalog

Sources: individual integration guides linked above and below.

| Connector family | Additional documented behavior / losses | Cyber Beacon status |
|---|---|---|
| Asana, Linear, ClickUp | Export title/notes/due/subtasks to concrete project/team/list; modifier copies and links. Linear destination group can set status/project/cycle/priority; ambiguous team rejects drop | Not planned; design command/undo before any local removal |
| Notion | Export title, notes/subtasks as page text; group sets a property. No channels/comments/objectives/time export; copy stays linked | High-value backlog option for actual work source |
| Trello | Export into board list; notes/due/subtasks as checklist; copy adds backlink comment | Later connector |
| Todoist | Export destination depends on project/section/label/date/custom filter; copied task remains linked | Later; protect duplicate-date feedback loops |
| Monday | Export board/group; notes become first update, subtasks subitems, due into designated/first date column | Later |
| Google Tasks / Microsoft To Do | Export into list with subtasks/steps; To Do notes keep basic rich formatting | Later |
| Microsoft Planner | Export concrete plan/bucket, not My Tasks/My Day; plain-text notes, max 20 checklist items | Later |
| All documented export/copy flows above | Local task removed on export, retained on copy; undo offered within one minute. No server compensation guarantees disclosed | Our durable history must not be sacrificed to mimic UI wording |
| [Slack](https://help.sunsama.com/docs/integrations/slack) | Message action, /todo with date/backlog parsing, task-link unfurl, ritual/highlight sharing; focus status/DND and title privacy; Sunny search requires extra grant | Not in initial stack; Telegram notification adapter isn't equivalent |
| [Teams](https://help.sunsama.com/docs/integrations/microsoft-teams) | Message/post action, channel-thread preview (reply/react if authorized), chat backlink, ritual/highlight sharing, focus presence/DND | Later; employer permission feasibility separate |
| [Toggl](https://help.sunsama.com/docs/integrations/toggl) | Send task/subtask actual entries; channel/context project/task/tag/billable mappings; local corrections replace **today's** entries, no historical-day sync | Depends on TimeEntry plan; do not infer generic bidirectionality |
| [Zapier](https://help.sunsama.com/docs/integrations/zapier) | Per-workspace regenerated token; actions create/update/find task/channel or find-or-create; not a trigger | Our API/n8n can serve similar goals; no need to adopt service automatically |
| iCloud / CalDAV | Calendar app passwords, custom HTTPS server incl. Nextcloud; iCloud device-subscribed calendars unavailable | Calendar breadth decision, no backend client secrets |
| Zoom / Google Contacts / Google Meet | Add conferencing, search invitee contacts; separate authorization | Not implied by Calendar READ/WRITE_BACK |
| [MCP server](https://help.sunsama.com/docs/integrations/mcp) | External assistant → local planning/time/calendar, OAuth Streamable HTTP; cannot read connected mail/tools through it | Distinct first-class third-party client/security scope |
| [AI Connected Apps](https://help.sunsama.com/docs/integrations/ai-connected-apps) | Sunny/Autoplan → external MCP tools; up to 20 apps; read/allowed vs write/ask-first defaults, per-tool Never. Autoplan only allowed reads; Sunny writes ask | Distinct from native sync adapter and from external agent task execution |

## 6. What “syncs” actually means, and what we must specify

Sunsama exposes at least six different mechanisms under integration UX:

1. Fetch-on-browse remote previews (its privacy manual says source contents normally
   remain in session/browser cache, with limited server metadata caching).
2. One-time import copies into a local worksheet.
3. Explicit remote commands from a permissioned preview.
4. Configured import/completion actions, possibly with a per-record prompt.
5. Selected continuous field links in specific providers.
6. External-activity collection for highlights, distinct from task completion or imports.

Source: [privacy/data storage](https://help.sunsama.com/docs/security/privacy-notes).
The manual describes up to 30-day encrypted activity retention for end-of-day summaries,
short-lived account metadata caches (10/30/60 minutes depending on provider), and AI
controls. This is not evidence of their exact request cadence or database schema.

### Cyber Beacon policy design requirements

Recommended inputs to parity tickets 02/03 (not a settled Python interface yet):

- Keep remote record storage/discovery and local worksheet creation separate. Snapshots
  serve the kiosk even for records never imported. Import action carries user intent.
- Define field ownership **per field and provider policy**, including one-time copies
  and local retitles, not `MIRRORED_FIELDS` as the whole integration story.
- Define action descriptions, availability given granted scopes and resource permission,
  valid transitions/options, confirmation, and stable idempotency key. Run commands
  through the shared budgeted server transport; never hand tokens to a client.
- Store an outbound intent/result so retries cannot reapply transitions, delete email
  twice, resend mail or create two exports after an ambiguous timeout. Where upstream
  lacks idempotency, reconcile the outcome instead of blindly retrying.
- Decide local success vs remote failure and make pending/failed actions visible in
  JobRun/action state; do not roll back actual work because a source is unavailable.
- Specify reopen, source deletion, lost permission, filter exit, and explicit dismissal
  separately. None is automatically “personal work finished.”
- Define cache/content retention and AI disclosure intentionally. Our durable raw payloads
  support offline kiosk, but need scope/size/retention rather than copying Sunsama's
  fetch-on-browse model or promising its privacy properties.
- Cross-account isolation, scope upgrades, tenant refusal and connection revocation stay
  independent from login. Provider capabilities alone do not prove resource write access.

## 7. Concrete scenarios the amended plan must pass

1. A Jira issue needs research Monday and implementation Wednesday: two worksheets,
   one upstream identity, separate do dates/notes/time; retry Monday's import adds none.
2. A GitHub PR merges while a “write release notes” worksheet remains unfinished:
   remote status updates, but worksheet stays open until the user decides.
3. Import a Notion page, rename personal action, then the page title changes: the source
   preview updates without destroying local wording, do date or history under the chosen policy.
4. A Gmail thread gets a reply after its worksheet completed: show new source activity,
   do not silently resurrect or duplicate personal work; user chooses follow-up behavior.
5. Gmail import marks read and removes Inbox, but the second call fails: local import
   remains identifiable, pending side effect retries safely, no duplicate Task.
6. Complete a Notion worksheet with a Done-property action while offline: preserve local
   completion and queue exactly the intended remote action with a visible failure path.
7. A meeting is on two connected calendars: one underlying occurrence must not double
   workload, and removing its checklist entry must not cancel the meeting.
8. A personal task routes to a personal calendar even when work is the global default;
   hidden reference calendars may still be non-blocking without changing remote busy status.
9. An export creates the remote task but times out before response: retry reconciles
   identity; no local history loss or double-created remote work.
10. A permission downgrade disables only the remote action; local worksheet, source
    link and kiosk last-good Snapshot remain accessible within our own data policy.
