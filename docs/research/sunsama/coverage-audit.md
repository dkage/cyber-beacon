# First-slice coverage audit

Maps the twelve GitHub issues (`#8`–`#19`, "First usable day") against the
[110-row feature inventory](./feature-inventory.md). Goal: confirm the slice is an
end-to-end loop, that every feature is owned somewhere, and that nothing critical
falls between "in the slice" and "explicitly deferred."

## Result summary

- **Ownership is complete.** Every `F001`–`F110` row names a parity-ticket owner
  (`02`–`12`, all open) or is settled by the baseline (`13`, resolved). No orphaned
  features.
- **The slice is coherent.** The minimal loop — create → import → estimate → order →
  capacity → track → complete → carry-forward → dashboard — is covered end to end.
- **~15 features are directly enabled** (several only partially), plus the two Cyber
  Beacon additions (kiosk dashboard, freshness/failure states).
- **One large deliberate deferral**: Sunsama's calendar projections/timeboxing. This is
  the natural next chunk, not a gap to hide.

## In the slice

| Feature family | Enabled by | Feature IDs |
|---|---|---|
| Local task, do date, notes, priority, estimate, completion | #10, #11 | F004, F010 (partial), F047 (local only) |
| Today view with manual ordering | #13 | F089 (partial), F048 (manual only) |
| Notion source browsing + explicit worksheet import | #14 | F001, F002, F006 |
| Google Calendar meetings, read-only | #15 | F050 (partial) |
| Work hours and capacity vs meetings | #16 | F033, F034 (workload only) |
| Timer, actual time, day totals | #17 | F069, F071 |
| Midnight carry-forward (baseline) | #18 | F036, F037 |
| Kiosk dashboard, stale/failure states | #19 | Cyber Beacon addition |

Foundations (`#8` scaffold, `#9` static client, `#10` domain, `#12` auth) enable the
loop but map to no single feature row; they are the platform the rows sit on.

## The one large deferral: calendar timeboxing

`F049`–`F061` — internal calendar, projections, pin-to-commit, buffers/splitting,
rescheduling, per-channel calendar targets — are all deferred to parity `05`. These are
Sunsama's scheduling heart and the reason "drag a task into a time slot" is not in the
first slice. **Recommendation:** make parity `05` the second release boundary
("Calendar planning" in the project's Release field) rather than letting it stay an
unbounded future item.

## Near-slice items needing a conscious call

These are not blockers, but their boundary deserves an explicit adopt/defer note when
their parity ticket closes:

- **Daily prep and wrap-up ritual flow** (`F031`, `F035`). The raw steps (estimate,
  order, capacity) are in-slice; the guided morning/evening flow and journal are
  deferred to parity `04`.
- **Meeting checklists** (`F063`–`F067`). Meetings are read-only in the slice; no
  completable checklist representation yet (parity `04`).
- **Priority reset semantics** (`F047`). Local priority is in-slice; daily-reset and
  persistent-backlog levels are deferred to parity `07`.
- **Already-imported flag / dedupe** (`F005`, `F009`). The baseline decided explicit
  import, but the identity/dedupe contract remains open in parity `02`.

## Traceability

The chain `GitHub issue → parity ticket → feature ID` is intact. Each issue's
"References" section points to its parity ticket(s), which own the feature rows.
Implementers start from the issue; design questions route back to the ticket.

## Verification limits

This is a planning-coverage audit, not a code review. The production backend and
frontend are not yet written; "in the slice" means an issue exists that must deliver the
behavior, not that it is implemented. Confidence in the inventory itself is scoped by
[README.md](./README.md): first-party documentation plus desktop inspection, no
authenticated mutations or private-backend observation.
