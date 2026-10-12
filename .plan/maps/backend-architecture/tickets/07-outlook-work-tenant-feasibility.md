---
type: research
blocked_by: [03]
claimed_by: s0765fc53a899
claimed_at: 2026-10-12T15:34:11Z
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

## Answer

Findings, with every claim cited to Microsoft Learn, are in
[`docs/research/microsoft-entra-app-registration-and-consent.md`](../../../../docs/research/microsoft-entra-app-registration-and-consent.md).

**Caveat first: the developer's actual tenant was not inspected.** What is established is
the documented behaviour and defaults; the two tenant settings that matter are left as a
five-minute check (below). "Established as fact" in *Done when* is met for the platform,
not yet for the tenant.

**The question was slightly the wrong one.** App registration need not happen in the work
tenant. A multitenant registration lives in a tenant the developer controls, and the work
tenant only ever sees *consent*. So "can users register apps" does not gate us; **user
consent policy** does.

**Consent is the real gate.** `Calendars.ReadWrite` and `Mail.Read` are not admin-consent
permissions in the Graph reference (delegated). But the Microsoft-managed default consent
policy, which is the default for a new tenant, excludes both from user consent. In a
tenant on current defaults, a user cannot consent to either, and an administrator must.
Publisher verification does not change that.

**One registration serves both accounts**, with `signInAudience =
AzureADandPersonalMicrosoftAccount` and the `common` authority. Each account is still its
own `IntegrationConnection` with its own credentials, as ticket 03 already has it.

**Classification**

- Personal Outlook: **buildable.** An ordinary adapter; no tenant is involved.
- Work Outlook: **buildable-with-an-admin-ask**, under default tenant policy. Becomes
  plain *buildable* if the tenant lets users consent, and *blocked* only if the
  administrator refuses (or the employer's policy forbids it, which is not a technical
  question). It is not blocked by app registration rules.

**Dead grants.** Every consent or token failure is a refresh/authorize failure, so all
map to `auth_dead`, none to `retryable`. An expiring access token is not one of them. The
codes split `auth_dead` into two remedies: `AADSTS90094` / `65001` need an administrator;
`50173`, `70008`, `700082`, `53003`, `50076`, `70043` need only the user to sign in again.
The adapter's `classify` should put the code in `last_error` so the two can be told apart.

**What the connections surface says (decided, reversible).** Obtaining a Connection can
fail at the consent step, before any `IntegrationConnection` row exists, so this needs
**no new `status` value**; it is the result of a connect *attempt*, not a Connection state.
On `AADSTS90094` or an "ask your admin" return, the connect flow shows "Your organisation
requires an administrator to approve this app", with what is being asked for and why, and
a copyable text to forward to the administrator. It is shown as an expected outcome, not
an error. Re-running the connect after approval takes the normal path. A *revoked* consent
on an existing Connection is the ordinary `needs_reauth`, with `last_error` saying an
administrator is needed. Ticket 03's reauth rules apply unchanged.

**To close the tenant gap:** sign in to the work account against a test registration
with the real scopes. A normal consent prompt means buildable; "Need admin approval" means
the admin ask. Nothing needs admin rights to find out.

**Omitted.** The admin-consent request URL format (not shown by the sources read), the
exact Graph 401 body for an expired access token, Conditional Access or tenant-restriction
posture, and whether employer policy permits the integration at all.
