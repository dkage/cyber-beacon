---
type: grilling
blocked_by: [03]
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
