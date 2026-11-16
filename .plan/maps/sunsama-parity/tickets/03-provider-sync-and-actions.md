---
type: grilling
blocked_by: [02]
---

# Per-provider field policies, remote commands and automations

## Question

**What exactly is copied, kept local, read continuously, or written upstream for each initial provider?**

Rows F011, F013–F019, F023–F030, F102. The [provider matrix](../../../../docs/research/sunsama/integration-semantics.md) distinguishes GitHub independence, Jira copy-on-import/status prompts, Notion property actions and mail triage. Backend tickets 02/03's no-write rule and 08's generic resolved completion conflict.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- For Notion, Google Calendar, Gmail, GitHub and Outlook, specify a field-by-field table: copy-on-import, local, remote preview, continuous read, explicit command, optional automation. Retain upstream state without universally completing worksheets.

- Design remote action descriptions, valid transition choices, ordered/conditional automations, prompts and granted-scope/resource-permission checks; avoid provider identity branches in shared orchestration.

- Specify local completion/reopen vs remote success/failure; durable outbound intents, ambiguous results, safe retries and user-visible repair. No automatic mail resend or repeated destructive action.

- Design export vs copy, destination selection, field losses, remote creation before local removal and compensating undo; explicitly stage complex exporters if not initial scope.

- Define content minimization, raw/source-preview/Snapshot/remote-activity retention and privacy. Our durable server cache is intentional, not Sunsama's browser-cache architecture.

- Review Gmail/Outlook action/send scopes and tenant consent, independent from login; build-time scope facts come from provider docs, not a possibly stale Sunsama privacy table.

## Done when

- Specify direction, trigger, opt-out, scope, reopen and failure for every in-scope field/action; no generic two-way-sync label.

- Pass resolved-PR-still-open, partial mail automation, offline Notion completion and export timeout scenarios.

- Amend backend 02/03/07/08, relevant glossary and any affected ADR with explicit approval; unchanged infrastructure policies remain ours, not alleged Sunsama internals.
