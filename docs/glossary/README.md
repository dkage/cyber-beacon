# Glossary

A quick-reference lookup for the terms this project has settled. It is an index, not a
source of truth.

**Authority.** [`CONTEXT.md`](../../CONTEXT.md) owns domain vocabulary, including the
`_Avoid_` synonyms. The [ADRs](../adr/) own architectural decisions. If anything here
drifts from them, they win. Fix this file.

| File | Covers |
|---|---|
| [domain.md](./domain.md) | Work, time, and provenance terms (Task, Do date, Mount, Source…) and the daily rhythm (Prep, Wrap-up, Bump) |
| [entities.md](./entities.md) | Model names, their key fields, and the per-user settings |
| [integrations.md](./integrations.md) | Provider interface, capabilities, sync engine, rate budget, health states |
| [background-work.md](./background-work.md) | Queue, scheduler, workers, retries, `JobRun` |
| [architecture.md](./architecture.md) | Stack, deployment, API conventions, infrastructure names |
| [sunsama-reference.md](./sunsama-reference.md) | Reference-to-domain translation and explicitly unsettled parity decisions; not settled new models |

Each entry gives a one-line meaning and where it was decided. Ticket references are to
`.plan/maps/backend-architecture/tickets/` unless explicitly labelled **parity**; those
refer to `.plan/maps/sunsama-parity/tickets/`. The [reference audit](../research/sunsama/README.md)
flags behavioral premises under review; retain current definitions until an approved
answer updates `CONTEXT.md` and this index.

**Maintenance:** any change to a plan, ADR or `CONTEXT.md` needs a check of this
glossary in the same commit.

