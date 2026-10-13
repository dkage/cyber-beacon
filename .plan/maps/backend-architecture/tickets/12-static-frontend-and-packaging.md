---
type: prototype
blocked_by: [04]
undermined_by: []
---

# Static SvelteKit frontend served by Django, and one-image packaging

## Question

**Can the web client be a static SvelteKit build served by Django from the same origin,
using Django's own session cookie, and can the whole backend ship as one image?**

[ADR-0001](../../../docs/adr/0001-django-owns-identity.md) wrote the web client as "HttpOnly
session cookies via SvelteKit as a backend-for-frontend", which keeps a Node server in
production. The ADR records no reason for the BFF. It is a *backend-for-frontend*: a small
server between the browser and the API that holds the credential on the browser's behalf.
The frontend is meant to be a pure API client, so it can be static files with no server
runtime, and the native Swift client is unaffected because allauth headless gives it a
separate app client with tokens against the same API.

The generated scaffold still carries a server stack (`hooks.server.ts` Better Auth handle,
`src/lib/server/`, Drizzle) that the existing removal follow-up already plans to delete.

### What is already settled and must not be re-decided

- Django, DRF, allauth headless and Django-Q2 stay; the language is not reopened.
- Django owns identity; every client is first-class
  ([ADR-0001](../../../docs/adr/0001-django-owns-identity.md)). A native client uses opaque,
  revocable tokens.
- Production is containers on the TrueNAS homelab, WireGuard-only, with Zoraxy terminating
  TLS and routing `/api` and `/` on one hostname ([ticket 04](./04-deployment-topology.md)).
- Two worker clusters (`worker`, `worker-ai`) on the Postgres ORM broker
  ([ticket 05](./05-worker-and-scheduler.md)).

### To prove or decide

- `adapter-static` with SSR off and an SPA fallback: deep links and a hard refresh on a
  nested route work when served by Django (WhiteNoise or a catch-all view) and behind Zoraxy.
- Login, logout and a state-changing request using allauth headless's browser client from the
  static app: where the CSRF token comes from, the header name, cookie `SameSite`, `Secure`
  and `HttpOnly` settings, and what a 403 looks like to the client.
- The same exercise through the dev setup (Vite dev server against Django) so local
  development works, and what proxying that needs.
- One image run as `web` and `worker` services next to Postgres under Compose: static build
  stage, `collectstatic`, migrations on start, and image size.
- The service-worker cache from ticket 04 for the kiosk, serving a static build.
- What ADR-0001 needs amended, and whether to write a new ADR or edit it.

## Done when

- A working spike (kept outside production code) shows login, a CSRF-protected write, a deep
  link refresh, and a `docker compose up` bringing up web, worker and Postgres.
- The session and CSRF behaviour is written down as a rule a frontend author can follow.
- The ADR-0001 change is named, with the reason the BFF was or was not kept.
