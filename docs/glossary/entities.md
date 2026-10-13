# Entities

Model names and the fields that carry a decision. Not a schema.

## Work and time (ticket 02)

| Model | Purpose |
|---|---|
| `Task` | The one kind of work item. Carries three independent local dates (do, due, start). **No status column**: status is derived from `do_date` and `completed_at`. Self-FK `parent` for subtasks |
| `TaskSource` | Zero-or-one per Task: provenance. Connection, `external_id`, untouched `raw` payload, `deleted_upstream_at` tombstone. FK is `PROTECT` |
| `TimeBlock` | A committed span of clock time (instants). Nullable Task. One Task may have several |
| `CalendarEvent` | Mirrored meeting. Has no do date and is not a Task |
| `TaskActivity` | Append-only semantic history. Kinds include `bumped`, `rescheduled` |
| `Attachment` | File on a Task or CalendarEvent. Stores a relative storage key, so the backend can be swapped by settings |
| `User` | Gains `timezone` (IANA), which local dates depend on |

`TaskEvent` was the working name for `TaskActivity` and is retired.

## Integrations (ticket 03)

| Model | Purpose |
|---|---|
| `IntegrationConnection` | Account link: `user`, `provider`, `account_identity`, `scopes`, encrypted `credentials`, `status`, `last_error`. Health lives here |
| `Mount` | Remote resource: `mapping` (JSONB, keyed by remote property **id**), `mirrors`, `is_publish_target`, `enabled`, `cursor`, `last_attempted_at`, `last_succeeded_at`, `consecutive_failures`, plus `next_attempt_at` and the `sync_started_at` lease (ticket 05). Freshness lives here |
| `MountSnapshot` | One row per Mount, latest only: `value` (JSONB), `fetched_at`. Written by the engine from the adapter's `summarize`. Read by widgets and the briefing (ticket 08) |

## Background work (ticket 05)

| Model | Purpose |
|---|---|
| `JobRun` | One row per background job attempt. 30-day retention. Behind the frontend's failure log view |

## Daily rhythm (ticket 06)

| Model | Fields |
|---|---|
| `DailyPrep` | `user`, `date`, `started_at`, `completed_at`, `skipped_at`. Unique on `(user, date)` |
| `WrapUp` | Same, plus `auto`, `journal_text`, `journal_written_at`. One row per calendar day |

A row is **resolved** if `completed_at` or `skipped_at` is set. A skipped prep is never
stored: it is the absence of a row past the cutoff.

## Per-user settings (ticket 06)

| Setting | Default | Meaning |
|---|---|---|
| `day_rollover` | 00:00 | Local time the day turns over. Decides when a wrap-up becomes due |
| `prep_cutoff` | 10:00 | Past it, with no prep resolved, prep is missed |
| `wrap_up_limit` | 24h | Past it, the sweep records an auto-skip |
