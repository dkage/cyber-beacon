---
type: grilling
blocked_by: [03]
claimed_by: s8c783101efc1
claimed_at: 2026-10-13T00:55:56Z
---

# What becomes a Task, and what is only a widget

## Question

**Which upstream things are projected into `Task` rows, and which exist only as numbers
and lists on the dashboard?**

[Ticket 03](./03-integration-provider-abstraction.md) settled the shape of an
integration; it did not settle what an integration is *for*. Notion and Google Calendar
did not force the question — a Notion database row is a Task, a calendar event is a
Calendar event — but the remaining providers all raise it at once, and each of them would
answer it differently if left to its own adapter:

- **GitHub.** Is a review request assigned to you a Task? An open PR of yours? An issue
  assigned to you? Some of these have due dates and some never will.
- **Gmail.** The brainstorm asks for an unread-mail counter, which needs no Task at all.
  But "reply to this" is real work. Is an email a Task, a counter, both, or neither until
  you say so?
- **Sentry.** An unresolved issue is work, but issue volume is a dashboard number. A
  Sentry integration that projects every unresolved issue into the Backlog would destroy
  the Backlog.
- **Obsidian.** The `fleeting` note count is explicitly a badge in the brainstorm. Is a
  note ever a Task?

Answering this once is what keeps adding an integration boring. Answering it five times,
inside five adapters, is how the Backlog silently becomes a firehose and the Bump
mechanic stops meaning anything.

### What is already settled and must not be re-decided

- A Task is the same kind of thing wherever it came from, its origin lives in a separate
  `Source` row, and the projection is deliberately lossy with the remainder kept in `raw`
  ([ticket 02](./02-domain-model.md)).
- Status is derived from `do_date` and `completed_at`; there is no status column.
- Completion is local and is never written upstream.
- A Mount already carries per-resource configuration and a filter, so "only things
  assigned to me" is expressible without new machinery.

### To resolve

- The rule that decides Task versus widget-only, stated so a new adapter's author applies
  it without asking.
- Whether some things are **promotable** — visible as a dashboard item that becomes a Task
  on a deliberate action — and if so, what the promoted Task's `Source` says.
- What a widget-only integration reads: whether it holds counts and lists outside the Task
  tables, and where that data lives given it must survive a provider being unreachable
  when the kiosk renders.
- Whether an integration may be both at once — GitHub plausibly is — and what that does to
  its Mount configuration.
- The Backlog's protection: what stops a provider with thousands of eligible records from
  flooding it, given a Task carries Bump history and appears in Daily prep.

## Done when

- The Task-versus-widget rule is written down and reads as applicable by someone who was
  not in the conversation.
- Promotion is either specified or ruled out with a reason.
- Where widget-only data lives, and its staleness behaviour, is decided.
- The dual-purpose case is settled.
- The remaining providers — Outlook, Gmail, GitHub, Sentry, Obsidian, Telegram, Jira — are
  each classified under the rule, so that each becomes an ordinary GitHub issue with no
  open questions left in it.

## Answer

Settled through a grilling session. Vocabulary is recorded in [`CONTEXT.md`](../../../CONTEXT.md)
(**Snapshot**, **Promotion**), which takes precedence over this prose if the two drift.

### The rule

> A remote record becomes a **Task** only if all three hold. **(a)** It is a discrete unit
> of work that is *yours*: assigned to you, requested of you, or authored by you and
> awaiting your action. **(b)** You could meaningfully give it a do date. **(c)** Whether it
> is done is your decision to make, not the provider's.
>
> Everything else is **widget-only**: counts and lists of ambient state, such as unread
> mail, unresolved Sentry issues or the `fleeting` note count.

An adapter author applies the three tests to a candidate record and never asks anyone.
The rule is enforced in configuration, not in adapters: **a Task-projecting Mount must
carry a filter**, and the default is "mine" (assigned, requested or authored), never
"everything visible". Adapters stay free of any Task-or-widget logic.

(c) is what the self-authored case turned on. An open PR of yours is yours to merge, and
that includes self-approving past review in an emergency, so it is a Task even though a
reviewer's state is involved.

### Where widget-only data lives: the Snapshot

One **`MountSnapshot`** row per Mount (latest value only): `value` (JSONB, e.g. `count`
plus a short item list), `fetched_at`, and the Mount's existing `last_succeeded_at`. The
sync engine is the only writer, from a new pure adapter method `summarize(records) ->
Snapshot`, beside `project`. Widgets and the AI briefing read the Snapshot; **nothing
calls a provider when the kiosk renders**.

Staleness follows ticket 03 unchanged: a Snapshot is shown with its `last_succeeded_at`,
so a provider outage leaves the last figures visible and labelled stale rather than blank
or falsely fresh. A live call at render was rejected because it fails exactly the
"provider unreachable" case. A typed table per provider was rejected as failing the
"eighth integration is boring" test.

History is **not** kept: latest value only. A time series can later be an append-only
table without changing the Snapshot contract.

### Dual purpose is per Mount

An integration may be both, and the unit that decides is the **Mount**, not the
Connection. One Connection carries several Mounts, each with its own filter and its own
`mirrors` flag. `mirrors=true` projects Tasks; `mirrors=false` produces a Snapshot only.
**Every Mount also writes a Snapshot** (at least its open-item count), so "tasks per
integration" badges need nothing extra.

This adds one capability to ticket 03's declared set: **`SUMMARIZE`** (the adapter can
produce a Snapshot). It extends that set; it changes nothing already decided. A provider
with `READ` and no `SUMMARIZE` stays valid.

Worked case, GitHub on one Connection:

| Mount | Filter | `mirrors` | Produces |
|---|---|---|---|
| Needs me | review requested of me, issues assigned to me, **open PRs I authored** | true | Tasks ("Review: …", "Merge: #198") |
| Failing CI | my PRs with red checks | false | Snapshot, a red badge |

The Needs me Snapshot is split into `awaiting_review` and `ready_to_merge`, so a PR waiting
on someone else is distinguishable on the badge. Review state never gates a Task: a PR you
intend to self-approve counts as ready.

### Promotion

Specified. A widget list item may carry a manual **"make this a Task"** action, offered
only when the adapter can name a stable `external_id` and `url`. The promoted Task gets an
ordinary `TaskSource` (with a `promoted` marker in `raw` and in the `TaskActivity` row) and
**then follows the normal sync path**, so later syncs treat it like any other sourced Task.
There is no one-off code path. This is how a Sentry issue or an email becomes work without
any Mount ever projecting it automatically.

### The Backlog's protection

Three layers, combined: **(1)** the mandatory "mine" filter above; **(2)** a **per-Mount
cap on open projected Tasks**, default about 200 and editable per Mount, past which the
engine stops projecting, sets a visible Mount warning, and still counts the overflow in the
Snapshot; **(3)** the first sync of a new Mount shows a **preview count and requires
confirmation** before projecting anything. Auto-archiving stale projected Tasks was
rejected: the Bump already surfaces what you keep avoiding, and silently archiving would
hide it.

### When a record leaves the filter

A merged PR is not missing, so the tombstone alone does not cover it. A tombstone from
`fetch` now carries a **reason**, reported by the adapter:

- **`resolved`** (merged or closed PR, closed issue, Jira Done): the engine **completes the
  Task** with a `TaskActivity` row whose actor is the integration. This is still a *local*
  write; nothing is sent upstream, so ticket 02's "completion is local" holds.
- **`withdrawn`** (review request retracted, row deleted or archived upstream): the Task is
  **tombstoned** (`deleted_upstream_at`) and left open for you to dismiss, because the work
  vanished rather than finished.

The engine remains the only writer, and branches on the reason, not on provider identity.

### Classification of the remaining providers

| Provider | Task Mount | Snapshot | Promotable |
|---|---|---|---|
| Google Calendar | no (`CalendarEvent`, never a Task) | next meeting | no |
| Outlook calendar | no (as Google) | next meeting | no |
| Outlook mail | no | unread count, recent list | yes |
| Gmail | no | unread count, recent list | yes ("reply to this") |
| GitHub | yes (Needs me, above) | yes, per Mount | yes (items outside the filter) |
| Sentry | no, never by default | unresolved count, top-N list | yes |
| Obsidian | no, a note is never a Task | `fleeting` count | no |
| Telegram | none (`NOTIFY` only) | none | no |
| Jira | yes (assigned to me) | open count | yes |
| Notion | yes | open count | no (already Task-shaped) |

Email is the judgment call: it is never an automatic Task, since volume would swamp the
Backlog, and "reply to this" is covered by promotion. Jira is deprioritised (the company
moved to Notion) but classified so its issue has no open questions.

### Omitted

- The Snapshot's exact JSON shape per provider and the per-provider `summarize` contents:
  adapter work, settled in each provider's issue.
- The SonarQube carousel, which is not in the integration list; it would be a widget-only
  Mount and needs no decision here.
- Whether the first-sync preview and the cap warning appear on the kiosk or only on the
  connections screen: a frontend decision.
- Briefing use of Snapshots: the AI briefing architecture is still in the map's fog.
