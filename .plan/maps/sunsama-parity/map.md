# Sunsama-shaped planning, Cyber Beacon identity

## Destination

A product specification that follows Sunsama's planning workflows closely, explicitly
accounts for every feature in the reference inventory, and keeps Cyber Beacon's own
identity, API-first architecture and dashboard. Every difference is adopted, adapted,
deferred or rejected deliberately; no backend migration or frontend brief relies on an
unexamined claim of parity.

## Notes

**User direction.** Use Sunsama as the behavioral starting point, with our identity and
added dashboard. This does not authorize blindly cloning proprietary code/assets, copying
private server architecture, requiring AI, or implementing every enterprise feature first.

**Required reading.** `CLAUDE.md`, `CONTEXT.md`, applicable ADRs, the
[backend architecture map](../backend-architecture/map.md), and the
[reference audit](../../../docs/research/sunsama/README.md). The
[110-row feature inventory](../../../docs/research/sunsama/feature-inventory.md) is the
coverage checklist; [integration semantics](../../../docs/research/sunsama/integration-semantics.md)
is the provider-specific source, not “everything syncs both ways.”

**This map decides; it does not build.** Buildable work goes to GitHub Issues after the
relevant decisions close. No production code changes or fabricated implementation status.
Use the repository's grilling workflow to confirm choices; facts come from the audit,
not questions the developer must answer from memory.

**Authority and reopening.** Backend tickets 02/03/06/08 remain historical settled
answers. This audit identifies contradicted premises, not approval for a replacement
schema. Before building affected slices, resolve this map's relevant ticket and amend
`CONTEXT.md`, the backend answer and glossary together. Until then the existing vocabulary
wins, but affected behavior is **under review, not ready for implementation**. Do not
remove chartr claims or reuse ticket identities. Cross-map dependencies below are prose
links because numeric `blocked_by` IDs are local to one map.

**Adoption order recommendation.** Manual source-selection → daily capacity/order →
projections/timeboxing → actuals/focus → recurrence/week/backlog → optional AI drafting.
Start connectors with Notion and Google Calendar, then real-use mail/GitHub/Outlook.
Provider breadth and collaboration are a separate disposition, not a prerequisite to a
usable personal planner. Final release boundary is decided in ticket 12.

**Identity and differentiators stay.** Retrofuturist terminal chrome, legible monospace
body text, amber attention, cyan external state, magenta AI, green healthy/done, red
late/failure. Five viewing profiles and TV distance calibration; no dense desktop layout
scaled up to a wall. Keep Snapshot freshness, failure visibility, Obsidian journal, Telegram
and future agent execution. The dashboard and planner consume one domain, not two.

**No private dependency.** The existing dashboard brief covers the dashboard, not the
planner. Its needed constraints are summarized here; any eventual spec must stand alone.
No committed document may depend on a private scratch path.

## Decisions so far

- [Reference audit and product direction](./tickets/01-reference-baseline.md) — REA inspected the installed desktop and captured 80 public-manual URLs; 110 feature rows plus provider rules identify gaps. Sunsama-shaped behavior is the product baseline, while individual reversals remain decisions, not assumed approval.

## Not yet specified

- **Source admission and worksheet identity.** Candidate browsing/import vs continuous Task projection; multiple worksheets, local retitles, URL and email identities. Affects backend tickets 02/03/08. <clears-with: 02>
- **Per-provider sync and commands.** Field directions/import copies, source preview edits, import/completion automations, scopes, export/copy, retries and data retention. Affects backend 02/03/08 and Microsoft scope feasibility. <clears-with: 03>
- **Day lifecycle, meetings and history.** Midnight rollover vs wrap-up Bump; progress breadcrumbs, imported meetings, suppression, archive/trash and journal. Affects backend 02/06/08/09 and worker sweeps. <clears-with: 04>
- **Scheduling and capacity.** Ordering, work hours, workload, deterministic projections vs committed blocks, split/auto-reschedule, local calendars and channel-target routing. Affects backend 02/03/06. <clears-with: 05>
- **Actual time and focus.** Timer state, manual corrections, day totals, inferred actual, Parallel overlap and breaks. Previously deferred TimeEntry now has an explicit parity owner. <clears-with: 06>
- **Organization and weekly intent.** Channels/contexts, personal privacy/capacity, daily vs backlog priority and weekly objectives/rituals. Not a generic project-board substitution. <clears-with: 07>
- **Recurrence and backlog.** Series/exceptions, rough/rigid times, rollover dedupe, backlog horizons/folders and archive review. <clears-with: 08>
- **Planner surfaces and interactions.** Today/Board/Calendar/Focus/rituals alongside the dashboard; task/search/create/merge, keyboard and touch. This is absent from the dashboard-only brief. <clears-with: 09>
- **AI and MCP boundaries.** Briefing vs suggestion vs Autoplan vs Sunny vs external execution; change review/undo and two MCP directions. Co-own sequencing with backend ticket 10, not a competing briefing implementation. <clears-with: 10>
- **Capture, delivery and client scope.** URL/deep links, forwarded email, Slack/Teams/Telegram, reminders, focus bar, mobile and offline limits under WireGuard. Co-own backend 09/11/12 constraints. <clears-with: 11>
- **Release disposition and breadth.** Assign every feature/provider to now/later/not planned; resolve email-client depth, conferencing, time export, collaboration/enterprise and privacy scope. <clears-with: 12>

## Out of scope

- Replacing Django/DRF/Postgres/allauth, credential encryption or first-class-client ownership.
- Copying Sunsama's assets, code, proprietary branding or undisclosed backend internals.
- Production implementation, automated changes to the developer's Sunsama records, and
  destructive/send-mail runtime experiments without a separately scoped test plan.
- A promise to build a native desktop shell, mobile app, team SaaS or every connector in v1.
