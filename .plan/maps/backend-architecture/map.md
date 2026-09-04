# Backend architecture and domain model

## Destination

Locked architectural decisions plus a domain spec the first backend vertical slice can be built against — the point where someone can start writing Django code without another decision needing to be made first.

## Notes

**Domain.** Personal productivity scheduling, Sunsama-shaped: pull tasks from integrations, drag them onto a day timeline that syncs to the calendar, generate an AI briefing from the finalised schedule. The secondary surface is an always-on kiosk dashboard. The full product brainstorm and the frontend design brief are private notes the developer holds; anything a ticket depends on is quoted into that ticket rather than referenced by path.

**This map plans, it does not build.** Every ticket resolves a decision. No production code is produced here.

**Skills.** Use `grill` every session, and a domain-modeling skill where one is available.

**This map is canonical.** The effort was first charted as GitHub issues — `dkage/cyber-beacon#2` and `#3`–`#7` — before the chartr convention was adopted. Those issues are closed and must not be reopened: planning lives here, and only work with a diff belongs in the issue tracker.

### Settled architecture

Decided before this map existed — the premise of the route, not steps along it. **`CLAUDE.md` holds the current stack and architecture; `docs/adr/0001-django-owns-identity.md` holds the identity-ownership decision and the alternatives rejected.** Read both before working any ticket; they are authoritative and this map does not restate them.

**`CONTEXT.md` at the repository root is the authority on domain vocabulary**, produced by ticket 02. Use its terms — in tickets, issues, models and routes — and do not drift to the synonyms it lists under `_Avoid_`.

### Standing constraints

- **Hardware.** An 8GB Raspberry Pi 5 drives a 4K TV as the always-on kiosk; a 64GB Xeon TrueNAS homelab is also available. Which hosts the backend is undecided — see the deployment ticket.
- The multi-user structure, first-class-client, and sign-in-vs-connect constraints are recorded in `CLAUDE.md`.

## Decisions so far

<!-- one gisted, linked line per resolved ticket -->

- [Record the settled stack in CLAUDE.md and ADR-0001](./tickets/01-record-settled-stack.md) — `CLAUDE.md` now describes the Django stack and the two-tracker rule; identity ownership recorded as [ADR-0001](../../../docs/adr/0001-django-owns-identity.md).
- [The domain model: do-date, due-date, and what a Task is](./tickets/02-domain-model.md) — `Task` carries three independent **local dates** (do, due, start) and no status; a separate `TimeBlock` holds the **instants**. Mirrored fields belong to upstream and are read-only, local fields are never touched by sync, and completion stays local. Vocabulary recorded in [`CONTEXT.md`](../../../CONTEXT.md).
- [The integration provider abstraction](./tickets/03-integration-provider-abstraction.md) — providers are **thin adapters** over one shared sync engine, differing only by a declared **capability** set; `IntegrationConnection` is independent of allauth ([ADR-0002](../../../docs/adr/0002-integration-connections-separate-from-identity.md)) and credentials are encrypted at rest ([ADR-0003](../../../docs/adr/0003-credential-encryption-at-rest.md)). A **Mount** is one remote resource under a Connection, carrying its own cursor and field mapping. Polling is the baseline and push only accelerates it; calendar write-back resolves conflicts by `If-Match` with the remote winning.

## Not yet specified

- **Offline client versus server concurrency.** [Ticket 03](./tickets/03-integration-provider-abstraction.md) settled how *this server* resolves a conflict with *a provider*. It did not settle how a client that was offline — the contemplated Swift app, holding a drag it could not send — replays a stale mutation against our own API. That is our own concurrency control on our own resources, and it will be discovered during a client build and retrofitted badly if left here.
- **A trash bin for Tasks generally.** Disconnecting a Connection can soft-delete the Tasks it sourced, recoverable for thirty days. Whether *every* Task deletion works that way is a Task-lifecycle decision that ticket 03 deliberately did not make on the domain model's behalf.
- **AI briefing architecture.** What triggers generation, how context is assembled, which model, what it costs per run, and where the output lives.
- **Agent-executed tasks.** The n8n / Hermes dispatch described as "Development 2" in the brainstorm — a task the AI can perform on the user's behalf, triggered from the briefing.
- **Notification system.** Telegram, email, and the TV's attention/alerting model for overdue work and skipped daily prep.
- **Widget data contracts.** What the dashboard actually asks the API for, per widget, and at what refresh cadence.
- **Daily-prep flow mechanics.** The morning ritual itself as a sequence of steps, including the previous day's wrap-up and its Obsidian journal write. <clears-with: 06>

## Out of scope

- **Frontend design and build.** Already specified in full in a separate design brief the developer holds — design tokens, five viewport profiles, widget catalog, mock data layer. Not fog; charted elsewhere.
- **The Swift iOS app.** The API is designed so it can exist; building it is a separate effort and is not confirmed.
- **Kiosk hardware setup.** TV mounting, orientation, and Pi provisioning.
