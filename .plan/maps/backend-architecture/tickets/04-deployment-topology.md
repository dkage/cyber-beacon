---
type: grilling
---

# Deployment topology: Pi, homelab, and reachability

## Question

**Where does the backend actually run?**

Two machines are available, and the obvious answer may be the wrong one:

- **Raspberry Pi 5, 8GB**, driving a 4K TV as the always-on kiosk.
- **Xeon homelab, 64GB, TrueNAS.**

The Pi is not a comfortable host for both roles. Chromium rendering a 4K dashboard permanently costs roughly 500MB–1GB, plus 400–600MB for a desktop session; the Django stack with workers adds roughly 300–620MB depending on the queue. It fits in 8GB, but browser and backend compete for the same headroom, and PostgreSQL on SD or USB storage is a wear problem with no snapshot story.

Running the backend on the homelab frees the entire Pi for the browser and puts PostgreSQL on ZFS with real snapshots.

To resolve:

- Pi-hosts-everything, versus homelab-hosts-backend with the Pi as a thin kiosk.
- **Homelab availability** — is it always on, and what does the TV show when it is not?
- **Reachability away from home.** The dashboard is meant to be a phone home screen too: Tailscale, Cloudflare Tunnel, or nothing.
- HTTPS and certificates outside local development.
- Docker Compose topology, and what runs natively versus containerised in each environment.
- Backups: what is genuinely irreplaceable once integrations can re-sync from source.

## Done when

- The host for the backend is chosen, with the failure mode when it is unreachable stated.
- The remote-access approach is decided, or explicitly ruled out.
- The certificate strategy for non-local environments is settled.
- The compose service topology is written down per environment.
- The backup scope names what is irreplaceable versus re-syncable.
