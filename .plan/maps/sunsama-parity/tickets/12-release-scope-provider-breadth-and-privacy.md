---
type: grilling
blocked_by: [01]
---

# Release scope, connector breadth, collaboration and privacy

## Question

**What does 'follow Sunsama closely' mean for the first usable release and the later roadmap?**

F026–F027, F030, F050, F062, F088, F094–F095, F102–F110. The feature inventory is comprehensive within its cited scope; matching all providers and enterprise surfaces is not automatically the first milestone.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Recommend first usable manual day: Notion/Google candidates, worksheet task list, estimates/capacity/order, projections/pinning, actual timer, daily rituals and dashboard. Confirm whether recurrence/channels/basic weekly work ship with this or immediately after.

- Stage Gmail/GitHub/Outlook by actual daily need; explicitly disposition Jira (deprioritized), Linear, Asana, ClickUp, Todoist, Trello, Monday, Microsoft To Do/Planner, Google Tasks, Apple Reminders, CalDAV/iCloud, Slack/Teams, Toggl, Zapier, conferencing/contacts.

- Decide mail-client depth: linked preview and triage vs full drafts/send/reply/forward. Do not treat Mail.Read approval as permission to send.

- Keep Sentry/Obsidian/SonarQube/Telegram/dashboard as our additions; choose native sync vs AI MCP read use per use case, not connector-name matching.

- Disposition team/shared workspaces, public highlights, comments/reactions, SSO/SCIM/audit policies, billing/referrals/courses/support as later or not planned with reasons.

- Define per-user content isolation, source-preview redaction on kiosk, raw payload/attachment/activity retention, AI disclosure controls and export/delete rights. Durable local cache is an intentional architectural difference.

## Done when

- Assign every F001–F110 row and every connector family an adopt/adapt/defer/reject disposition plus release stage, keeping owner tickets accountable for exact design.

- Write release exit scenarios: plan a realistic day, execute/record work, replan, shut down and glance at the TV while a provider is unavailable.

- Do not close undecided feature design tickets by scope assertion alone; deferred/rejected rows need explicit reasons and no implied schema implementation.
