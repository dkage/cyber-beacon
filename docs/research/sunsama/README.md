# Sunsama reference audit and Cyber Beacon gap map

Inspected **2026-11-16**. Product baseline: Sunsama's current public manual and the
installed macOS desktop **3.4.14**, build `2610024fcalyyd7`.

## Start here

- [Feature inventory](./feature-inventory.md): feature-by-feature comparison, current
  coverage, and the decision ticket that owns each gap.
- [Integration semantics](./integration-semantics.md): how issues, pages, email and
  meetings become work; field mapping, actions, completion and sync direction.
- [Source manifest](./sources.md): all inspected manual URLs, article titles and
  REA capture identities; coverage and limitations.
- [3.5.2 addendum](./evolution-3.5.2.md): post-audit desktop findings (coding-agent
  host, native desktop shell, Apple Reminders); relevant to AI and client epics.
- [Coverage audit](./coverage-audit.md): maps the twelve first-slice GitHub issues
  against the feature inventory and flags what is deferred vs critical.
- [Sunsama parity planning map](../../../.plan/maps/sunsama-parity/map.md): the route
  from these findings to an agreed product specification.

**Status:** research is complete for the bounded source inventory, not a certification
of every feature in every Sunsama deployment. Product direction is confirmed by the
user: follow Sunsama closely, with Cyber Beacon's own identity and added dashboard.
Individual schema changes and reversals of settled decisions are **not** silently
approved by that direction. The linked open tickets decide them.

## Evidence and method

REA performed controlled navigation of the public first-party manual in temporary
Chromium profiles, captured accessibility text, and terminated each owned browser.
80 distinct URLs were captured, including an obsolete calendar-settings link that
returned the manual index rather than an article. Child articles were followed for
recurrence, sorting, task creation, weekly rituals and timeboxing. No signed-in task
was created, edited, completed or deleted; no email was sent and no integration was
connected. These are **documented product rules**, not witnessed account mutations.

REA also statically analyzed five selected sources from the installed `app.asar`:
`main/app-url.js`, `main/main-window.js`, `renderer/main-window-preload.js`,
`resources/mini-focus-bar.js`, `main/add-task-window.js`. Parent Evidence:
`ev_0c363256aeeba725ef907795b0286ba5610dc7663e68fe64c0956321045288a7`.
ASAR SHA-256: `70fceccf28f6038827696b0ee4fc1734df6822ccbaa20660c7659f5e7610a3d1`.
The package's identity/version, source text and HTML were additionally inspected
read-only with ordinary local file tooling; those observations are not REA runtime
Evidence. The desktop loads `https://app.sunsama.com/`, not an offline copy of the
main planner. Local focus-bar code corroborates timer, planned/actual time, break,
Pomodoro and completion controls. It cannot establish the remote planner's schema.

Limitations retained rather than hidden:

- The initial broad static analysis exceeded REA's retained-representation budget.
  The successful narrowed analysis parsed five files without parse failures, but
  application/semantic coverage is partial, with explicit node/unknown ceilings and
  1,714 unselected inventoried files. Zero inferred Electron boundaries is **not**
  evidence of no IPC or no desktop functionality.
- ASAR integrity declarations disagree with the two unpacked native Reminder helpers.
  Analysis used `record-and-continue`; mismatched bytes are **observed-untrusted**.
  We did not execute or infer Reminder behavior from those binaries.
- A requested loopback CDP endpoint for the desktop was not reachable. No authenticated
  desktop UI/network capture was obtained. Public documentation captures succeeded.
- First-party docs can disagree. The meeting-import article says new accounts default
  to Auto-sync; the FAQ still says prompt-by-default. The integration guide describes
  Jira commenting, while the privacy page's older permission description says no
  comment writes. Treat defaults/scopes as version-sensitive and verify at build time.
- Internal polling intervals, webhooks, retry policy, database tables, remote ETags,
  conflict ordering, event markers and exactly-once guarantees are **unknown**. No
  private server implementation was inspected. Our existing polling/ETag design is
  ours, not a discovery about Sunsama.

## The most consequential corrections

### 1. A planning worksheet, not a universal mirrored task database

Sunsama lets you **browse remote work without committing it to your task list**. You
select a few issues/pages/emails, then import them to a day, the backlog, or directly
onto the calendar. The imported local task is a personal worksheet linked to the
remote record: local notes, subtasks, estimates and time tracking do not become
comments or changes in the team's tool. Remote preview edits are a separate surface.
See [integration semantics](./integration-semantics.md).

Our tickets 02/03/08 instead primarily describe continuously projecting filtered
Notion/GitHub/Jira records into Tasks. A mandatory mine filter and a cap of 200 limit
the flood; they do not reproduce deliberate admission. Promotion covers email but
not the general source-browser workflow. The parity plan must decide explicit import
as the normal interaction, without sacrificing stored Snapshots for the kiosk.

### 2. Remote completion does not universally mean personal completion

GitHub is the clearest counterexample: closing an issue or merging a PR does **not**
complete its Sunsama task, and completing the worksheet does not mutate GitHub. Jira
and Linear offer status prompts; Notion offers configured property actions; Asana and
ClickUp have different completion rules; Google Tasks and Microsoft task products use
one-way local-to-remote completion. These cannot be implemented as one global rule.

Ticket 08's `resolved -> complete Task` rule contradicts GitHub worksheet semantics.
Tickets 02/03's no upstream writes rule omits useful explicit Notion/email actions.
Revisit both directions together; do not add a generic bidirectional-sync switch.

### 3. Dates and estimates are not all live mirrors

Sunsama calls the day a task appears on its **start date**. In Cyber Beacon that is
**Do date**. Cyber Beacon's **Start date** remains earliest actionability and is *not*
the translation of Sunsama's start date.

Notion imports only the title, not its date properties. Jira copies due date and
remaining estimate once. Asana/Trello copy due date once. Todoist uniquely links its
due date to the planning day, while ClickUp links due dates. This differs from our
single mirrored title/due-date policy and local-only estimates. Local worksheet
renaming and more than one worksheet for the same upstream issue need explicit design.

### 4. Three layers of time, not two

Our model separates committed **Time blocks** from actual **Time entries**. Sunsama
also has **task projections**: a deterministic, fluid calendar preview calculated
from task order, remaining time, work hours and blocking events. A projection neither
creates an external event nor commits the task to that clock time. Pinning or
pressing `X` creates working sessions. Projections and stored Time blocks must not be
conflated, especially by the dashboard or an AI briefing.

### 5. Daily capacity is central

The legacy ritual explicitly checks workload before finalizing a plan. Personal
contexts do not count toward work capacity. Meetings can be imported to the checklist
and workload. Working hours, shutdown time, buffers and overcommit choices constrain
scheduling. We currently have estimates and dates, but not that capacity contract,
persisted task order, daily estimates, or workload arithmetic.

### 6. Our rollover is a deliberate difference, not Sunsama behavior

The manual consistently describes incomplete work rolling to tomorrow at **midnight**,
with progress breadcrumbs on past days; repeated inactivity can auto-archive it.
Shutdown explicitly **does not move unfinished tasks**. Our Wrap-up-gated Bump clears
do dates into the Backlog, pins the Pending day and can auto-skip after 24 hours.
Ticket 06's phrase “like Sunsama” is unsupported and contradicted by current docs.
Preserve the historical decision, flag the error, and resolve the choice explicitly.

### 7. “Calendar events are never Tasks” is not parity

Sunsama keeps the underlying event but can represent it on the checklist, attribute
meeting time to workload, add notes, and auto-complete its checklist representation
when the meeting ends (unless a timer is running). Removing it from tasks does not
remove the calendar event. An imported meeting cannot be merged or have real subtasks.
Cyber Beacon can retain separate event identity, but needs a deliberate linked
checklist/read-model decision instead of ruling the behavior out by definition.

### 8. Current Sunsama has much more AI than our original reference

The current manual leads with **Autoplan**, an agentic beta enabled for new workspaces,
while documenting the manual ritual as legacy. It drafts a day from connected tools,
rules, weekday themes, existing work and capacity; reports changes and judgment calls;
and supports undo. Sunny can modify local tasks/calendar/time, while ordinary source
integrations are read-only to the assistant. MCP-connected apps have separate write
approvals. This is distinct from an after-planning briefing and from executing work
through n8n/Hermes.

Recommended adoption: **manual planning foundation first**, deterministic projections
next, optional agentic drafting later. “Current beta is the default” is not a reason
to require AI to plan a day or to allow silent writes to work systems.

## Recommended adaptation, not an unapproved schema replacement

1. Keep Django/DRF/Postgres/allauth, the shared sync engine, encrypted credentials,
   server-side token ownership, first-class clients and homelab/kiosk topology.
2. Make intentional source selection and local worksheets the product baseline. Decide
   remote identity versus worksheet identity before first migrations.
3. Declare each field/action's policy: read-only remote preview, import-time copy,
   local field, continuous remote read, explicit remote command, optional automation.
   Keep all writes behind permissions and the shared rate-limited server transport.
4. Plan ordered daily work and realistic workload before calendar pinning. Model
   projections separately from committed blocks and tracked actuals.
5. Reconcile rollover and meeting checklists before building the day-state API. Neither
   a glossy planner nor a dashboard should hide contradictory lifecycle rules.
6. Include timer/time entries, channels/contexts and basic recurrence in the parity
   planning frontier, rather than calling them incidental later polish.
7. Add Today/Board/Calendar/Focus/planning surfaces alongside the dashboard. Preserve
   the retrofuturist terminal identity, readable monospace body type, amber personal
   attention, cyan external state, magenta AI, green healthy/done and red failure.
   Do not copy Sunsama branding, assets or source code.
8. Keep dashboard profiles, distance-aware TV density, Snapshot freshness, failure log,
   Obsidian journal and Telegram delivery as Cyber Beacon differentiators. They read
   the same committed/proposed/actual state as the planner, not a parallel task model.
9. Make broad provider parity and team/enterprise surfaces explicit later decisions,
   not an accidental promise to implement every connector before the first usable day.

## What still needs direct account/runtime verification

The source inventory records the documented behavior. Before claiming exact end-to-end
parity, witness (using disposable records and separately authorized remote mutations):

- Re-import the same source; rename worksheets; distinguish duplicate intent from retries.
- Close/reopen remote records and local tasks for each provider, with automations both
  enabled and disabled, including denied permission and expired grants.
- Reopen an imported email after a new reply, and test thread/message identity, imported
  filtering, account isolation, archive/label actions and delayed-send cancellation.
- Move/delete external working sessions while offline, refresh, and observe convergence.
- Test recurring event instance changes, deleted meetings, cancelled attendance and
  imported-event removal exceptions without duplicate workload.
- Cross midnight, DST, travel, weekends and a multi-day absence with unfinished work,
  tracked time, recurrence exceptions and priority resets.
- Undo/retry a partially failed export or automation and observe compensation semantics.

No client-visible evidence can by itself establish Sunsama's private server transaction
or queue implementation. Implement our own specified, testable guarantees rather than
inventing those details.
