---
type: grilling
claimed_by: s6cb86cf7c9c0
claimed_at: 2026-10-12T04:15:42Z
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
- **Where uploaded files live.** [The domain model](./02-domain-model.md) settled that attachments store a relative key through Django's storage layer, so local disk, a MinIO bucket on the homelab, or S3 are a settings change apart with no migration between them. Two concrete inputs: meeting audio recordings are large, and the Pi's SD card is the wrong place for them; and uploaded files are the one category of data that **no integration can re-sync**, which makes them the sharpest case in the backup question above.

## Done when

- The host for the backend is chosen, with the failure mode when it is unreachable stated.
- The remote-access approach is decided, or explicitly ruled out.
- The certificate strategy for non-local environments is settled.
- The compose service topology is written down per environment.
- The backup scope names what is irreplaceable versus re-syncable.
- The storage backend for uploaded files is chosen, and its location survives the backend host moving.

## Answer

**The backend runs on the TrueNAS homelab, in containers. The Pi is a thin kiosk.** All of the following was settled with the developer in this session.

### Host and runtime

- **Homelab hosts the backend and PostgreSQL**; the Pi runs only Chromium. Postgres sits on a ZFS dataset with snapshots, and the Pi keeps its whole 8GB for the 4K browser and does no database writes. The homelab is on 24/7.
- **Containers, not a VM.** Django, workers and Postgres together use well under 1GB against 64GB. The deployment is a TrueNAS custom app (Compose) with ZFS datasets as bind mounts. The `CLAUDE.md` rule of systemd units for workers is amended: systemd in a VM, or a Compose service with a `restart:` policy in a container. The *no supervisord* part stands.
- **Failure mode when the homelab is unreachable.** The frontend is served from the homelab, with a service worker caching the app shell and the last good API responses. A TV that is already on keeps showing the last-known schedule with a visible "stale since HH:MM" banner and retries quietly. A cold TV boot with the homelab down shows an error page, accepted as rare.

### Reachability and certificates

- **WireGuard only.** The phone and Mac already connect over the developer's WireGuard, so nothing is public. Cloudflare Tunnel was considered and not adopted. **Ticket 03's webhook flag stays off**, so Google Calendar sync is the five-minute poll. A later switch could expose only the webhook path through a tunnel; that is not decided here.
- **Certificates:** Zoraxy terminates TLS with Let's Encrypt DNS-01 through a Cloudflare API token, the pattern the SonarQube subdomain already uses. `beacon.<domain>` resolves through the router's DNS (the developer's TP-Link) to the homelab's private IP, so it works on the LAN and over WireGuard with nothing public.

### Compose topology

- **Dev (Mac):** only Postgres in Docker. Django and Bun run natively.
- **Prod (TrueNAS custom app):** `web` (Django behind gunicorn), `worker`, `scheduler` (left generic until ticket 05 picks the queue), `postgres`, `vault-sync`, and `frontend` (a static build behind nginx).
- Zoraxy stays outside the stack as the shared TLS terminator. On one hostname it routes `/api` to Django and `/` to the frontend, which keeps allauth's session cookies same-origin with no CORS.

### Obsidian vault

- Obsidian Sync (the developer's existing subscription) runs through a **`vault-sync` container**, the only read-write holder of the vault dataset.
- Obsidian ships an official Headless client, an open-beta npm package needing Node 22+. There is no official Docker image. The container is **our own small Dockerfile** (Node 22 slim, a pinned install, one vault, continuous sync). No community wrapper was adopted, because they would hold the Obsidian credentials.
- **Backend mounts:** the vault read-only, plus a nested read-write mount for `Journal/` only. Two writers never touch the same paths, so Sync conflicts cannot arise on the developer's own notes.
- **Recovery:** hourly ZFS snapshots of the vault dataset, plus Obsidian Sync's own version history.
- A custom MCP or service in front of the vault was considered and rejected: it would add a process and leave conflicts unchanged. Agent write access to the vault belongs to the map's "Agent-executed tasks" fog.

### Uploaded files

A **ZFS dataset mounted into the backend container**, with the host path as a Compose parameter, through Django's local storage. Files are stored under a relative key (ticket 02), so a move to MinIO or S3 later is a settings change. The location survives a backend move because it is a dataset that can be replicated or copied with the stack. MinIO was rejected as a service with no benefit at one user. S3 as primary was rejected because large meeting audio would cross the internet.

### Backups

- **Irreplaceable:** the Postgres local fields (time blocks, priorities, notes, completions, daily prep and wrap-up rows, journal text), all uploaded files, and the ADR-0003 credential-encryption key.
- **Re-syncable:** mirrored fields, tasks pulled from integrations, and cached state.
- **Method:** hourly ZFS snapshots locally, a nightly encrypted `pg_dump` to a versioned S3 bucket, and a TrueNAS Cloud Sync task for the uploads dataset. The encryption key also goes in the developer's password manager, separate from the DB dump.
- **Accepted off-box data-loss window: 24 hours.** WAL archiving was rejected as overkill for one user. No off-box backup exists today, so this scheme is new. Restores are manual, and the developer will track what was and wasn't backed up.

### Considered and not adopted

- **Pi hosts everything:** Postgres on SD or USB storage, with no snapshots, competing with Chromium for headroom.
- **AWS (ECS and Aurora)**, as a rough estimate only: about $95–110 a month with Aurora Serverless v2, about $60–70 with RDS `db.t4g.micro`, and about $15–25 for one small EC2 instance running Compose. Aurora's five-minute poll would defeat scale-to-zero. The pricing figures come from third-party sources and were not verified against AWS. The containers stay portable, so AWS remains a possible future move.
- **Cloudflare Tunnel for the whole app:** it puts the OAuth-token-bearing API behind a third party for no gain.

### For later tickets

- **Ticket 05:** the `worker` and `scheduler` slots are left generic. The queue choice must run as Compose services.
- **Not specified:** the Cloud Sync and `pg_dump` schedules and bucket lifecycle rules are implementation detail. The restore procedure is not written.
