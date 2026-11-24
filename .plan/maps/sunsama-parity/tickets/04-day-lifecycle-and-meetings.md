---
type: grilling
blocked_by: [01]
---

# Daily lifecycle, meeting checklists and progress history

## Question

**Do we adopt Sunsama midnight rollover and meeting checklists, or retain specific Cyber Beacon differences, and what is the complete day-state contract?**

F029, F031–F039, F063–F067, F082, F086 and F095. Current Sunsama docs explicitly separate shutdown from task rollover; backend 06 instead gates Backlog Bump on Wrap-up. CalendarEvent is never a Task in current CONTEXT.md.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### Decided in ticket 13

Midnight carry-forward is decided: unfinished work moves to the next day at midnight, and shutdown does not gate rollover. The remaining questions below are the full day-state contract and meeting checklists.

### To resolve

- Decide whether configurable rollover, wrap-up gating, Pending day and 24h auto-skip survive as optional differences.

- Specify prep/shutdown steps including review, gathering meetings, estimating/checking capacity, ordering, optional timeboxing and sharing. Define repeat planning, future days, evening planning and skipped days.

- Keep event identity separate but decide a linked checklist/read model; define event-occurrence dedupe, auto-import exclusions, remove-without-delete suppression and no duplicate workload.

- Specify meeting auto-completion Always/Never/Invitees with active-timer exception; handle remote cancellation/time edits, actual-time edits, no merging/subtasks and late attendance.

- Define historical day membership from actual/subtask progress, credited completion dates, archive inactivity vs backlog vs trash, counts and restoration. Contrast one-week Sunsama trash with our 30-day disconnect policy.

- Keep Postgres journal authoritative and Obsidian asynchronous. Decide highlights/mood/summary privacy and what needs remote activity history instead of latest-only Snapshots.

## Done when

- Write an explicit day-state transition table/API, historical membership rules, and scheduler actions.

- Test midnight/DST/travel/weekends/gaps, recurring occurrence collision, cancelled meeting and deletion/restore across clients.

- Amend backend 02/05/06/08/09, CONTEXT.md and glossary together after confirmation; replace the unsupported 'like Sunsama' premise without erasing history.

## Phase 1 implementation disposition (2026-11-18)

The developer authorized autonomous implementation of the entire First usable day.
[The bounded release contract](../../../../docs/phase-one-contract.md) resolves this
ticket's Phase 1 slice and supersedes conflicting historical premises for that slice.
Broader release/parity questions above remain open. Verification and any limitations
are recorded with the implementation; the packaging proof is not claimed in advance.

## Resolved so far (2026-11-18) — Decision set: day lifecycle, meetings, history

Confirmed with the developer. Mirrored in the parity-04 decision-log issue; already
settled items from 13/05 are confirmed, not re-decided.

- **04-1 Day-state contract:** explicit per-day state machine (unset -> prepped -> active
-> shutdown-resolved/{skipped|auto-skipped}), per-day per-user Postgres records (one row
per calendar day for a hole-free month log). Prep = settle yesterday, gather meetings,
estimate/check capacity (parity 05), order, optional timebox, optional share; missed if
past a per-user prep cutoff. Shutdown = review, highlights/mood/journal, publish;
resolved when done, skipped by user, auto-skipped after a limit. Evening planning for
tomorrow + future-day navigation + re-planning included. Skipping never moves tasks.
- **04-2 Rollover:** parity 13 + 05-1.4 confirmed final. Only optional knob kept is
per-user carry-forward placement (top/bottom). No auto-skip of unfinished Tasks; no
"ask tomorrow" state.
- **04-3 Meeting identity/dedupe:** key checklist entries by occurrence identity
((calendar, event-id, occurrence)); one Event-ID wins; never double-count workload for
overlapping duplicates; reuse the parity-02 Source/identity discipline. Auto-import
exclusions + Importable flag (6.4/6.2) apply.
- **04-4 Meeting lifecycle:** remote events are the source of truth; cancellation/decline
removes the entry (workload recalculated) unless manually removed (suppressed, not
resurrected); time-edit reflows but never touches actual TimeEntry or a manual
completion; auto-completion modes Always/Never/Only-with-invitees, paused while a timer
runs; no merge / no real subtasks.
- **04-5 History & archive:** completion credits the do-date day (with happened-on
annotation); past-day membership derives from do-date + activity, not current state.
Archive = soft, explicit "park it", not Backlog and not deletion. Retained trash (no
purge) is the deliberate override of Sunsama's one-week (phase-1 contract); auto-archive
is manual/opt-in only.
- **04-6 Journal & highlights:** Postgres journal authoritative, Obsidian async
(unchanged). Highlights = privacy-filtered summary from local Activity + short-lived
remote activity history only where a provider feed is connected, never from the
latest-only kiosk Snapshot. Personal/private channels excluded by default; sharing
per-action with explicit consent.

Folds into CONTEXT.md/glossary (Journal, day-state) and backend 02/05/06/08/09 when the
full set closes; 04/07 re-check coupling noted.
