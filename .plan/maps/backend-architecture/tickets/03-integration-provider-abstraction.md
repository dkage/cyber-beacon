---
type: grilling
blocked_by: [02]
claimed_by: s7ada441f1bb2
claimed_at: 2026-08-29T20:41:16Z
---

# The integration provider abstraction

## Question

**What shape does an integration have, such that adding the eighth one is boring?**

Blocked by the domain model: an integration's job is to project external things into local entities, so those entities must exist first.

Two providers are in scope here, chosen because they **stress the abstraction in opposite directions** — designing against only one produces something that breaks on the other:

- **Google Calendar** — bidirectional. Scheduling writes back, so conflict resolution is real, and push notifications are available instead of polling.
- **Notion** — read-heavy, with a punishing rate limit of roughly 3 requests/second average. Forces a polling budget, caching, and backoff as first-class concerns rather than afterthoughts.

To resolve:

- The provider interface every integration satisfies, and where per-provider quirks are allowed to live.
- **`IntegrationConnection` as a model distinct from allauth's `SocialAccount`.** Identity is one-per-provider-per-user; connections are **many** — this developer has personal and work Google accounts, personal and work Outlook. The lifecycles differ too: revoking calendar access must not log anyone out. The connection carries scopes, tokens, sync state, and rate-limit budget.
- **Credential encryption at rest.** OAuth refresh tokens in plaintext PostgreSQL columns is a liability once there is more than one user. Decide the field-level encryption approach and where the key lives — outside the database.
- Sync state and scheduling: full vs incremental, cursors, what "last synced" means, and what happens after a long outage.
- **Bidirectional conflict resolution** for Calendar: a local move versus a remote move of the same block.
- Failure and re-auth: what the user sees when a refresh token dies, scoped to the connection rather than the whole account.

## Done when

- The provider interface is specified: its methods, and what a new integration must implement.
- `IntegrationConnection`'s fields and its cardinality relative to `SocialAccount` are settled.
- The credential encryption mechanism and key location are chosen.
- The Calendar write-back conflict rule is stated concretely enough to implement.
- The rate-limit budgeting approach is defined and demonstrably survives Notion's limit.
- The remaining integrations in the map's *Not yet specified* have graduated into tickets, and that fog entry is cleared.

## Answer

Settled through a grilling session. The shape below is what the first integration app can
be built against. Two decisions were large enough to record separately:
[ADR-0002](../../../docs/adr/0002-integration-connections-separate-from-identity.md) for
the split from allauth, and
[ADR-0003](../../../docs/adr/0003-credential-encryption-at-rest.md) for credentials at
rest. `Mount` is now in [`CONTEXT.md`](../../../CONTEXT.md), which takes precedence over
the prose here if the two ever drift.

### The spine: adapters are thin, and the engine is the only thing that writes

One rule answers most of this ticket:

> A provider adapter speaks HTTP and translates payloads. It owns no loop, no
> transaction, and no `save()`. A single **sync engine** owns all of those, for every
> provider, forever.

The map's success test — that adding the eighth integration is boring — *is* this
decision. Boring means the new file contains no orchestration, and the only way to
guarantee that is for the orchestration to live somewhere else. It also carries ticket
02's central guarantee across the seam: the engine holds the single
`save(update_fields=MIRRORED_FIELDS)`, so an adapter that returns a `do_date` has it
dropped rather than obeyed. Sync cannot touch your schedule by construction, and a new
adapter's author cannot break that even carelessly, because they never hold the model.

Providers differ by **declared capability**, never by identity:

```
READ  INCREMENTAL  WRITE_BACK  WEBHOOK  MAPPABLE  NOTIFY  REVOKE
```

The engine branches on the declaration. **An `if provider == "notion"` anywhere in the
engine means the abstraction has failed**, and that is the review rule rather than a
style preference. Per-provider quirks are allowed in exactly two places: inside the
adapter (pagination, property types, error mapping) and in per-Mount configuration.
Declaring capabilities as data rather than as class hierarchy also means the connections
API can tell a client that a Connection is readable but not writable without
instantiating anything.

### The provider interface

```python
class Provider(Protocol):
    key: str                                    # "google_calendar", "notion"
    capabilities: frozenset[Capability]
    policy: RatePolicy                          # req/s, burst, page size, retry ceiling

    # authorization
    def authorize_url(state) -> str
    def exchange_code(code) -> Credentials
    def refresh(creds) -> Credentials
    def account_identity(creds) -> str          # Google `sub`, Notion `workspace_id`
    def revoke(ctx) -> None                     # REVOKE

    # discovery
    def list_mountables(ctx) -> list[Mountable] # the calendars / data sources on offer
    def describe_schema(ctx, mount) -> Schema   # MAPPABLE — powers mapping validation

    # reading
    def fetch(ctx, mount, cursor) -> Iterator[Page]   # records + tombstones + next cursor
    def project(record, mapping) -> Projection        # pure; mirrored fields only

    # writing                                          # WRITE_BACK
    def push(ctx, mount, intent) -> RemoteRef
    def unpublish(ctx, mount, ref) -> None

    # push                                             # WEBHOOK
    def verify(request) -> WebhookEvent
    def subscribe(ctx, mount, callback_url) -> Subscription

    def classify(exc) -> ErrorKind
```

Three properties matter more than the exact method list.

**`ctx` hands the adapter its HTTP client.** An adapter never constructs one. That is
what makes the rate budget unbypassable rather than a convention someone remembers.

**`fetch` yields pages rather than returning a list**, so the engine checkpoints the
cursor mid-sync. A Notion crawl that dies on page 40 of 60 resumes at 40 instead of
respending the whole budget.

**`classify` is the adapter's error taxonomy**, collapsing a provider's HTTP mess onto
five kinds the engine understands: `retryable`, `rate_limited`, `auth_dead`,
`cursor_invalid`, `fatal`. This is the smallest interface that lets the engine do the
right thing without knowing which provider it holds — retrying a `retryable`, sleeping on
a `rate_limited`, stopping dead on an `auth_dead` rather than burning budget re-asking a
question with a permanent answer.

`project` stays on the adapter and stays pure. Notion's needs to know that a `rollup` can
wrap a date; that is provider knowledge. It touches no database.

### Connection and Mount

**`IntegrationConnection`** — one authorised link to one account at one provider. It has
**no foreign key to allauth's `SocialAccount`** and its own OAuth client code; see
ADR-0002.

| field              | type              | null | notes                                                     |
|--------------------|-------------------|------|-----------------------------------------------------------|
| `user`             | FK                | no   | multi-user in structure from day one                      |
| `provider`         | text              | no   | the adapter's `key`                                       |
| `account_identity` | text              | no   | provider's stable account handle; unique with the two above|
| `display_name`     | text              | no   | local and editable — "Work Google (danilo@…)"             |
| `scopes`           | text[]            | no   | what was actually granted, not what was asked             |
| `credentials`      | **encrypted JSON**| yes  | opaque blob; null once disconnected                       |
| `status`           | text              | no   | `active` / `needs_reauth` / `disabled` / `disconnected`   |
| `last_error`       | text              | yes  | last classified failure, in human words                   |
| `connected_at`     | instant           | no   |                                                            |
| `disconnected_at`  | instant           | yes  | set when credentials are wiped                            |

**`Mount`** — one remote resource attached through a Connection: one calendar, one Notion
data source, one Obsidian directory.

| field                  | type    | null | notes                                                        |
|------------------------|---------|------|--------------------------------------------------------------|
| `connection`           | FK      | no   | cascade; the Connection row is itself protected              |
| `user`                 | FK      | no   | denormalised — see the publish-target constraint below       |
| `remote_id`            | text    | no   | calendar id, data source id, directory path; unique per conn |
| `remote_name`          | text    | no   | cached label for display                                     |
| `mapping`              | JSONB   | no   | field map, keyed by remote property **id**                   |
| `mirrors`              | bool    | no   | default true — this Mount is read into local records         |
| `is_publish_target`    | bool    | no   | default false — our Time blocks are written here             |
| `enabled`              | bool    | no   |                                                               |
| `cursor`               | text    | yes  | opaque, provider-defined                                     |
| `last_attempted_at`    | instant | yes  |                                                               |
| `last_succeeded_at`    | instant | yes  | **this is what the UI shows**                                |
| `consecutive_failures` | int     | no   | default 0                                                    |
| `last_error`           | text    | yes  |                                                               |

The split is by concern: **the Connection owns health, the Mount owns freshness.** A
Connection is the permission; a Mount is what that permission is aimed at.

The alternative — one Connection per calendar — was rejected because it multiplies OAuth
grants and re-auth prompts by calendar count. Holding the per-resource state in a JSONB
blob on the Connection was rejected because cursors are genuinely per-resource: a Google
`syncToken` belongs to one calendar and a `410 GONE` invalidates one calendar's, so
burying them in JSONB makes "what is stale?" unqueryable and makes two concurrent syncs
contend for one row.

`user` is denormalised onto `Mount` for one reason, stated so nobody removes it as
redundant: **at most one Mount across all of a user's Connections may be the publish
target**, and a partial unique index is the only way to enforce that in the database
rather than in a code path someone can forget. The FK to `connection` would otherwise
make it a two-hop constraint Postgres cannot express.

### The field mapping is keyed by property id, not by name

Notion changes the *shape* of projection, not only its order. A Notion data source has
arbitrary user-defined properties, so *which property is the due date* is configuration —
and it is per-data-source, not per-connection, because two databases in one workspace
have different property names and the same token reads both. The developer's real case:
one database with a `Due date` column, another whose equivalent is `Concluída em`, and a
third with no due-date column at all, which maps to nothing — the domain model already
permits an absent `due_date` to mean no deadline.

`mapping` is JSONB on the Mount, keyed by the remote **property id**, caching the name and
the type:

```json
{"due_date": {"id": "a%3Bhb", "name": "Concluída em", "type": "date"}}
```

Notion's property ids are documented as stable across renames — "does not change if the
name is changed" — so a name-keyed mapping would break silently on a rename, and break
*later*, long after anyone connects the two events. The cached name is for display and
for rebuilding filters; the id is the identity. The type is carried because the
projection genuinely must branch on `date` versus a `formula` or `rollup` that returns
one. A separate `FieldMapping` table was rejected: every read is "this one Mount's
mapping," so it buys joins nobody wants and a migration for every new mappable field.

Mappings are **validated on write** against a live `describe_schema` fetch, so a bad
mapping fails when you save the connection rather than at 3am inside a worker.

### Sync state, and why a long outage is not a special case

Two timestamps, not one: **`last_attempted_at` and `last_succeeded_at` are different
columns and the interface shows the second.** A Mount that has been failing for six hours
must not read as "synced 40 seconds ago" — that is the single most common way a dashboard
of this kind lies to its owner, and it costs one column to make impossible.

An invalid cursor is **ordinary and expected**, not a disaster path. Google says so
explicitly with `410 GONE` — sync tokens expire, and ACL changes invalidate them — and
Notion's `last_edited_time` checkpoint never expires but will pull a large first page
after an outage. So the engine has one rule: *cursor rejected → clear it, run a full
sync, reconcile by `external_id`* — which is the same path the very first sync takes, and
is therefore exercised routinely rather than only after something has gone wrong.

Ticket 02's `deleted_upstream_at` is what makes that reconcile safe. Records missing from
a full sync are **tombstoned, never deleted**, so a provider having a bad day cannot take
your do-dates, time blocks, attachments and completion history with it.

### Polling is the baseline; push only accelerates it

Every provider implements incremental polling. A declared `WEBHOOK` capability, when a
public callback URL is also configured, shortens the interval to a floor — it does not
replace the poll.

Push-first was rejected on the facts. Google Calendar's watch channels **cannot be
renewed, only replaced**, and expire on Google's schedule, so a missed renewal silently
stops a calendar syncing with no error raised anywhere. Google additionally requires a
CA-valid certificate on a domain verified in Search Console, which depends on
[the deployment ticket's](./04-deployment-topology.md) reachability decision — undecided
at the time of writing. Under this design that dependency is not blocking: with no public
URL you get a five-minute poll, and reachability later turns a flag on.

The webhook's only job is to **enqueue the sync the timer would have run**. It carries no
data — Google's notification has no body by design; it is a "go look" ping — so the push
path and the poll path are one code path and there is no second thing to get wrong. It
also means no provider's bespoke payload format becomes load-bearing.

### The rate budget, and the rule that makes Notion survivable

The budget is keyed by **a scope string the adapter names**, not by connection id. The
adapter answers "what bucket does this request spend from?" — `notion:ws:abc123`,
`google:conn:42` — and a token bucket gates every outbound request inside the engine's
HTTP client.

This matters because Notion's limit is roughly three requests per second **per
connection** *plus* a separate workspace-wide budget shared across connections. A
per-connection budget would let a personal and a work connection into the same workspace
each believe it owns 3 r/s and together spend 6. The budget belongs to a remote scope, not
to a local model. The **enforcement point is the engine's HTTP client**; where the bucket
is *stored* touches [ticket 05](./05-worker-and-scheduler.md) and is left to it.

Purely reactive backoff — fire and honour `429` — was rejected: it fails hardest during a
full sync, which is exactly when thousands of requests are in flight and a backoff spiral
is most expensive.

The arithmetic the ticket asks for. Notion returns full property values in the data source
query at 100 rows per page, so a full sync of a 2,000-task data source is **20 requests,
about 7 seconds** at 3 r/s. Steady state is far below the ceiling: an incremental poll
filtered on `last_edited_time` is a single request, so three Mounts on a five-minute
cadence spend about **36 requests per hour against a budget of 10,800**.

The danger is not the ceiling, it is an N+1. If an adapter fetched each row's blocks to
get its content, that same sync becomes 2,020 requests and **about eleven minutes** of
solid budget. So the interface carries a rule, not just a number: **`fetch` may not make
per-record requests.** Whatever a record needs must come from the list payload or be
deferred to a separate, deliberately scheduled job.

### Calendar write-back: optimistic concurrency, and the remote wins

Ticket 02 settled that a Time block is *ours* — we author the calendar event, stamped with
`extendedProperties.private` so a later sync can tell our own blocks from genuine
meetings. This ticket settles what happens when both ends move.

Every write sends `If-Match` with the stored ETag. A `412` means the remote changed under
us: **re-fetch, and the remote wins.** The local Time block is updated to match and a
`TaskActivity` row records that it moved and who moved it.

This feels backwards for a moment, given we are the author, so the reasoning is recorded:
an unexpected remote change to one of our own events means a human moved it somewhere that
was not this application, and that human was the user. Forcing our value over it means the
app silently undoes a change made on a phone — the failure people do not forgive.
Timestamp-based last-write-wins cannot detect the conflict at all. Prompting the user was
rejected because the primary surface is a kiosk with no keyboard, and because the activity
row makes it unnecessary: the move is visible in the history without interrupting anyone.

Three boundaries on that rule:

- It governs **time and existence only**. A provider never wins over local fields — the
  meeting's local `notes`, the Task a block belongs to, attachments. Ticket 02's
  local/mirrored split is untouched.
- **A remotely deleted event we authored deletes the local `TimeBlock` and keeps the
  `Task`**, recording it. The plan changed; the intention did not.
- The cost is real and is accepted: a local edit that loses a `412` is overwritten rather
  than merged, surviving only in `TaskActivity`. Telling the user actively belongs to the
  notification system, which is still fog.

A distinct problem surfaced here and is deliberately **not** answered: a client that was
offline — the contemplated Swift app holding a drag it could not send — replaying a stale
mutation against *our* API is our own concurrency control on our own resources, with no
provider involved. It is now recorded in the map's *Not yet specified*.

### Which calendar receives published blocks

One Mount is flagged `is_publish_target`, chosen explicitly, and it **defaults to the
primary calendar of its connection**. Mounts are otherwise read-only mirrors.

The default is recorded with its reason, because a future reader will otherwise "fix" it:
secondary Google calendars do not reliably raise alerts on Android, which makes the
primary the only dependable place for a schedule the user is meant to be reminded of.
Writing blocks to "the first connection's primary calendar" implicitly was rejected as the
route by which a personal drag lands in a work calendar in front of colleagues.

### Failure, re-auth, and disconnection

A dead refresh token sets the **Connection** to `needs_reauth`. Its Mounts stop being
enqueued, **every other Connection keeps syncing**, and the data already synced **stays
visible, marked stale with its `last_succeeded_at`**. A dead token does not mean the tasks
stopped existing. It surfaces on the connections endpoint and conspicuously on the kiosk,
which the developer's own product research already asks for in the forgotten-prep case.

Re-authorisation has two hard requirements:

- It **updates the existing row**, keeping Mounts, mappings and cursors. Deleting and
  recreating would evaporate a carefully built property mapping and force a full sync.
- It **compares `account_identity` and refuses a mismatch.** When Google's account chooser
  is sitting on the wrong account, silently re-pointing work Mounts at personal data
  produces records that look entirely legitimate afterwards.

Disconnection is not deletion. It **wipes credentials immediately** — that is the point of
it — stops syncing, and keeps the `Task` and `TaskSource` rows. The FK is `PROTECT`:
`CASCADE` here would be ticket 02's entire thesis defeated by a foreign key, quietly
deleting a user's attachments, time blocks and completion history because a token was
revoked. Dropping the `TaskSource` rows while keeping the Tasks is nearly right and fails
on reconnection — with provenance gone, reconnecting the same workspace re-imports
everything as duplicates, leaving two of each with the blocks on the wrong copy. So
**reconnecting the same `account_identity` adopts the existing Sources and resumes.**

A checkbox on the disconnect form additionally **soft-deletes** the sourced Tasks:
`deleted_at` set, excluded by the default manager, purged by a scheduled job after **30
days**. Reconnecting inside the window restores them. Indefinite retention was rejected
because it makes "delete my work data" a lie, which is the wrong thing to be wrong about;
a per-user setting was rejected as a settings screen for a system with one user, reachable
later without anything moving.

### Integrations that are not syncs

Telegram is outbound-only — a bot token and a chat id, no records, no cursor. Obsidian is
a directory on disk with no OAuth at all, read for the `fleeting` note count and written
for the wrap-up journal. Both use **the same `IntegrationConnection`**, separated purely
by declared capability: Telegram declares `{NOTIFY}` and nothing else, so the sync engine
never enqueues it — not through a special case, but because it has no `READ`. Obsidian's
credential blob holds a path instead of tokens, which ADR-0003's opaque-blob decision
already permits.

This is the cheapest available test of whether the capability design is real, and it
passes. A notification sink still needs credentials encrypted at rest, per-user
configuration, a health status and a re-auth surface — the entire Connection model and
none of the sync engine. A separate model for sinks would duplicate all four to avoid one
empty capability set; putting a bot token in `settings.py` breaks multi-user on day one.

### How the remaining integrations clear the fog

Two tickets, not seven:

- **[07 — the Outlook work tenant](./07-outlook-work-tenant-feasibility.md)** (research).
  The only genuine unknown, and it is a fact to find rather than a decision to make:
  whether the tenant permits third-party app registration at all.
- **[08 — what becomes a Task, and what is only a widget](./08-task-or-widget.md)**
  (grilling). The question Gmail, GitHub, Sentry and Obsidian all raise at once. Answer it
  once and five adapters inherit it; leave it and each adapter answers it differently in
  its own file, which is precisely how the eighth one stops being boring.

Everything else — writing an adapter — becomes **one GitHub issue per provider**, because
the repository's two-tracker rule is "if it has a diff, it is an issue," and an adapter is
nothing but diff. They are not filed yet: `CLAUDE.md` generates issues once a map's
frontier empties, and tickets 04–06 are still open. One ticket per provider was rejected
as contradicting this ticket's own success test — six grilling sessions written before the
first adapter has ever run is designing against imagination rather than feedback.

### A correction to this ticket's premise

The ticket states that allauth identity is "one-per-provider-per-user." That is not what
the constraint says: `SocialAccount` is unique on `(provider, uid)`, so a user *may* hold
several accounts per provider. The conclusion the ticket draws is right and the argument
for it is stronger than the one written down — the objection is not a cardinality limit
but that **every `SocialAccount` is a login credential**, so connecting an
employer-controlled account for its calendar would make that account a way to sign in.
Recorded in ADR-0002 in those terms.

### Excluded deliberately

- **Which queue and scheduler run any of this**, and where the rate-limit token bucket is
  stored. [Ticket 05](./05-worker-and-scheduler.md), which this ticket now feeds with three
  concrete inputs: per-provider queue routing so a Notion sync crawling behind its budget
  never blocks a calendar sync, the nightly trash purge, and the budget store.
- **Reachability and certificates** for webhook callbacks.
  [Ticket 04](./04-deployment-topology.md). Nothing here blocks on it.
- **Offline client versus server concurrency**, and **a general trash bin for Tasks** —
  both raised here, both genuinely outside this ticket, both now in the map's fog.
- **Field-level encryption of user content.** Ruled out with its reasoning in ADR-0003;
  the deployment ticket owns the disk-level answer that actually covers it.
- **Write-back of completion and upstream status.** Still ticket 02's answer: completion is
  local. Publishing our own Time blocks is not write-back, and remains the only thing this
  application writes upstream.
- **Bulk backfill of historical data.** Every sync path here is "changes since a cursor"
  or "everything currently visible." Importing three years of closed Notion rows is a
  different job with a different budget profile.
