---
type: grilling
blocked_by: [01]
---

# Channels, contexts, daily priority and weekly objectives

## Question

**Which organizational concepts make planning useful without turning Cyber Beacon into another project manager?**

F034, F040–F048. Current local priority is one small int; Project and block categories were deferred. Sunsama has channels/contexts, separate daily/backlog priority and weekly objectives, not an upstream issue board.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Define Channel and Context separately from Connection/Mount and Project; task/objective membership, filters/default creation/import precedence, disable/delete and personal/private semantics.

- Define personal work's exclusion from work capacity while still occupying real clock time; channel-based calendar routing co-owned with scheduling ticket 05.

- Choose daily priority reset/rollover levels vs persistent backlog priority, local vs upstream fallback and sorting ties.

- Define Weekly objective identity, week anchoring, notes, completion, extensions/carry-over and task linkage without deleting Tasks or inventing project status.

- Define weekly planning/review target week, combined flow, weekend settings, summaries, manual vs suggested task alignment and historical time allocation.

- Reconcile channel color with Cyber Beacon semantic colors and kiosk privacy; category tint must not change the meaning of failure/AI/external state.

## Done when

- Record vocabulary/cardinalities and examples spanning work/personal channels and an objective extended two weeks.

- Specify filter and time aggregation semantics, objective deletion/unlink and priority reset without losing persistent urgency.

- Update backend 02/03/06 implications, CONTEXT.md and glossary after approval; do not call this a Project schema by assumption.

## Resolved so far (2026-11-18) — Decision set: channels, priorities, weekly objectives

Confirmed with the developer. Mirrored in the parity-07 decision-log issue.

- **07-1 Channel & Context model:** Channel = per-user label on a Task/Objective;
Context groups channels. Single channel per task (nullable). Assignment precedence:
explicit > import/channel rule > user default > unset. Disabling keeps tasks (they
surface as "no channel"); deleting never deletes tasks. Not a Project/board schema and
not a Connection/Mount.
- **07-2 Personal channels:** a per-channel personal/private flag drives parity-05
2.4/6.1/6.3 — excluded from work-capacity, still occupies real clock time, routes/binds
to a calendar, publishes private, redacted on the kiosk. Single source of truth those
decisions reference.
- **07-3 Priority:** adopt daily priority (today's ordering intent, per-day resettable)
separate from persistent backlog priority (urgency); prefer two distinct fields.
Upstream fallback only when local unset; auto-sort tie-break: running > fixed-clock >
pins > backlog priority > do-date > created. Reset opt-in per day, never destructive.
- **07-4 Weekly objective:** its own per-user entity (target week, channel, notes,
optional local completion, derived progress). Carry-over keeps notes + links; unlinking
never deletes a Task; progress derived, no status column. Never a Project or parent Task.
- **07-5 Weekly ritual:** target week, optional combined daily+weekly flow, per-user
weekend setting, privacy-filtered summary, task alignment suggested but explicitly
accepted (consistent with 1.1); historical time allocation a derived aggregate across
actuals by channel/objective.
- **07-6 Colors/privacy:** channel color an optional tint on non-semantic surfaces only,
never overriding global semantic colors (amber/cyan/magenta/green/red). Personal
channels render neutral/redacted on the kiosk.

Folds into CONTEXT.md/glossary (Channel, Context, Weekly objective, daily vs backlog
priority) and backend 02/03/06 when the full set closes.

## Parity 05 re-check (2026-11-18)

Both parity-05 blockers' material is now settled: meeting-checklist day-lifecycle detail
(parity 04 set) and channel personal flag + channel->calendar binding (this parity 07
set). Parity 05 is treated as closed pending CONTEXT/glossary/backend fold-in.
