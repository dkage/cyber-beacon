---
type: grilling
---

# The domain model: do-date, due-date, and what a Task is

## Question

**What is a Task, and what does it mean for one to be scheduled?**

This is the root of the map. Django models get written early and migrations are awkward to unwind, so this decides the shape of the schema, the API contract, and the calendar write-back.

The sharpest known constraint, and the thing that most motivated this project: **do-date and due-date are different.** From the developer's own product research — *"If I organized things by when they're due, like every app wants, rather than when I intend to do them, as is normal behavior, I would be up all night every night."* That is a statement about what a Task **is**, not a feature request.

To resolve:

- The entities and their names. `Task`, and whatever represents "this task occupies 14:00–15:30 on Thursday" — a scheduled block, a time block, something else. One task may occupy several; the research explicitly asks for splitting a task across multiple blocks.
- **Do-date vs due-date vs start-date.** Which exist, which are optional, and what each means when absent.
- **Timezone semantics, deliberately.** `USE_TZ=True` with UTC storage is the easy half. The hard half: a *do-date* is a local calendar date, not an instant, and so is a due-date. Modelling them as timestamps is a trap that surfaces months later as tasks landing on the wrong day across DST or travel. A scheduled block, by contrast, genuinely is an interval of instants.
- **Task provenance.** A task pulled from Jira or Notion is a projection of something someone else owns. What is locally editable, what stays authoritative upstream, and what happens on conflict.
- Subtasks and hierarchy, and whether they schedule independently of their parent.
- Where completion lives, and whether completing locally writes back to the source.

## Evidence

Verbatim from the developer's product research, quoted here so this ticket stands alone. Each line constrains the model rather than requesting a feature.

**The do-date / due-date split — the motivating constraint:**

> "If I organized things by when they're due, like every app wants, rather than when I intend to do them, as is normal behavior, I would be up all night every night"

> "I desperately need this for planning homework and time blocking for study. I want to know when it's due but I want to plan it for days to study it without changing the initial due date"

> **Do/Due Date Distinction**: This is by far one of the most requested features — separating when you plan to work on a task from when it's actually due

**A precise invariant, and the sharpest test of whether the split is modelled correctly:**

> **Don't change end date when postponing** — Postponing a task should not shift the deadline

If moving a task's do-date drags its due-date along, the two fields are not actually independent and the model is wrong.

**A third date, distinct from both:**

> **Start date / "Start On"** — For tasks that aren't actionable until a future date

**One task, several blocks:**

> Split tasks into multiple time blocks

> **Time estimation in calendar view** — Including splitting a task into multiple time blocks

This is why a scheduled block cannot simply be two columns on `Task`.

**Hierarchy and dependency, which may or may not be in scope for a first model:**

> **Sequential/dependent tasks within projects** — Arrange tasks that depend on one or more previous tasks

> **Subtask time repeats with parent** — When a parent task repeats, subtask times should follow

> **Display parent task name** — Option to show the parent task context when viewing subtasks


## Done when

- Every entity is named, with its fields and their nullability.
- Each date-bearing field is explicitly classified as a local date or an instant, with the reasoning recorded.
- The rule for a task whose upstream source disagrees with local state is stated.
- Subtask scheduling behaviour is decided.
- `CONTEXT.md` exists at the repo root containing the resolved terms, per `docs/agents/domain.md`.
- The `## Answer` states what was decided and what was deliberately excluded.
