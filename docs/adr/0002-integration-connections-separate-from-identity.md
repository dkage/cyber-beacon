# Integration connections are separate from identity

[ADR-0001](./0001-django-owns-identity.md) settled that Django owns identity and that
django-allauth in headless mode is the account system. allauth also ships a complete
OAuth client: `SocialApp` holds the client credentials, the connect flow performs the
authorization-code exchange, and `SocialToken` stores the result. Connecting Google
Calendar through that machinery is the path of least resistance and it is the wrong one.

**We decided that an integration connection is its own model with its own OAuth client
code, holding its own credentials, with no foreign key to `SocialAccount`.** allauth
authenticates people; it has nothing to do with reading a calendar.

## Considered Options

**Connect through allauth's flow.** Rejected on a security property rather than a
modelling preference: allauth's connect flow creates a `SocialAccount`, and *every*
`SocialAccount` is a login credential. Connecting an employer-controlled Google account
so its calendar can be read would make that account a way to sign in to a personal
dashboard, and an administrator disabling it would become a login event. The two
lifecycles must not touch — "sign in with Google" and "connect Google Calendar" are
different things, which `CLAUDE.md` already records as a standing constraint.

**Reuse allauth's models, add our own fields.** `SocialToken` is unique on
`(app, account)` — one token row per application per account, carrying one scope set.
The real shape is two Google *connections* holding calendar scopes plus one Google
*identity* holding `openid email`: three credential sets across two accounts, one of
which must never grant a login. That constraint cannot express it.

**A foreign key to `SocialAccount` when the connection happens to reuse the login
provider.** A nullable relationship that is populated in one case and empty in the
other, whose only consumer would have to handle both. It buys nothing and it invites
exactly the coupling this decision exists to prevent.

## Consequences

- We write the authorization-code exchange ourselves, once, inside the sync engine —
  roughly the volume of code in a Laravel Socialite driver that does not exist yet. Each
  provider contributes `authorize_url`, `exchange_code`, `refresh`, and
  `account_identity`; nothing else.
- Client credentials for connecting are configured independently of allauth's
  `SocialApp` rows, so the same Google project can serve both purposes with different
  scopes without one flow's configuration changing the other's.
- Revoking or losing an integration connection cannot log anybody out, and cannot cascade
  into the account system, because there is no relationship along which it could.
- A connection is re-authorised by updating the existing row, matched on
  `account_identity` — the provider's stable account handle, Google's `sub` or Notion's
  `workspace_id`. Re-authorising with a *different* account is refused rather than
  accepted, since silently re-pointing a work connection at personal data produces
  records that look entirely legitimate afterwards.
- Adopting django-oauth-toolkit later, as ADR-0001 contemplates, remains additive: it
  concerns third parties calling *our* API, which is the opposite direction from this.
