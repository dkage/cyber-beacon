# Integrations

Source: ticket 03, [ADR-0002](../adr/0002-integration-connections-separate-from-identity.md),
[ADR-0003](../adr/0003-credential-encryption-at-rest.md).

## The rule

**Adapters are thin; the engine is the only thing that writes.** An adapter speaks HTTP
and translates payloads, with no loop, transaction or `save()`. An `if provider ==
"notion"` in the engine means the abstraction has failed.

| Term | Meaning |
|---|---|
| **Sync engine** | The one shared orchestrator. Owns loops, transactions, cursor checkpoints, and the single `save(update_fields=MIRRORED_FIELDS)` |
| **Adapter** | A provider's file: pagination, property types, error mapping. Gets its HTTP client from `ctx` and never builds one |
| **Capability** | A declared flag. `READ INCREMENTAL WRITE_BACK WEBHOOK MAPPABLE NOTIFY REVOKE`. The engine branches on these, never on provider identity |
| **`ctx`** | What the engine hands an adapter, including the rate-limited HTTP client |
| **`fetch`** | Yields pages (records, tombstones, next cursor) so the cursor checkpoints mid-sync. May not make per-record requests (no N+1) |
| **`project`** | Pure function turning a record plus mapping into mirrored fields. No DB |
| **`classify`** | Adapter error taxonomy: `retryable`, `rate_limited`, `auth_dead`, `cursor_invalid`, `fatal` |
| **`RatePolicy`** | Adapter-declared limits: req/s, burst, page size, retry ceiling |

## Sync behaviour

| Term | Meaning |
|---|---|
| **Cursor** | Opaque per-Mount checkpoint (Google `syncToken`, Notion `last_edited_time`) |
| **Cursor rejected** | Expected, not a disaster: clear it, run a full sync, reconcile by `external_id`. Same path as the first sync |
| **Tombstone** | `deleted_upstream_at`. Records missing from a full sync are tombstoned, never deleted |
| **`last_attempted_at` vs `last_succeeded_at`** | Two columns on purpose. The UI shows the second, so a failing Mount never reads as "synced just now" |
| **Polling baseline** | Every provider polls. A `WEBHOOK` only shortens the interval and enqueues the same sync. It carries no data. Currently off (no public URL) |
| **Rate scope** | A string the adapter names (`notion:ws:abc123`, `google:conn:42`). The token bucket is keyed by it, not by Connection. Enforced in the engine's HTTP client, stored as a Postgres row (ticket 05) |
| **Publish target** | The one Mount per user where Time blocks are written. A partial unique index enforces "at most one". Defaults to the connection's primary calendar |
| **Mapping** | Per-Mount field map keyed by property id, validated on write against a live `describe_schema` |

## Task or widget (ticket 08)

| Term | Meaning |
|---|---|
| **`SUMMARIZE`** | Capability: the adapter can produce a Snapshot. Added to the set from ticket 03 |
| **`summarize`** | Pure adapter method, beside `project`. The engine writes the result |
| **Dual purpose** | Per **Mount**: `mirrors=true` projects Tasks, `mirrors=false` is Snapshot only. Every Mount writes a Snapshot |
| **Mount cap** | Per-Mount ceiling on open projected Tasks (~200). Past it the engine stops projecting, warns, and still counts the overflow |
| **First-sync preview** | A new Mount shows a count and needs confirmation before projecting |
| **Tombstone reason** | `resolved` completes the Task (actor: the integration, local write only). `withdrawn` tombstones it and leaves it open |
| **Promotion** | Manual widget-item-to-Task. Needs a stable `external_id` and `url`. Then follows the normal sync path |

## Connection health

`status`: `active` / `needs_reauth` / `disabled` / `disconnected`.

| Term | Meaning |
|---|---|
| **`needs_reauth`** | Dead refresh token. Mounts stop being enqueued, other Connections keep syncing, synced data stays visible marked stale |
| **Re-authorisation** | Updates the existing row (keeps Mounts, mappings, cursors) and refuses an `account_identity` mismatch |
| **Disconnection** | Not deletion: wipes credentials, keeps Tasks and Sources. Reconnecting the same identity adopts the existing Sources |
| **Soft delete** | Optional on disconnect: `deleted_at` on sourced Tasks, purged after 30 days, restored by reconnecting inside the window |

## Calendar write-back

- Every write sends `If-Match` with the stored ETag. On `412` the **remote wins**: the
  local Time block is updated and a `TaskActivity` records the move.
- Remote wins on **time and existence only**. Local fields are never overridden.
- A remotely deleted event we authored deletes the `TimeBlock` and keeps the `Task`.
- Our events are stamped with `extendedProperties.private` to tell them from meetings.

## Unobtainable Connections

Source: ticket 07, [research](../research/microsoft-entra-app-registration-and-consent.md).

- A tenant may refuse **consent** (not app registration) before any Connection exists.
  This is the result of a connect attempt, not a `status`. The UI says an administrator
  must approve, as an expected outcome.
- All Microsoft consent and token failures classify as `auth_dead`; `last_error` carries
  whether an admin (`AADSTS90094`/`65001`) or only the user (others) can fix it.
- One Microsoft app registration (personal + work audience) serves every Outlook Connection.

## Non-sync Connections

Telegram declares `{NOTIFY}` only, and Obsidian holds a path in its credential blob.
Both use the same `IntegrationConnection`. With no `READ`, the engine never enqueues
them.
