---
type: grilling
blocked_by: [04, 07]
---

# Capacity, ordered work, projections and committed time

## Question

**How does a realistic daily task list become a fluid projection or a committed calendar plan?**

F003, F031, F033–F034, F046, F048–F062, F073. Backend 02/03 have TimeBlock and a single publish target but no persisted order, workload or projection contract.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Define daily task ordering/manual pins/auto-sort and running/fixed-task precedence with concurrency-safe reorder operations.

- Define work hours per weekday/channel/day, unavailable days, shutdown, workload threshold, missing estimates, personal exclusions and meeting counting exactly once.

- Introduce a derived task-projection read model distinct from TimeBlock and TimeEntry; deterministic remaining-time placement, no remote writes, clear unplaced/overcommitted output.

- Define pin/auto-schedule commands, buffers, split limit/one-block override, no scheduling into past, overtime/next-day/defer choices and explicit preview/undo.

- Specify rescheduling only owned sessions, early-finish contraction and dependent moves; preserve the original intended plan in Activity rather than using actual time to rewrite history silently.

- Revisit single publishing Mount: internal local calendar, channel routes, task-default vs event-default, privacy/free-busy/reminders. Calendar visibility, importability and blocking are independent; local overrides must not patch remote busy state.

- Clarify date-vs-instant rules, day estimates vs cumulative estimates vs block totals, external calendar races, event CRUD/conferencing depth and Parallel scheduling.

## Done when

- Write deterministic scheduling inputs/outputs, capacity arithmetic and all calendar-target/override precedence.

- Define API preview/commit/undo and conflict behavior; retain engine ownership, rate limiting and source-token isolation.

- Pass examples with 2h task split by meeting, personal task routing, hidden non-blocking calendar, zero estimate, overtime, overlapping owned sessions and DST; amend backend 02/03/06 and glossary.

## Phase 1 implementation disposition (2026-11-18)

The developer authorized autonomous implementation of the entire First usable day.
[The bounded release contract](../../../../docs/phase-one-contract.md) resolves this
ticket's Phase 1 slice and supersedes conflicting historical premises for that slice.
Broader release/parity questions above remain open. Verification and any limitations
are recorded with the implementation; the packaging proof is not claimed in advance.
