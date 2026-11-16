---
type: grilling
blocked_by: [01]
---

# Baseline reversals of the earlier model

## Question

**Which behaviors of the earlier domain/integration model are reversed by the Sunsama baseline, and what replaces them?**

## Done when

- `CONTEXT.md` and the glossary reflect the four reversals.
- Parity tickets 02/03/04 no longer list these as open questions.
- Backend tickets 02/03/06/08 mark the reversed behaviors as superseded.

## Answer

Four reversals are decided and recorded in `CONTEXT.md` and the glossary. They are the
product baseline for the first usable day; the remaining parity decisions stay open.

1. **Explicit import, not automatic projection.** Connecting a source does not fill the
   task list. Remote records are browsed in a source panel and deliberately imported as
   local worksheets. The earlier `mirrors=true` default (auto-project filtered records
   into Tasks) is reversed: import is the normal interaction, and any automatic projection
   is opt-in per Mount.

2. **Local worksheets.** An imported Task is a personal worksheet linked to its remote
   record. Local fields — title, notes, dates, priority, estimate, completion — are owned
   here. The remote record is a source preview, not a live mirror.

3. **Local completion.** Completing a Task here does not write back to the provider by
   default. Upstream status changes (e.g. a merged GitHub PR) do not complete the local
   worksheet. Remote actions are separate, explicit commands with their own permissions.

4. **Midnight carry-forward.** Unfinished work moves to the next day at midnight. Shutdown
   (wrap-up) is an optional review and does not gate rollover. The earlier wrap-up-gated
   Bump into Backlog is reversed: carry-forward keeps the do date on the next day rather
   than clearing it.
