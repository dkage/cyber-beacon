---
type: grilling
blocked_by: [04, 05]
---

# Actual time, timers, focus and parallel work

## Question

**What state and arithmetic make actual time trustworthy across days, devices and overlapping work?**

F038, F055, F069–F074, F077 and F088. TimeEntry was named but deferred in backend 02; parity now needs an owned specification, not Task started_at/finished_at columns.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Specify TimeEntry and running timer state, start/pause/resume/stop, task/subtask totals and multi-device idempotency/version checks.

- Define per-day and cumulative totals, cross-midnight splitting/attribution, retrospective correction/move/delete, no future time and running-entry edit validation.

- Decide planned-as-actual opt-in; preserve measured/manual/inferred provenance and avoid meeting/task/subtask double counting.

- Decide whether Parallel is initial scope; if adopted, adjacent planned runs take max duration, overlapping timers split elapsed time evenly, and Focused stops others. Keep implementation extensible if deferred.

- Specify focus current/next progression, completion timer behavior, breaks, Pomodoro counters vs work actuals and forgotten-timer recovery.

- Scope time-export events for Toggl later without claiming past-day bidirectional sync.

## Done when

- Write arithmetic examples, storage invariants and versioned timer/correction APIs.

- Test two clients starting/stopping, same command retry, sleep/reboot, DST/midnight, subtask roll-up, Parallel overlap and inferred actual distinction.

- Add settled terms/models to CONTEXT.md and glossary and remove the relevant backend 02 deferral only with approval.

## Phase 1 implementation disposition (2026-11-18)

The developer authorized autonomous implementation of the entire First usable day.
[The bounded release contract](../../../../docs/phase-one-contract.md) resolves this
ticket's Phase 1 slice and supersedes conflicting historical premises for that slice.
Broader release/parity questions above remain open. Verification and any limitations
are recorded with the implementation; the packaging proof is not claimed in advance.

## Resolved so far (2026-11-18) — Decision set: actual time, timers, focus & parallel

Confirmed with the developer. Mirrored in the parity-06 decision-log issue. Blockers
04/05 are now resolved.

- **06-1 TimeEntry & timer state:** keep the one-running-timer invariant (Phase 1);
versioned timer/correction API (If-Match like Task) + per-device idempotent command key.
Tasks and subtasks can each be timed; a parent total is its own actuals, never silently
rolled up from subtasks.
- **06-2 Totals & attribution:** per-day total = entries intersected with local-day
boundaries (DST/midnight); cumulative per-task = its own entries; cross-midnight entries
split by intersection to both days. Corrections versioned (#26); no future time; running
entry editable only by stop/correct.
- **06-3 Planned-as-actual & provenance:** planned-as-actual = optional inferred
fallback (default off) on completion when nothing tracked; every entry carries
provenance measured/manual/inferred; no-double-count invariant (meeting checklist time
and a matching TimeEntry never both add; subtask roll-up explicit only).
- **06-4 Parallel:** deferred with semantics recorded now (adjacent planned runs take
max duration for workload; overlapping tracked timers split elapsed evenly; Focused
stops others) so a later parallel schema needs no migration.
- **06-5 Focus & breaks:** breaks/Pomodoro are attention/UI timers, never TimeEntries;
focus progression completes the current task by stopping its timer and advancing to next;
forgotten-timer recovery = surface running timer + versioned stop/correct (#26).
- **06-6 Toggl export:** explicit later boundary — event-based actual export
(channel->project/tag map), today-only corrections, no past-day bidirectional sync.

Folds into CONTEXT.md/glossary and removes the backend 02 TimeEntry deferral with
approval; supplies acceptance for #26/#44/#45.
