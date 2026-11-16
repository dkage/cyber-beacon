# Sunsama reference translation and decision status

This index prevents reference-language from silently changing our settled domain.
Authority remains [`CONTEXT.md`](../../CONTEXT.md) and the ADRs. Reference findings:
[audit](../research/sunsama/README.md), [integration rules](../research/sunsama/integration-semantics.md).
Decision owners: [parity map](../../.plan/maps/sunsama-parity/map.md).

## Translate, do not alias blindly

| Sunsama term | Cyber Beacon meaning / status |
|---|---|
| Start date | **Do date**, the day of intended work. Never map it to our earliest-actionable Start date |
| Worksheet | Reference description of a personal task linked to a remote record. Local title/field ownership and repeated imports are under review in parity 02, not a settled new entity |
| Working session | Our **Time block**, committed planned clock time; estimate/day allocation coupling under review in parity 05 |
| Task projection | Fluid, deterministic calendar preview, not a committed Time block or Time entry. Proposed read-model contract: parity 05 |
| Actual time | Our **Time entry** concept. Storage, timer rules, corrections and totals await parity 06 |
| Channel / Context | Reference grouping and personal/privacy/capacity semantics; not our Connection or Mount. Adoption/model: parity 07 |
| Weekly objective | Reference weekly intent with linked work and notes; not automatically a Project or parent Task. Decision: parity 07 |
| Rollover | Reference midnight carry-forward. **Not our Bump** (clears do date into Backlog). Choice: parity 04 |
| Archive | Reference inactivity holding area. **Not Backlog or trash/deletion**. Choice: parity 04/08 |
| Source candidate / import | Browse remote records without creating Tasks; explicit admission. Existing Promotion is narrower. Contract: parity 02 |
| Remote action / automation | Reference explicit command or import/completion side effect. **Not a mirrored field write by the reader**. Policy: parity 03 |
| Autoplan / Sunny | Reference AI drafting / conversational assistant. Neither equals our post-plan briefing nor external task execution. Decision: parity 10 with backend 10 |
| MCP server / AI Connected App | External assistant → our planning data / our assistant → another tool; opposite trust directions, both require separate decisions in parity 10 |

## Existing decisions explicitly under review

Backend tickets **02/03/06/08** keep their historical answers. They must not be presented
as verified Sunsama parity or implemented as finalized reference behavior until the
relevant parity decisions settle:

- Default automatic Task projection and global mirrored title/due-date ownership.
- Generic upstream `resolved` causing personal Task completion.
- Wrap-up-gated Backlog Bump and Pending-day pinning claimed to be “like Sunsama.”
- Calendar events excluded from all checklist work and promotion.
- One calendar publishing target per user rather than per-channel routing/local fallback.
- Deferred actual-time/recurrence and absent capacity/order/projection/weekly contracts.

Django identity ownership, credential encryption, shared orchestration, first-class
clients, durable kiosk Snapshots and the deployment stack are not reversed by a
behavioral reference audit. Product terms become settled only when their ticket,
`CONTEXT.md` and affected glossary entries are amended together.
