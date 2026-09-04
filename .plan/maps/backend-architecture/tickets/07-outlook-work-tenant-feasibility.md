---
type: research
blocked_by: [03]
---

# Whether the work Microsoft tenant permits a third-party app registration

## Question

**Can this application be registered against the developer's work Microsoft tenant at
all, and with which scopes?**

Every other integration on the list is a decision or a diff. This one is a *fact nobody
has checked*, and it is the only item among the remaining providers that can turn out to
be impossible rather than merely unbuilt.

Microsoft Entra ID tenants can be configured to forbid users from registering
applications, and separately to require administrator consent before an application
receives any delegated permission. A work tenant with either setting on means the Outlook
work integration cannot be built without an administrator, regardless of how good the
provider abstraction is. Personal Outlook is unaffected and is an ordinary adapter.

This matters beyond Outlook: it is the first case where a Connection may be
*unobtainable* rather than merely broken, and the answer determines whether the
connections UI needs to say anything about that.

To find out:

- Whether user app registration is permitted in the tenant, or restricted to
  administrators.
- Whether admin consent is required for the delegated Graph scopes a calendar and mail
  integration needs (`Calendars.ReadWrite`, `Mail.Read`), and if so, what requesting it
  involves.
- Whether a single multi-tenant app registration can serve the personal account and the
  work tenant, or whether they are two registrations.
- What a rejected or revoked consent looks like to the running application — whether it
  is distinguishable from an expired token, given [ticket 03](./03-integration-provider-abstraction.md)
  separates `auth_dead` from `retryable`.

## Done when

- The tenant's app-registration and admin-consent posture is established as fact, not
  assumption.
- Personal and work Outlook are each classified as buildable, buildable-with-an-admin-ask,
  or blocked.
- If blocked, what the connections surface tells the user is decided, so the case is
  handled rather than presented as a bug.
