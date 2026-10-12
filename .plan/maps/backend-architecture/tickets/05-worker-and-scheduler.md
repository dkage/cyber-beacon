---
type: grilling
blocked_by: [03]
claimed_by: s2c4c3712c280
claimed_at: 2026-10-12T04:35:03Z
---

# Background worker and scheduler

## Question

**What runs the background work, and what schedules it?**

Blocked by the integration provider abstraction — the sync design determines what the queue is actually asked to do.

The workload: integration syncs, AI briefing generation, notifications, retries, and periodic polling. Note that **scheduling is not peripheral here** — the product's core loop is "poll these services on a cadence," so the scheduler is a primary component, not an add-on.

Memory is no longer a deciding factor. The earlier lean-queue argument assumed a constrained Pi; 8GB plus an available homelab removes it. Decide on ergonomics and on the scheduling story instead.

Candidates:

- **Celery + Redis** — heaviest, best-known, `beat` handles scheduling natively. The most written-about path.
- **Dramatiq + Redis** — nicer API, leaner, but **no built-in scheduler**; needs `dramatiq-crontab` or APScheduler bolted on.
- **Django-Q2** — scheduler integrated into Django Admin, which is genuinely pleasant for inspecting sync runs on a self-hosted box.

To resolve:

- Which queue, and the scheduler that goes with it.
- Where per-connection rate-limit budgeting is enforced, given Notion.
- Retry and backoff policy, and what a permanently failing sync does.
- Observability: how a failed sync surfaces to a human who is not reading logs.
- Whether the AI briefing shares this queue or wants its own, given very different latency and cost profiles.

## Done when

- The queue and scheduler are chosen, with the rejected options and reasons recorded.
- The enforcement point for rate limiting is named.
- The retry, backoff, and permanent-failure policy is written down.
- The mechanism by which a human learns a sync broke is decided.
- The AI briefing's queue placement is settled.

## Answer

Settled through a grilling session. **Django-Q2 on the ORM (Postgres) broker runs all background work, and its schedules drive the polling.** Vocabulary is in [`CONTEXT.md`](../../../../CONTEXT.md) and the glossary, which take precedence over this prose if they drift.

### Queue and scheduler

- **Django-Q2, ORM broker, no extra services.** Queued tasks, schedules and results live in Postgres and show in Django Admin. Scheduling is primary here, and Q2 has it built in.
- **Rejected: Celery + Redis.** It was the first recommendation and was reversed. Its two advantages were named-queue routing and an atomic Redis home for the token bucket, and Django-Q2 turned out to cover both (below). What remained was two extra services (`redis`, `beat`) and a queue that is lost on restart, for a load of a few dozen requests an hour. Memory was never a factor: about 0.8–1.3 GB for the whole Celery stack against 64 GB.
- **Rejected: Dramatiq + Redis.** No built-in scheduler, and scheduling is the core of the product.
- **Switching later is cheap and is kept cheap by four rules.** Tasks are thin wrappers that call one engine function each. All enqueueing goes through one `enqueue()` helper. All schedules are defined in one module or one data migration. Every job is idempotent. A move to Celery would then be roughly a day or two (task entry points, the helper, the schedules, the Compose services), with no change to the engine, adapters, models, `JobRun` or the Postgres-held state. This is an estimate, not a measurement.

### Scheduling shape

One **dispatcher tick** runs every minute. It selects Mounts that are `enabled`, whose Connection is `active`, and whose `next_attempt_at` has passed, then enqueues one sync per Mount. The poll interval is per-Mount data, defaulting to five minutes (ticket 03). One-off per-Mount schedule entries were rejected: they would need creating and deleting as Mounts change, and a `needs_reauth` Connection is skipped by a single filter instead. A webhook, if ever enabled, enqueues the same sync task. A Mount already syncing is skipped via a **lease** (`sync_started_at`, expiring after the sync timeout plus a margin, so a crashed worker cannot wedge a Mount).

Other periodic entries: the ~15-minute sweep from ticket 06 (auto-skip wrap-ups past their limit, which runs `bump_day`), the nightly trash purge from ticket 03, and the nightly `JobRun` purge.

### Queues and worker services

Django-Q2 queue names are cluster names, and a cluster works exactly one queue. Two clusters:

- **`worker`** (queue `default`): every sync for every provider, the sweep, the Obsidian journal write, purges and Telegram sends.
- **`worker-ai`** (queue `ai`, one worker): the AI briefing only. It has a long timeout and **at most 2 retries**, because a retry costs money. Its output is stored in Postgres. It never shares capacity with syncs, in either direction.

A per-provider cluster (a `notion` queue) is a settings-and-Compose change and is deferred until a crawl is seen starving another provider. **A throttled job never sleeps.** When the token bucket is empty it checkpoints its cursor, sets the Mount's `next_attempt_at` a few seconds ahead and exits, freeing its worker slot; the next dispatcher tick picks it up again. No per-job schedule row is created. Without this rule a split would be cosmetic.

### Rate-limit enforcement and the bucket's store

The enforcement point is, as ticket 03 settled, the **engine's HTTP client**. The bucket is stored in **Postgres**, one row per rate scope string, taken with `SELECT ... FOR UPDATE`. At about 3 requests per second per scope the row lock costs nothing, and the bucket survives a restart. Redis was the alternative and is not needed.

### Retry, backoff and permanent failure

The **engine** owns retries, driven by ticket 03's `classify` kinds. The queue's own retry is only a crash safety net.

| kind | behaviour |
|---|---|
| `retryable` | exponential backoff with jitter, capped at about 1 hour |
| `rate_limited` | back off, honouring `Retry-After` |
| `auth_dead` | Connection to `needs_reauth` immediately, no retry |
| `cursor_invalid` | clear the cursor and run a full sync |
| `fatal` | fail fast |

The backoff is held in `next_attempt_at` on the Mount, with `consecutive_failures` as the counter. After **5 consecutive failures** the Mount is auto-**disabled** (`enabled=false`) with `last_error` set; it is re-enabled manually or by a successful manual "sync now". Django-Q2's `retry` setting must stay above the task `timeout`, or a still-running task is redelivered and runs twice. The lease and idempotent jobs cover the rare duplicate regardless.

### Durability

The queue is in Postgres, so a restart loses nothing queued. All truth is in Postgres regardless, and **every background job must be derivable from Postgres state**: the journal write from `journal_written_at IS NULL` on a completed wrap-up, the briefing from "prep completed and no briefing stored". The periodic sweep re-enqueues anything stranded. Nothing here enters the backup scope from ticket 04.

### How a human learns something broke

- **`JobRun`**, one generic table for every background job: `kind` (`sync`, `journal_write`, `briefing`, `purge`…), an optional Mount or WrapUp it concerns, start and end times, outcome (the `classify` kind for syncs), the error in human words, and counts. A read-only `/api/v1` endpoint serves it. Retention is **30 days**, purged nightly. It is a table of our own so history survives a change of queue library.
- **A red "!" and log view in the frontend** is a requirement from the developer: clicking the indicator shows why a job failed, from `JobRun`. This ticket supplies the data and the endpoint; the UI belongs to the frontend design brief, which is out of scope for this map.
- **Telegram, on state transitions only**: `active→needs_reauth`, a Mount auto-disabled, a journal write stuck. One message per transition, never per failure. Routing, quiet hours and the TV's alert model stay with the notification system, still fog.
- **Inspection:** Django Admin for queued tasks, schedules and results, plus `manage.py qmonitor` and `qinfo` from a shell. The monitor needs a shared cache (a database cache table is enough), not the default local-memory one.

### Refinements

Added after the answer above was first written, from a review of the Django-Q2 switch.

- **The tick is the only retry mechanism.** Throttling, backoff and re-attempts all go through `next_attempt_at`; the `Schedule.ONCE` release originally proposed was redundant and is dropped. The journal write retries the same way, through the sweep.
- **Lost runs.** Django-Q2 hard-kills a task past its timeout, so a `JobRun` can be left open. The sweep closes any run still open past its timeout with outcome `lost`, counted as a failure, so the failure log never shows a run stuck as "started".
- **One record, not two.** Django-Q2's own success and failure result tables are capped or disabled (its save-limit setting). `JobRun` is the only human-facing log, and the 30-day purge covers it.
- **`retry` above `timeout` is tested.** One test asserts it for every cluster, since the `ai` cluster's long timeout is where a mistake would cause a duplicate run.
- **Schedules come from code.** The tick, sweep and purges are defined once in an idempotent `ensure_schedules()` that runs on deploy and recreates anything missing, so an accidental edit in Admin does not silently stop polling.

### For the build issue

Not decisions, only setup items to carry onto the backend issue when one is filed: a shared cache (a database cache table is enough) for `qmonitor` and `qinfo`; a small `workers` count of about 2, since each worker loads the whole Django app; and pinning the Django-Q2 version after checking at build time that its release cadence and Django support are healthy.

### Excluded deliberately

- **A web dashboard for queue state.** Flower was considered and is Celery-only. The v2 option is a read-only endpoint over Django-Q2's `Stat` class.
- **Model choice, context assembly and per-run cost of the AI briefing.** Only its queue placement is settled here; the rest stays fog.
- **Notification delivery.** Only the three health events are defined.

### Flags

- **A defaults caveat.** The five-failure limit, the one-hour cap, the two AI retries, the 30-day retention and the lease length are reasoned defaults accepted as recommended, not tuned against real traffic. All are settings.
- **Ticket 04's service list is amended**, not reopened: see the note appended there.
- **Ticket 06's wording** that the vault sits on the backend's machine is unchanged by this ticket.
