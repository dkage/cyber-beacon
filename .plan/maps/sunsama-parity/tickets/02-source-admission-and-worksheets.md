---
type: grilling
blocked_by: [01]
---

# Source browsing, intentional import and worksheet identity

## Question

**How do remote candidates become local Tasks without turning every connected service into a second Backlog?**

Feature rows F001–F012, F020–F022, F028, F083 and F087. Backend tickets 02/03/08 assume filtered projection, mirrored titles/due dates and reconciliation by external identity. Sunsama offers source panels, explicit import, editable local worksheets and repeated Jira imports.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### Decided in ticket 13

Explicit import is the normal interaction; imported Tasks are local worksheets. The remaining questions below are the identity/dedupe and field-ownership details, not the admission model itself.

### To resolve

- Decide whether automatic Task projection remains an opt-in per Mount, and what safe defaults replace mirrors=true.

- Separate remote identity from worksheet ID; allow intentional multiple work units while deduplicating retry/import requests and cross-Mount overlap. Decide whether TaskSource is a remote-record entity or a per-worksheet link.

- Specify browse/search/filter/group/sort, paging, freshness and already-imported flags independently of Snapshot. Browsing may be server-cached without creating Tasks.

- Specify local title/notes/due/estimate ownership and import snapshots; source preview still shows current remote fields. Preserve independent do/due/actionability dates.

- Define email account/message/thread identity, new-reply indicators and follow-up choices; GitHub notification → issue links without accidental cross-account dedupe.

- Define paste-URL recognition, connect-required flow, generic-link fallback and server-side SSRF defenses. Merge/import-as-subtask retains provenance and time; specify duplicate/template behavior.

## Done when

- Write entity cardinalities, uniqueness and idempotent import API/read-model contracts; no private client logic.

- Walk the integration-semantics scenarios for Jira repeat work, Notion rename, Gmail new reply, retry and overlapping Mounts.

- Amend backend 02/03/08 plus CONTEXT.md/glossary only after approval; candidate/source-browser terminology must not redefine Backlog or Promotion accidentally.

## Phase 1 implementation disposition (2026-11-18)

The developer authorized autonomous implementation of the entire First usable day.
[The bounded release contract](../../../../docs/phase-one-contract.md) resolves this
ticket's Phase 1 slice and supersedes conflicting historical premises for that slice.
Broader release/parity questions above remain open. Verification and any limitations
are recorded with the implementation; the packaging proof is not claimed in advance.
