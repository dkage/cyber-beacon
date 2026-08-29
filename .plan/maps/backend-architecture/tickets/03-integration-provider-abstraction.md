---
type: grilling
blocked_by: [02]
---

# The integration provider abstraction

## Question

**What shape does an integration have, such that adding the eighth one is boring?**

Blocked by the domain model: an integration's job is to project external things into local entities, so those entities must exist first.

Two providers are in scope here, chosen because they **stress the abstraction in opposite directions** — designing against only one produces something that breaks on the other:

- **Google Calendar** — bidirectional. Scheduling writes back, so conflict resolution is real, and push notifications are available instead of polling.
- **Notion** — read-heavy, with a punishing rate limit of roughly 3 requests/second average. Forces a polling budget, caching, and backoff as first-class concerns rather than afterthoughts.

To resolve:

- The provider interface every integration satisfies, and where per-provider quirks are allowed to live.
- **`IntegrationConnection` as a model distinct from allauth's `SocialAccount`.** Identity is one-per-provider-per-user; connections are **many** — this developer has personal and work Google accounts, personal and work Outlook. The lifecycles differ too: revoking calendar access must not log anyone out. The connection carries scopes, tokens, sync state, and rate-limit budget.
- **Credential encryption at rest.** OAuth refresh tokens in plaintext PostgreSQL columns is a liability once there is more than one user. Decide the field-level encryption approach and where the key lives — outside the database.
- Sync state and scheduling: full vs incremental, cursors, what "last synced" means, and what happens after a long outage.
- **Bidirectional conflict resolution** for Calendar: a local move versus a remote move of the same block.
- Failure and re-auth: what the user sees when a refresh token dies, scoped to the connection rather than the whole account.

## Done when

- The provider interface is specified: its methods, and what a new integration must implement.
- `IntegrationConnection`'s fields and its cardinality relative to `SocialAccount` are settled.
- The credential encryption mechanism and key location are chosen.
- The Calendar write-back conflict rule is stated concretely enough to implement.
- The rate-limit budgeting approach is defined and demonstrably survives Notion's limit.
- The remaining integrations in the map's *Not yet specified* have graduated into tickets, and that fog entry is cleared.
