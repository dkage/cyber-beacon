# Background work

Source: ticket 05. Django-Q2 on the Postgres ORM broker. There is no Redis and no
separate beat process.

| Term | Meaning |
|---|---|
| **Django-Q2** | The chosen queue and scheduler. Queued tasks, schedules and results live in Postgres and show in Django Admin. Celery + Redis was considered and reversed. Switching later is cheap if the four rules below hold |
| **Cluster** | A Django-Q2 worker group. A cluster works exactly one queue, and the queue name is the cluster name |
| **`worker`** | Compose service, a cluster on queue `default`: every sync for every provider, the sweep, the journal write, purges, Telegram |
| **`worker-ai`** | Compose service, a cluster on queue `ai` with one worker. Briefing only, long timeout, at most 2 retries. Never shares capacity with syncs |
| **Dispatcher tick** | Per-minute schedule. Enqueues one sync for each Mount that is `enabled`, has an `active` Connection, and whose `next_attempt_at` has passed. The poll interval is per-Mount data (default 5 min) |
| **Sweep** | The ~15-minute idempotent periodic job: auto-skip overdue wrap-ups (running `bump_day`) and re-enqueue stranded jobs (ticket 06) |
| **Lease** | `sync_started_at` on a Mount. Stops two syncs of one Mount and expires so a crashed worker cannot wedge it |
| **`next_attempt_at`** | When a Mount may next be attempted. Holds the backoff after a failure |
| **Rate bucket** | One Postgres row per rate scope, taken with `SELECT ... FOR UPDATE`. Enforced in the engine's HTTP client |
| **Release** | A throttled job re-queues itself with `schedule(..., Schedule.ONCE, next_run=...)` and **never sleeps**. The Laravel equivalent is `release($delay)` |
| **Auto-disable** | After 5 consecutive failures a Mount gets `enabled=false` and a visible `last_error`. Re-enabled manually or by a successful manual sync |
| **Derivable job** | Every background job must be re-derivable from Postgres state, with the sweep as the safety net |
| **`JobRun`** | One generic table of every background job attempt: `kind`, optional Mount or WrapUp, times, outcome, error in human words, counts. Retained 30 days. Feeds a read-only `/api/v1` endpoint and the frontend's red "!" log view |
| **Health event** | A state transition (`active→needs_reauth`, a Mount auto-disabled, a journal write stuck). Sends one Telegram message per transition, never per failure |

## Backoff by `classify` kind

| kind | behaviour |
|---|---|
| `retryable` | exponential backoff with jitter, capped near 1h |
| `rate_limited` | back off, honouring `Retry-After` |
| `auth_dead` | Connection to `needs_reauth`, no retry |
| `cursor_invalid` | clear the cursor and run a full sync |
| `fatal` | fail fast |

## Switch-cheaply rules

1. Tasks are thin wrappers calling one engine function each.
2. All enqueueing goes through one `enqueue()` helper.
3. All schedules are defined in one place.
4. Jobs are idempotent. Django-Q2's `retry` setting must exceed the task `timeout`, or a
   running task is redelivered and runs twice.

## Inspection

Django Admin, `manage.py qmonitor` and `qinfo` (they need a shared cache, not
local-memory). Flower is Celery-only and does not apply. A web queue view is a v2 idea.
