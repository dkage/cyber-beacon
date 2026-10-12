# Microsoft Entra: app registration, consent, and what a dead grant looks like

Research for planning ticket 07 (the Outlook work tenant). Read 2026-10-12, all from
Microsoft Learn pages, cited per claim. **Not verified here:** the developer's actual
tenant settings. Nothing in this file touched the tenant; it records the documented
defaults and the five-minute check that turns them into fact (see the last section).

## 1. Can a user register an app in a tenant?

- By default, yes. "By default in Microsoft Entra ID, all users can register applications
  and manage all aspects of applications they create." An admin restricts this with
  **Users can register applications = No** and hands the right back out through the
  Application Developer role. [delegate-app-roles](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/delegate-app-roles)
- The failure is a clean message: "You don't have permission to register applications in
  the <directoryName> directory. To request access, contact your administrator." Same source.

## 2. Does the work tenant need to host our registration at all?

No. A registration lives in one *home* tenant; a multitenant one is usable from other
tenants. "Multitenant apps are available to users in both their home tenant and other
tenants." [single-and-multi-tenant-apps](https://learn.microsoft.com/en-us/entra/identity-platform/single-and-multi-tenant-apps)
So "can I register in the work tenant" is the wrong question: register in a tenant the
developer controls and let the work tenant only *consent*. App registration restrictions
then do not apply to us; consent policy does.

## 3. Consent: this is the real gate

- Default: users may consent to permissions that do not need admin consent, but "can't
  consent to allow an app unfettered access to read and write to all files".
  [configure-user-consent](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/configure-user-consent)
- The Graph permissions reference lists both `Calendars.ReadWrite` and `Mail.Read` as
  **AdminConsentRequired = No** for *delegated* use (Yes only for application
  permissions). [permissions-reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- **But tenant policy can be stricter than that flag.** The Microsoft-managed default,
  `microsoft-user-default-recommended`, is "also the default for a new tenant" and
  *excludes* from user consent, among others, Graph `Mail.Read`, `Calendars.ReadWrite`,
  `Calendars.Read`, `Tasks.ReadWrite`, `Contacts.ReadWrite`, and Exchange
  `EWS.AccessAsUser.All`. [manage-app-consent-policies](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-app-consent-policies)
  So in a tenant on current defaults, neither scope can be user-consented.
- A blocked user is "told to ask their admin for access"; if the **admin consent
  workflow** is enabled they can submit a request from the prompt. [application-consent-experience](https://learn.microsoft.com/en-us/entra/identity-platform/application-consent-experience)
- Admins can also disable user consent entirely ("Do not allow user consent"), and
  Application / Cloud Application Administrators can grant delegated consent.
  [delegate-app-roles](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/delegate-app-roles)
- Consequence: publisher verification does not rescue us. The recommended policy excludes
  these scopes regardless of publisher status (same manage-app-consent-policies page).

## 4. One registration or two?

One suffices. `signInAudience = AzureADandPersonalMicrosoftAccount` is "Any Microsoft
Entra directory ... and personal Microsoft accounts", and the authority `common` admits
both account kinds; `consumers` / `organizations` restrict to one.
[supported-accounts-validation](https://learn.microsoft.com/en-us/entra/identity-platform/supported-accounts-validation),
[v2-protocols-oidc](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc)
Costs of the combined audience: max two client secrets, max 30 permissions per resource,
no national clouds, shorter scope names. Same validation page. None bite this project.
Refresh tokens are "bound to a combination of user and client, but aren't tied to a
resource or tenant" ([refresh-tokens](https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens)),
so each account still gets its own `IntegrationConnection` with its own credentials,
consistent with ticket 03.

## 5. What a refused or dead grant looks like

Error codes, from [reference-error-codes](https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes)
unless stated:

| Situation | Signal |
|---|---|
| Consent needs an admin | `AADSTS90094` AdminConsentRequired; consent screen "ask your admin" |
| Consent never given / removed | `AADSTS65001` DelegationDoesNotExist: "Send an interactive authorization request" |
| User pressed cancel | authorize error `access_denied`; `AADSTS65004` UserDeclinedConsent ([v2-protocols-oidc](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc)) |
| Refresh token revoked (password reset by admin, "revoke sessions") | `AADSTS50173`, "a fresh auth token is needed" |
| Refresh token idle past lifetime | `AADSTS70008` / `AADSTS700082` (default lifetime 90 days, [refresh-tokens](https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens)) |
| Conditional Access now blocks or demands MFA | `AADSTS53003`, `AADSTS50076`, `AADSTS70043` |

Revocation specifics: a user changing their own password does **not** revoke a
confidential client's refresh token; the user revoking tokens, an admin revoking all
tokens, or an admin resetting the password in the Entra / M365 admin center does.
[refresh-tokens](https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens)

**Distinguishable from an expired access token?** An access token expiring is the normal
case and is handled by `refresh`; it is not an error at the token endpoint. Every row above
is a *refresh or authorize* failure, so all map to ticket 03's `auth_dead`, never
`retryable`. They are separable *within* `auth_dead` by code, which matters because the
remedy differs: 90094/65001 need an administrator, the rest need only the user to sign in
again. Not verified: the exact Graph-side HTTP status/body for an expired access token
(401); the adapter should treat that as "refresh once, then `auth_dead`".

## 6. Not established by this research

- The developer's work tenant's two settings (registration is irrelevant per section 2;
  **user consent policy** and **admin consent workflow** are what matter).
- Whether the tenant uses Conditional Access or tenant restrictions that would block a
  third-party client outside the consent model.
- The exact admin-consent request URL format; the sources read describe the endpoint but
  do not show it.
- Employer policy: consent technically available does not mean a personal tool reading
  work mail is permitted.

**To turn this into fact (no admin rights needed):** sign in to the work account and
start the connect flow with the real scopes from a test registration. Outcome A, a normal
consent prompt: buildable. Outcome B, "Need admin approval" / `AADSTS90094`: admin ask.
Optionally, Entra admin center > Enterprise apps > Consent and permissions shows the
policy if the developer has read access.
