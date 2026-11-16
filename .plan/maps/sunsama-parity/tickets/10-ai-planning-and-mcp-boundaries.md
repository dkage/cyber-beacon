---
type: grilling
blocked_by: [03, 05, 06, 07]
---

# Briefing, optional AI planning, assistant and MCP

## Question

**Which AI roles are useful, what can they read/change, and how can a person inspect and undo the result?**

F029, F096–F102. Backend ticket 10 remains owner of stored briefing trigger/context/model/cost/failure decisions. Current Sunsama also has Autoplan, Sunny, recommendations and opposite-direction MCP integrations.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Keep manual planning fully functional; distinguish post-plan briefing, creation suggestions, agentic plan draft, conversational local assistant, remote MCP tool use and executing real-world work.

- Co-resolve backend 10: briefing input snapshots, finalization/revision trigger, skipped prep, schedule changes, storage/freshness, per-run budget and failure; do not make a conflicting second implementation plan.

- For AI drafting, define allowed sources/accounts, standing rules/expiry, weekday themes, capacity constraints and proposal/change-set lifecycle. Recommend review before committing; note Sunsama currently applies changes and offers undo.

- Define action provenance, judgment-call review, partial/whole undo with version checks, cancellation and concurrent human edits; don't overwrite newer data with an inverse patch.

- Separate external assistants calling our MCP API from our assistant consuming external MCP tools. Default-deny sensitive source access and writes; explicit grants/allow-once/ask/never, revocation and SSRF/tool-trust boundaries.

- Define retention, AI disclosure/opt-out, recommendations toggles, conversation history and safe degradation. n8n/Hermes execution is distinct and stays later unless explicitly brought in.

## Done when

- Publish a capability/data/action matrix for each AI role, staged by release, with costs and non-AI fallback.

- Resolve backend 10's briefing question and link one canonical answer; amend any no-live-provider-generation rule explicitly rather than silently expanding it.

- Test stale plan review, partial failure, undo after human edit, denied tool action and secret leakage; update vocabulary only after decisions settle.
