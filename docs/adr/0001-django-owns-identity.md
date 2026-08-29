# Django owns identity; every client is equal

The SvelteKit scaffold arrived with a complete server-side stack — Better Auth issuing
cookies through `hooks.server.ts`, Drizzle over its own SQLite file, and a `task` table.
Django was to own the backend and its own database. That left two runtimes positioned to
own persistence and identity, with nobody having decided which.

**We decided that Django owns everything stateful** — users, authentication,
authorization, OAuth credentials, integration state, migrations, and background jobs —
and that every API consumer is a first-class client with no privileged position. The web
frontend calls the same versioned API a native client would; its Better Auth, Drizzle, and
SQLite stack is removed.

## Considered Options

**Better Auth as an identity provider, Django as a resource server.** Better Auth issues
JWTs and Django validates them via JWKS. A legitimate OAuth2-shaped architecture that
would have preserved existing work, rejected for two reasons: it makes a Node process a
hard runtime dependency of the whole system on a Raspberry Pi, and it keeps identity in
TypeScript while the product being built is a Django API — every future client would
traverse a Node hop that exists only for historical reasons.

**A third-party IdP** (Auth0, Clerk, Keycloak). Solves multi-user and SaaS properly, at
the cost of money or ops, and offloads a part of the system worth understanding directly.

**django-oauth-toolkit with Authorization Code + PKCE.** This was the initial choice, made
in anticipation of a future Swift client. Rejected because PKCE's browser round-trip and
consent step exist to let an authorization server delegate access to a client it does not
trust — and every client here is first-party. It would make shipping a native login form
harder than not shipping one. Note that PKCE is standard practice for *any* public native
client, first-party included; the objection is to the ceremony for a private application,
not to PKCE itself.

We use **django-allauth in headless mode** instead: a maintained account system with an
explicit `app` client type for native clients, covering login, verification, password
reset, social login, and later MFA. This is an implementation choice inside the decision
above, and is reversible — if third-party developers ever call this API,
django-oauth-toolkit layers on additively without allauth coming out.

## Consequences

- SQLite is not the datastore. Two runtimes writing one file was the original hazard;
  PostgreSQL is used from the start, and also serves the multi-user structure the schema
  assumes.
- Token transport differs by client while the auth system stays single: the web client
  uses HttpOnly session cookies via SvelteKit as a backend-for-frontend, a native client
  holds tokens in the Keychain. Prefer allauth's opaque, revocable token strategy over
  JWT until statelessness actually pays — a JWT cannot be withdrawn before it expires.
- "Sign in with Google" and "connect Google Calendar" must stay separate concerns. One
  user connects several accounts per provider (personal and work), so integration
  connections are many-per-provider-per-user, unlike allauth's `SocialAccount`.
