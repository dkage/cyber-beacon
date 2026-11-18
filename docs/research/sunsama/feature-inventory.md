# Feature inventory: Sunsama → Cyber Beacon

This is the feature coverage index, not a claim that undocumented experiments or
enterprise customizations were exhaustively discovered. Sources were inspected on
2026-11-16; [method and limits](./README.md), [all source URLs](./sources.md).
Integration details and the complete documented connector list are in
[integration-semantics.md](./integration-semantics.md).

**Coverage describes planning, not implementation.** The production backend is not
written. `Partial` = concepts exist but behavior/contracts are missing; `Different` =
a settled decision conflicts; `Deferred` = explicitly postponed; `Missing` = no durable
plan found; `Keep` = matching intent or an intentional Cyber Beacon architecture choice.
Owners below are ticket numbers on the [parity map](../../../.plan/maps/sunsama-parity/map.md).
An owner must close each row as adopt/adapt/defer/reject, with reasons, not lose it.

## Source admission and worksheet tasks

Sources: [creating/importing](https://help.sunsama.com/docs/getting-started/basics/importing-and-creating-tasks),
[URL import](https://help.sunsama.com/docs/usage-guides/tasks/add-via-url),
[merge](https://help.sunsama.com/docs/usage-guides/tasks/merge-tasks), individual integrations.

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F001 | Browse remote work in a side panel before importing | Different: filtered Mounts project Tasks automatically; add candidate browsing distinct from Task storage | 02 |
| F002 | Drag a candidate to a day creates its worksheet there | Partial: do dates exist, but no candidate/import operation | 02 |
| F003 | Drag candidate straight to calendar imports and timeboxes | Partial: TimeBlock publishing exists; atomic intent/idempotency undefined | 02, 05 |
| F004 | Add to today, choose date, or choose backlog without drag | Partial: ordinary writes exist, admission UX absent | 02, 09 |
| F005 | Already-imported filtering; show again intentionally | Missing: distinguish imported UI state from eligibility and deletion | 02 |
| F006 | Remote search/filter/group/sort/account switch | Partial: Mount filter is sync configuration, not an interactive source browser | 02 |
| F007 | Paste a supported source URL; connect if needed; preview before saving | Missing: canonical URL resolution and permission-safe fallback | 02 |
| F008 | Generic URL or inaccessible source becomes a plain linked task | Missing: generic backlink separate from source identity; SSRF-safe resolution | 02 |
| F009 | Same Jira issue can have multiple worksheets with different titles | Different/unclear: source reconciliation identity must not impose one Task per remote record | 02 |
| F010 | Worksheet notes, subtasks, comments, timing stay personal | Partial: notes and attachments local, but comments, rich text and per-source title ownership incomplete | 02, 09 |
| F011 | Separate remote preview can edit permitted upstream fields | Different: mirrored fields are globally read-only and only blocks are published | 03 |
| F012 | Merge an existing task or candidate into another as subtask; retain notes, timing and source; unmerge | Partial: independent self-FK exists, preservation/merge commands do not | 02, 09 |

## Provider behavior and email

Sources: [Gmail](https://help.sunsama.com/docs/integrations/gmail),
[Outlook](https://help.sunsama.com/docs/integrations/outlook),
[Notion](https://help.sunsama.com/docs/integrations/notion),
[GitHub](https://help.sunsama.com/docs/integrations/github),
[Jira](https://help.sunsama.com/docs/integrations/jira),
[privacy](https://help.sunsama.com/docs/security/privacy-notes).

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F013 | Field sync policies differ by provider and field | Different: one live mirrored title/due-date policy is not enough | 03 |
| F014 | GitHub close/merge does not complete worksheet in either direction | Different: ticket 08 resolves remote closure into local completion | 03 |
| F015 | Jira/Linear/Monday import and completion status prompts | Deferred: upstream transitions explicitly postponed | 03 |
| F016 | Notion import/completion property automations per database | Different: no upstream writes; add ordered, conditional command policies | 03 |
| F017 | Asana/ClickUp/Todoist completion policies differ from Microsoft/Google tasks | Missing: per-provider direction, reopen and opt-out matrix | 03 |
| F018 | Remote write controls reflect granted permissions; incremental consent | Partial: connection scopes exist, per-action locks/consent do not | 03 |
| F019 | Export local task into a remote project/list/database; modifier copies and links | Missing: field losses, destination selection, compensation/undo | 03 |
| F020 | Email subject → title; task links to thread/message; personal worksheet | Partial: promotion says “reply to this”, not message/conversation identity | 02 |
| F021 | Gmail labels combine by intersection; imported filter reveals new replies | Missing: unseen activity is not “new Task automatically” | 02 |
| F022 | Outlook folders, Focused/Other, unread/flag/attachment filters | Missing: provider browsing contract | 02 |
| F023 | Previewing email marks it read; inline thread/conversation preview | Different: a preview can be a remote mutation, must be explicit in permissions | 03 |
| F024 | Gmail triage controls and configurable import/completion actions | Missing: archive/trash/read/star/importance/label actions | 03 |
| F025 | Outlook flags/read/categories plus archive/delete automations | Missing: do not reuse Gmail labels or action vocabulary | 03 |
| F026 | Reply/reply-all/forward, saved draft, 10-second undo-send | Missing: mail-client scope; additional sending consent, not current Mail.Read scope | 03, 12 |
| F027 | Gmail signature supported, forward omits attachments; Outlook opposite attachment/signature limits | Missing: document deliberate mail-client limits, not a generic “email integration” | 03, 12 |
| F028 | GitHub notification email can resolve underlying issue/PR, avoids stale duplicate import display | Missing: cross-provider links and dedupe vs new activity | 02 |
| F029 | Daily highlights collect one's work in tools even when no worksheet imported | Missing: Snapshot latest state is not external activity history | 04, 10 |
| F030 | Browser/session cache for browsing; bounded server metadata/activity retention | Different: durable raw payloads and kiosk Snapshots are ours; define minimization/retention | 03, 12 |

## Daily, weekly and organizational planning

Sources: [legacy ritual](https://help.sunsama.com/docs/usage-guides/daily-planning/legacy),
[shutdown](https://help.sunsama.com/docs/usage-guides/daily-highlights),
[weekly objectives](https://help.sunsama.com/docs/usage-guides/weekly-objectives),
[weekly rituals](https://help.sunsama.com/docs/usage-guides/weekly-objectives/weekly-planning),
[channels](https://help.sunsama.com/docs/usage-guides/channels-and-contexts).

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F031 | Manual ritual: reflect, gather meetings/tasks, check workload, order/timebox, share | Partial: missing explicit estimates/capacity step, order and summary | 04, 05 |
| F032 | Plan future dates, re-enter planning, context-filtered runs, evening planning for tomorrow | Partial: unique per-day ritual lacks revision/replanning semantics | 04 |
| F033 | Working hours and shutdown time per weekday; unavailable days | Missing: rollover time/prep cutoff are not working hours | 05 |
| F034 | Workload threshold and predicted finish warning; personal work excluded | Missing: estimates exist but no workload/read model or thresholds | 05, 07 |
| F035 | Shutdown review, highlights, mood and reflection; publish ends shutdown | Partial: journal/Obsidian exists, not activity highlights or publish/privacy | 04 |
| F036 | Shutdown does not move unfinished work | Different: Wrap-up resolution currently triggers Bump into Backlog | 04 |
| F037 | Midnight rollover, configurable top/bottom placement, consecutive-day badge | Different: pending-day pin and wrap-up limit are not parity | 04 |
| F038 | Past-day progress breadcrumbs from actual time or completed subtask | Missing: TaskActivity helps but historical day membership unplanned | 04, 06 |
| F039 | Auto-archive after inactivity (>4 consecutive days default); actual time/subtask completion prevents it | Different: auto-archive rejected; distinguish archive from Backlog/trash | 04, 08 |
| F040 | Weekly objectives have notes, channel, time/progress, linked daily Tasks | Deferred/missing: generic Project postponed; objective is a separate concept | 07 |
| F041 | Extend/carry over objectives, retain notes, unlink tasks without deleting | Missing: week identity, history and lifecycle | 07 |
| F042 | Weekly plan/review rituals; optional combined flow; weekday-based target week | Missing: daily-only ritual model | 07 |
| F043 | Share daily/weekly plans and reviews to Slack, Teams, email | Partial: briefing delivery planned; ritual summaries are different payloads | 11 |
| F044 | Channels categorize work; Context groups channels; personal excludes work capacity | Deferred: block categories are not equivalent to task channels | 07 |
| F045 | Defaults, filtered creation and import rules assign channels | Missing: assignment precedence and overrides | 07 |
| F046 | Channel links to calendar for timeboxing; separate calendar import channel | Different: single global publish target cannot express this | 05, 07 |
| F047 | Daily priority resets unless configured; persistent backlog priority has different levels | Different: one local small-int priority; upstream fallback is not daily intent | 07 |
| F048 | Automatic ordering honors priority, fixed times, manual pins and running timer | Missing: Task has no persisted day ordering/pin semantics | 05, 09 |

## Calendar, projections and scheduling

Sources: [calendar](https://help.sunsama.com/docs/integrations/calendar),
[meeting import](https://help.sunsama.com/docs/usage-guides/importing-meetings),
[playlist method](https://help.sunsama.com/docs/usage-guides/playlisting),
[timeboxing](https://help.sunsama.com/docs/usage-guides/timeboxing),
[auto-scheduling](https://help.sunsama.com/docs/usage-guides/timeboxing/timeboxing-auto-scheduling),
[calendar selection](https://help.sunsama.com/docs/usage-guides/timeboxing/timeboxing-choosing-calendar).

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F049 | Internal private calendar works with no external account | Partial: blocks may lack event, but offline/local-only planning behavior unspecified | 05 |
| F050 | Google, Outlook, iCloud, CalDAV/Fastmail/Nextcloud calendars; multiple accounts | Partial: Google/Outlook planned; others absent | 12 |
| F051 | Calendar enabled, visible, importable and scheduling-blocking are independent | Missing: Mount enabled/mirrors alone cannot express them | 05 |
| F052 | Per-calendar non-blocking default with event override; distinct remote free/busy | Missing: local availability policy must not accidentally patch remote busy state | 05 |
| F053 | Projections: ordered remaining estimates around meetings and hours; fluid, local-only, not AI | Missing: explicitly distinguish from TimeBlock | 05 |
| F054 | Pin projection/press X commits working sessions; undo | Partial: drag publishing only | 05 |
| F055 | Multiple working sessions per task, across days; resize changes planned time | Partial: many blocks exist; per-day planning and estimate coupling undefined | 05, 06 |
| F056 | Auto-schedule with buffers, splitting (max 3), one-block override, no past-time pick | Missing: deterministic scheduling service | 05 |
| F057 | Overcommit offers overtime, next day with room (up to month), defer, cancel | Missing: conflict/capacity UI and policy | 05 |
| F058 | Auto-reschedule own sessions on collision; never move meetings/past days | Missing: scoped batch changes and atomic undo | 05 |
| F059 | Finishing early shortens session and pulls contiguous sessions forward until ≥30m gap | Missing: opt-in policy, preserve original plan/actual distinction | 05 |
| F060 | Task-calendar target precedence: channel → default tasks calendar → internal | Different: at most one publishing Mount per user | 05 |
| F061 | Different default for new events; working-session privacy, busy/free and reminders | Missing: task publication policy is not general calendar event editing | 05 |
| F062 | Create/edit/delete events, attendee responses, Meet/Zoom, contacts | Different/partial: external events read-only except local notes | 05, 12 |
| F063 | Import meetings as checklist work, manually or auto/suggest | Different: CalendarEvent can never be Task and no promotion | 04 |
| F064 | Meeting import filters: invitees, free/busy, OOO/HOLD, attendance, multi/single-day all-day | Missing: checklist eligibility separate from calendar visibility | 04 |
| F065 | Imported-event auto-completion: always/never/invitees; running timer prevents automatic completion | Different: no completable meeting representation | 04 |
| F066 | Remove checklist event without deleting remote; manual removal suppresses re-import | Missing: local suppression and event occurrence identity | 04 |
| F067 | Imported meetings cannot merge or contain real subtasks | Different: if linked checklist added, don't indiscriminately apply Task self-FK | 04 |
| F068 | Calendar layers for actuals/projections/completions, 1–3x zoom and color options | Partial: kiosk calendar widgets planned, interactive planner layers absent | 09 |

## Actual time, focus and routines

Sources: [planned/actual](https://help.sunsama.com/docs/usage-guides/tasks/planned-and-actual-times),
[focus](https://help.sunsama.com/docs/usage-guides/focus-mode),
[focus bar](https://help.sunsama.com/docs/usage-guides/focus-bar),
[breaks](https://help.sunsama.com/docs/usage-guides/breaks),
[recurrence](https://help.sunsama.com/docs/usage-guides/tasks/recurring-tasks),
[backlog](https://help.sunsama.com/docs/usage-guides/backlog).

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F069 | Start/pause/resume task and subtask timers; manual actual time | Deferred: TimeEntry named, not specified | 06 |
| F070 | Correct/move/delete entries, cross-midnight entries, no future edits or editing running entry | Missing: server validation and history | 06 |
| F071 | Day totals in list vs cumulative totals on task; history by day | Missing: one task estimate is insufficient for day-specific planning | 06 |
| F072 | Optional planned-as-actual on completion if nothing tracked | Missing: preserve inferred actual vs measured provenance | 06 |
| F073 | Parallel tasks share projected space; workload counts longest adjacent run | Missing: scheduling/time arithmetic | 05, 06 |
| F074 | Parallel timers overlap and divide actual time evenly; Focused stops all others | Missing: global-single-timer assumption must be explicit | 06 |
| F075 | Focus mode, next task progression, calendar peek and starts-soon focus switch | Missing: dashboard is not an interactive focus mode | 09 |
| F076 | Desktop focus bar/menu tray, global timer shortcut, join meeting, task completion | Missing: native shell not implied by SvelteKit | 11 |
| F077 | Break reminders, snooze 5m/skip, break timers, countdown/count-up Pomodoro | Missing: attention system distinct from overdue task alerts | 06, 11 |
| F078 | Timer sound choices/volume, warnings at 10/5/0 minutes | Missing: quiet hours and kiosk-safe adaptation | 11 |
| F079 | Recurrence daily/weekdays/weekly/monthly/yearly, interval and weekday rules | Deferred: rule + generated instances intentionally postponed | 08 |
| F080 | Rough or rigid clock time; Parallel occurrences; ordinary instances with copied fields | Missing: recurrence scheduling policy | 08 |
| F081 | Edit one vs all incomplete, stop/extend series; preserve completed history | Deferred/missing: no exceptions/series commands | 08 |
| F082 | Unedited rollover occurrence removed when next occurrence arrives; edits preserve uniqueness | Missing: dedupe must not discard real progress | 04, 08 |
| F083 | Repeating source-linked tasks prohibited; source recurrence imports one occurrence (Todoist) | Missing: series ownership and source occurrence identity | 02, 08 |
| F084 | Backlog horizons: next week/two, month, quarter, year, someday, never | Different/partial: null do date only; add optional horizon without fake dates | 08 |
| F085 | Backlog folders removed on assigning a day; search and priority filter | Missing: folder lifecycle is not a Project | 08 |
| F086 | Trash holds deleted tasks one week; undo and restore | Partial: ticket 09 open; disconnect policy currently 30 days | 04 |
| F087 | Duplicate/template task retains reusable structure; one task may be visible on multiple days | Partial: no copy semantics; preserve vs duplicate source/time identity | 02, 09 |
| F088 | Toggl actual-time export, per-channel project/tag/client/billable mapping, today-only corrections | Missing: time-entry integration beyond READ/WRITE_BACK | 06, 12 |

## Surfaces, capture, AI and product breadth

Sources: [Today](https://help.sunsama.com/docs/usage-guides/today-view),
[Board](https://help.sunsama.com/docs/getting-started/basics/kanban-task-view),
[shortcuts](https://help.sunsama.com/docs/usage-guides/keyboard-driven-actions),
[forwarding](https://help.sunsama.com/docs/usage-guides/email-forwarding),
[Sunny](https://help.sunsama.com/docs/usage-guides/sunny),
[Autoplan](https://help.sunsama.com/docs/usage-guides/daily-planning),
[MCP](https://help.sunsama.com/docs/integrations/mcp),
[AI apps](https://help.sunsama.com/docs/integrations/ai-connected-apps),
[settings](https://help.sunsama.com/docs/settings/user-settings),
[mobile](https://help.sunsama.com/docs/settings/mobile-settings),
[workspace](https://help.sunsama.com/docs/settings/workspace-settings).

| ID | Sunsama feature and rule | Our planning coverage / required adaptation | Owner |
|---|---|---|---|
| F089 | Today, day-column Board, Calendar-centered mode, date navigation and default view | Missing: private brief specifies dashboard only, not planner | 09 |
| F090 | Search task type/date/channel, archived results, one-shot sorts and command palette | Missing: query endpoints + keyboard/touch equivalents | 09 |
| F091 | Fast creation directives for date/estimate/channel/objective/priority/parent/folder | Missing: API parsing boundaries and accessible form controls | 09 |
| F092 | Global add-task desktop shortcut; generic/source deep links | Missing: web/native responsibility and safe scheme handling | 11 |
| F093 | Forward email to secret today/backlog address; subject title, body preview, no attachments, 35MB cap | Missing: inbound mail path not compatible with assuming private API is publicly reachable | 11 |
| F094 | Slack message action and /todo; Teams message action; backlinks/thread preview | Missing: Telegram NOTIFY is not inbound message capture | 11, 12 |
| F095 | Share summaries, highlights feed, reactions/comments and meeting-note email | Missing: privacy-filtered publishing separate from journal export | 04, 11, 12 |
| F096 | Sunny chat: local task/calendar/time/objective operations and saved conversations | Deferred/missing: briefing + future task execution are narrower | 10 |
| F097 | Autoplan beta: braindump, tools, hours, priorities, themes and standing rules | Missing: proposal/change-set lifecycle distinct from briefing | 10 |
| F098 | Review agent changes, judgment calls, per-action/whole-run undo and replan | Missing: provenance, version checks and compensating operations | 10 |
| F099 | AI estimate/channel/objective suggestions; independent toggles | Missing: opt-in context scope and deterministic fallback | 10 |
| F100 | External assistants use remote OAuth MCP for local planning data, not source mail/tools | Missing: do not expose integration tokens/data through generic agent access | 10 |
| F101 | Incoming MCP apps expose tools to Sunny; Read/Write + allowed/ask/never; planning reads only | Missing: opposite direction from serving MCP; permissions/security boundary | 10 |
| F102 | Privacy, per-tool activity inclusion, AI opt-outs and data retention | Partial: credentials secured; content/AI/provider permissions need product contract | 03, 10, 12 |
| F103 | Slack/Teams focus presence/DND and private-title handling | Missing: permissioned outbound side effect tied to timer lifecycle | 11, 12 |
| F104 | Mobile share sheet/Siri, Live Activities or Android timer notification, badges and widgets | Deferred: native client designed for, not committed | 11 |
| F105 | Mobile offline mode (organization-gated), font scaling, left-hand/RTL, haptics | Partial/deferred: stale kiosk cache exists, editable offline replay not settled | 09, 11 |
| F106 | Timezone-change alert, time format, week start, density/display settings | Partial: timezone/DST groundwork exists; client settings contract absent | 09 |
| F107 | Reminder schedule, daily/weekly ritual prompts, summary email drafts | Partial: prep missed and worker health alerts planned, not reminder preferences | 11 |
| F108 | All documented provider families, including Google Tasks, Microsoft tasks, CalDAV and Apple Reminders | Missing beyond initial connectors; inventory every family but stage by actual use | 12 |
| F109 | Shared/private workspaces, invites, roles, teammate privacy and highlights feed | Deferred: multi-user structure is not a shared-workspace specification | 12 |
| F110 | Enterprise SAML/SCIM/audit/policy controls; billing/referrals/onboarding courses/support roadmap | Missing, not parity-critical for self-hosted personal product; explicit disposition required | 12 |
| F111 | Coding-agent host (installed 3.5.2): run Claude Code / Codex / pi as local agents that read and write planning data via ACP + device pairing + machine-scoped prefs | Missing: REA-new; distinct from Sunny/Autoplan and from external execution; needs parity 10 boundary | 10 |
| F112 | Native desktop shell (installed 3.5.2): global add-task window, tray/mini focus bar, keep-running-in-tray, custom URL scheme, auto-update with relaunch toast and ShipIt/Squirrel guard | Missing: native shell not implied by SvelteKit; roadmap item | 11 |
| F113 | Local-OS connector pattern (installed 3.5.2), e.g. native Apple Reminders Swift bridge: per-minute auto-import, destructive delete-on-import option, recurring-occurrence handling | Missing: macOS-local bridge incompatible with Linux server; cannot reuse server-owned token model as-is | 12, 11 |

## Cyber Beacon additions and intentional architecture differences

These are not Sunsama gaps to remove:

- Kiosk dashboard with TV landscape/portrait, desktop, tablet and mobile profiles;
  widgets, calibration, glanceability, freshness and cached failure states.
- Obsidian journal writes and note counters, Telegram alerts/briefing delivery,
  Sentry/SonarQube snapshots and later external agent execution.
- Django API ownership, durable server-side records/Snapshots, WireGuard-only access,
  provider-independent worker orchestration and honest planned-versus-actual history.
- Cyber Beacon visual identity, accessibility and safe attention model. Channel colors
  must not override global semantic colors or turn the kiosk into a distracting strobe.

Keep these while adopting the proven planner interactions. The reference is behavior,
not Sunsama's brand, source code, internal architecture or subscription packaging.
