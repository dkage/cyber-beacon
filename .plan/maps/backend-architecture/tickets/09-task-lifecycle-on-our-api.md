---
type: grilling
blocked_by: [02, 03]
---

# Task lifecycle on our own API: stale writes and deletion

## Question

**How does our API protect a Task or Time block from a stale write, and what does deleting
one mean?**

Two questions that both add columns to `Task` and so must be settled before its first
migration.

[Ticket 03](./03-integration-provider-abstraction.md) settled how *this server* resolves a
conflict with *a provider* (`If-Match`, remote wins). It did not settle how a client that was
offline replays a stale mutation against *our own* API: the contemplated Swift app holding a
drag it could not send, or a second browser tab, or the kiosk. No provider is involved; this
is our concurrency control on our own resources. Left alone it is discovered during a client
build and retrofitted badly.

Ticket 03 also soft-deletes the Tasks a Connection sourced (`deleted_at`, hidden by the
default manager, purged after 30 days, restored by reconnecting). Whether *every* Task
deletion works that way was deliberately not decided on the domain model's behalf.

### What is already settled and must not be re-decided

- Mirrored fields are read-only and sync never touches local fields
  ([ticket 02](./02-domain-model.md)); the sync engine is the only writer of mirrored fields.
- Disconnect soft-deletes sourced Tasks for 30 days; reconnecting inside the window restores
  them ([ticket 03](./03-integration-provider-abstraction.md)).
- `TaskSource` is `PROTECT`; a Task's Attachments, Time blocks and Activity must never be
  lost to a cascade.
- Every API consumer is a first-class client (`CLAUDE.md`).

### To resolve

- The concurrency mechanism on our own resources: a `version` or `updated_at` precondition
  (`If-Match` / ETag) on which resources, and what a client does on `412`.
- What a client that was offline does with a queued mutation that lost: replay, rebase, or
  surface to the user. The kiosk has no keyboard.
- Whether a stale `do_date` write is dangerous in a way a stale `notes` write is not, given
  Daily prep and the Bump both write `do_date` server-side.
- Whether every Task deletion is a soft delete, the retention window, who may restore, and
  what restoring a Task does to its Time blocks and published calendar events.
- How a manually deleted, sourced Task interacts with the next sync: does a record that
  returns from upstream re-create it?

## Done when

- The concurrency rule is written so a client author can implement a retry without asking.
- Deletion semantics are decided for sourced and unsourced Tasks, including the sync
  interaction.
- Any new columns on `Task` and `TimeBlock` are named, so the first migration is complete.
