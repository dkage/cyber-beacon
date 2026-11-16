---
type: grilling
blocked_by: [01]
---

# Channels, contexts, daily priority and weekly objectives

## Question

**Which organizational concepts make planning useful without turning Cyber Beacon into another project manager?**

F034, F040–F048. Current local priority is one small int; Project and block categories were deferred. Sunsama has channels/contexts, separate daily/backlog priority and weekly objectives, not an upstream issue board.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Define Channel and Context separately from Connection/Mount and Project; task/objective membership, filters/default creation/import precedence, disable/delete and personal/private semantics.

- Define personal work's exclusion from work capacity while still occupying real clock time; channel-based calendar routing co-owned with scheduling ticket 05.

- Choose daily priority reset/rollover levels vs persistent backlog priority, local vs upstream fallback and sorting ties.

- Define Weekly objective identity, week anchoring, notes, completion, extensions/carry-over and task linkage without deleting Tasks or inventing project status.

- Define weekly planning/review target week, combined flow, weekend settings, summaries, manual vs suggested task alignment and historical time allocation.

- Reconcile channel color with Cyber Beacon semantic colors and kiosk privacy; category tint must not change the meaning of failure/AI/external state.

## Done when

- Record vocabulary/cardinalities and examples spanning work/personal channels and an objective extended two weeks.

- Specify filter and time aggregation semantics, objective deletion/unlink and priority reset without losing persistent urgency.

- Update backend 02/03/06 implications, CONTEXT.md and glossary after approval; do not call this a Project schema by assumption.
