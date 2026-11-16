---
type: grilling
blocked_by: [02, 04, 05, 06, 07, 08]
---

# Interactive planner beside the Cyber Beacon dashboard

## Question

**What complete frontend specification supports Sunsama's planner workflows while preserving our dashboard-first identity?**

F004, F010, F012, F048, F068, F075, F087, F089–F091, F105–F106. The existing design brief is dashboard-only and explicitly excludes the planner; backend map's 'already specified in full' is not a planner specification.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Specify Today, day-column Board, Calendar-centered, Focus, Daily prep/Wrap-up, weekly, Backlog/archive/trash, source panels, task details and settings navigation alongside dashboard profiles.

- Define source-vs-worksheet presentation, remote permission warnings, calendar projection/committed/actual visual layers and provider-action pending/failure feedback.

- Define task add directives and equivalent form controls, merge/unmerge, duplicate, search type/date/channel/archived, sorting/manual pins, command palette, keyboard and drag interactions.

- Give keyboard, pointer and touch alternatives; account for narrow screens, reduced motion, contrast, font scaling and timezone/week-start defaults.

- Keep TV glance-only density, distance calibration and passive cached/stale states; no disguised editable offline dashboard or credential scope expansion.

- Define API-owned read models and optimistic UI rollback; no frontend business-rule duplication. Build a standalone committed spec, not a reference to a private brief.

## Done when

- Produce a planner interaction/state/API matrix including loading/empty/error/stale/conflict and accessibility paths.

- Show how completing prep moves into Today/Focus or dashboard by preference without losing state; phone interaction and kiosk read-only scope stay distinct.

- Cross-check identity and widget data contracts with backend 09/11/12; settle what responsive web supports vs native-only later.
