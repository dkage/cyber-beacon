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

## Resolved so far (2026-11-18) — Decision 1: daily ordering

Worked through with the developer one decision at a time. Adopted positions are
recorded here and still need folding into `CONTEXT.md` and the glossary when the full
decision set for this ticket settles. Dependencies on tickets 04 (day lifecycle) and
07 (channels/priorities, personal-work exclusion) must be re-checked at close.

- **1.1 Who sets order:** Blend — per-day, per-user server-persisted order, freely
draggable; optional pins that survive re-sort; **auto-arrange is an explicit user
action**, never silent background re-sort. New days: carry prior order; auto-suggest
shown but applied only on accept. (Order of the day is a row-level concept as in Phase 1.)
- **1.2 Special-task precedence:** running/started task is always "next" for projection
(its row is not moved), fixed clock-time tasks anchor like meetings (nothing placed
over them, one gesture un-anchors), pinned tasks win, then others by estimate-desc and
priority. Auto-sort precedence: running > fixed > pins > estimate-desc > priority.
- **1.3 Concurrency:** reuse the Phase-1 row-lock + versioned whole-day reorder as the
sole ordering write path (auto-sort, midnight sweep, import all route through it);
record order changes as semantic Activity (per-day, per-user).
- **1.4 Where order lives:** per-day, per-user, server-persisted. Carry-forward places
unfinished work at top by default in original relative order, with a bottom-placement
setting; consecutive-day badge derived from Activity, not stored.

## Resolved so far (2026-11-18) — Decision 2: capacity

- **2.1 Work window:** per-weekday work hours + optional shutdown time + one-day
overrides + whole-day unavailable flags + optional channel overrides. Generalize Phase
1's single window to per-weekday. Shutdown is an informational/hard-scheduling boundary
that never gates carry-forward (consistent with the midnight rollover baseline, parity
13). Channel override wiring depends on decision 7.
- **2.2 Workload threshold & predicted finish:** derive predicted-finish by walking
committed sessions weighted, in current order; show finish vs shutdown. Advisory, never
blocking. Workload threshold = planned work vs window (minus meetings); personal work
excluded. Feeds auto-schedule overcommit choices (decision 5). No fudge factors in v1.
- **2.3 Missing estimates:** projection/finish-time use a configurable default duration
(default 30m; 15/30/45/60 options); always show "+ N unestimated" separately. Strict
over-capacity threshold uses real estimates only; projected finish uses real + default.
- **2.4 Personal vs work capacity:** personal/private is excluded from work-capacity
arithmetic and workload thresholds but still occupies calendar time and constrains
scheduling. Tagging source = channel/calendar "personal" flag (decisions 6/7). Actual /
completed time is always real and unaffected.

## Resolved so far (2026-11-18) — Decision 3: projections vs committed blocks

- **3.1 Projection is a derived read-model, not a stored entity.** Computed from
committed inputs (order, remaining estimates, work hours, blocking meetings) with a
deterministic algorithm, exposed via a read endpoint, labeled preview. No projection
row is persisted as a TimeBlock; a cached snapshot for kiosk freshness is never a
committed block.
- **3.2 Deterministic recipe:** walk ordered remaining work (real estimate minus
tracked actual), fit into work window minus blocking meetings, never past shutdown.
Parallel tasks share projected intervals; Focused breaks the sequence; running timer
first; fixed clock times anchor (per Decision 1).
- **3.3 Explicit commit only.** Viewing/ordering/projecting writes nothing. Only pin /
commit / drag creates a working session (TimeBlock) on its calendar target. Per audit
(F053/F054): projection never creates an external event and never commits by itself.
- **3.4 Freshness:** recompute on authoritative server state, debounced per user
interaction; commit re-reads the current projection atomically before locking (never
pin a stale preview); kiosk shows last-good projection with computed-at freshness.

## Resolved so far (2026-11-18) — Decision 4: pin-to-commit & undo

- **4.1 Commit mechanics:** commit creates one working session per pinned projection
slot; many sessions per task across days allowed; session resize updates planned time
and re-projects the remainder, never actuals. Plain pin uses the projection; a
modifier key = one-block/no-split override. Targets resolve per Decision 6 (internal
default -> channel -> tasks calendar).
- **4.2 Intended plan preserved:** every commit/resize/move/undo writes a semantic
Activity record of the intended plan; actuals (TimeEntry) never modify or replace
planned session history. Planned-vs-actual reporting reads both streams; a
rearrangement is a first-class event (who/what/when/from->to).
- **4.3 Undo contract:** version-checked inverse patch through the Phase-1 row-lock /
precondition write path; atomic per change-set; scoped so it never reverts unrelated
edits; distinct "undo whole run" command for runs; conflict with newer local edits ->
surface and ask, never clobber.
- **4.4 Boundary invariants:** commit never writes remotely by default; never
moves/edits meetings; never places sessions in the past; ambiguous projections route
to explicit choices (Decision 5), never silent decisions.
