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
