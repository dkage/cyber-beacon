# Sunsama reference translation and decision status

This index prevents reference-language from silently changing our settled domain.
Authority remains [`CONTEXT.md`](../../CONTEXT.md) and the ADRs. Reference findings:
[audit](../research/sunsama/README.md), [integration rules](../research/sunsama/integration-semantics.md).
Decision owners: [parity map](../../.plan/maps/sunsama-parity/map.md).

## Translate, do not alias blindly

| Sunsama term | Cyber Beacon meaning / status |
|---|---|
| Start date | **Do date**, the day of intended work. Never map it to our earliest-actionable Start date |
| Worksheet | A Task imported from a remote record; a personal copy whose local fields are yours. Decided (parity 13) |
| Working session | Our **Time block**, committed planned clock time. Decided (parity 05): many sessions per task across days; resize re-plans, never actuals |
| Task projection | Fluid, deterministic calendar preview, not a committed Time block or Time entry. Decided (parity 05): derived read-model, explicit commit only |
| Meeting checklist | Local read-model of a Calendar event on the day's list; auto-complete paused by a running timer; remove-without-delete. Decided shape (parity 05); day-lifecycle detail in parity 04 |
| Actual time | Our **Time entry** concept. Storage, timer rules, corrections and totals await parity 06 |
| Channel / Context | Reference grouping and personal/privacy/capacity semantics; not our Connection or Mount. Decided (parity 07): per-user Channel label + Context grouping; personal flag drives capacity/routing |
| Weekly objective | Reference weekly intent with linked work and notes; not automatically a Project or parent Task. Decided (parity 07): its own entity, target week, derived progress, carry-over |
| Rollover | Reference midnight carry-forward. Adopted as our **Carry-forward** (parity 13) |
| Archive | Reference inactivity holding area. **Not Backlog or trash/deletion**. Choice: parity 04/08 |
| Source candidate / import | Browse remote records without creating Tasks; explicit admission. Decided (parity 13); identity/dedupe detail in parity 02 |
| Remote action / automation | Reference explicit command or import/completion side effect. **Not a mirrored field write by the reader**. Policy: parity 03 |
| Autoplan / Sunny | Reference AI drafting / conversational assistant. Neither equals our post-plan briefing nor external task execution. Decision: parity 10 with backend 10 |
| MCP server / AI Connected App | External assistant → our planning data / our assistant → another tool; opposite trust directions, both require separate decisions in parity 10 |

## Existing decisions superseded by the baseline

Backend tickets **02/03/06/08** keep their historical answers, but four behaviors are
reversed by [parity ticket 13](../../.plan/maps/sunsama-parity/tickets/13-baseline-reversals.md):

- Automatic Task projection → **explicit import** of local worksheets.
- Generic upstream `resolved` completing a Task → **local completion**; remote actions are separate.
- Wrap-up-gated Backlog Bump and Pending-day pinning → **midnight carry-forward**.
- Mirrored title/due-date ownership → **local worksheet fields** with a source preview.

Still open (not yet decided): recurrence, AI boundaries, and the per-field/action
matrix. Calendar routing, capacity/projections, pin-to-commit and auto-schedule are
settled in parity 05 (Decisions 1–6); the day-state/meeting-checklist contract and
journal in parity 04; channels/contexts, daily-vs-backlog priority and weekly
objectives in parity 07.

Django identity ownership, credential encryption, shared orchestration, first-class
clients, durable kiosk Snapshots and the deployment stack are not reversed by a
behavioral reference audit. Product terms become settled only when their ticket,
`CONTEXT.md` and affected glossary entries are amended together.
