---
type: grilling
blocked_by: [04]
---

# Kiosk authentication

## Question

**How does the always-on kiosk authenticate to the API, and what is it allowed to see?**

[ADR-0001](../../../docs/adr/0001-django-owns-identity.md) settled two client shapes: the
web client uses HttpOnly session cookies through SvelteKit as a backend-for-frontend, and a
native client holds opaque, revocable tokens in the Keychain. The kiosk fits neither. It is
a Raspberry Pi running Chromium on a 4K TV with **no keyboard**, and it must sign in once,
stay signed in for months, survive reboots and power cuts, and be revocable if the Pi is
lost or the TV is moved.

[Ticket 04](./04-deployment-topology.md) settled reachability: access is WireGuard-only, the
backend runs on the homelab, and the kiosk has a service-worker cache for when the homelab
is down. That narrows who can reach the API; it does not say how the kiosk proves who it is
or what it may read.

### What is already settled and must not be re-decided

- Django owns identity and authentication; allauth headless is the sole account system, and
  every API consumer is a first-class client ([ADR-0001](../../../docs/adr/0001-django-owns-identity.md)).
- Integration tokens are never exposed to any client.
- Access is WireGuard-only, with TLS terminated at Zoraxy
  ([ticket 04](./04-deployment-topology.md)).
- Widgets read stored data and Snapshots, never a live provider call
  ([ticket 08](./08-task-or-widget.md)).

### To resolve

- The credential: a long-lived device token, a paired-device flow (code shown on the TV,
  approved from a signed-in phone), or something else, and how a keyboardless device
  obtains it the first time.
- Scope: the kiosk should read dashboard data and nothing else. Whether that is a distinct
  permission class, which routes it may call, and whether it may write at all (for example
  completing a Task from the TV).
- Lifecycle: expiry and rotation, where the credential is stored on the Pi, and how it is
  listed and revoked from the connections or settings surface.
- Multi-user: a kiosk belongs to one user's data today; how that binding is recorded so a
  SaaS future does not break it.
- What the kiosk shows when its credential is dead, given nobody is at the keyboard, and
  how that interacts with the service-worker cache from ticket 04.

## Done when

- The credential type, its first-time provisioning and its revocation are decided.
- The kiosk's permission scope is stated as a rule a route author can apply.
- Any new model or setting is named, so the first auth migration is complete.
