---
type: grilling
blocked_by: [04, 07]
---

# Recurring work, backlog horizons and archive

## Question

**How do routines and future work stay visible without duplicate occurrences or a polluted daily list?**

F039, F079–F085. Recurrence was explicitly postponed in backend 02 and auto-archive rejected in 08; they are reopened planning questions, not already adopted behavior.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Define rule + materialized ordinary Task instances + exceptions; daily/weekdays/weekly/monthly/yearly, interval/weekday rules and date/timezone generation horizon.

- Define rough vs rigid start time, Parallel defaults, completed-instance preservation and edit-one/update-all-incomplete/stop/extend/delete-incomplete commands.

- Define untouched rollover collision with next instance vs genuinely edited/progressed occurrence; never discard logged time/notes to avoid duplicates.

- Keep source recurrence separate: cannot blindly repeat one upstream issue link, Todoist occurrence identity and native recurring series differ.

- Define optional backlog horizons without fake do dates, folders removed on scheduling, persistent priorities and filters; distinguish folder from project.

- Resolve inactivity archive threshold and progress signal, visible restoration, review reminder and search; archive is neither deletion nor undated work.

## Done when

- Write recurrence/exception API and all scope-of-edit choices with preservation tests.

- Walk monthly last weekday, missed workweek, DST routine, next-occurrence collision, stopped series, moved backlog folder and restoring archive.

- Amend backend 02/08 deferrals and CONTEXT.md/glossary only for explicitly adopted concepts.
