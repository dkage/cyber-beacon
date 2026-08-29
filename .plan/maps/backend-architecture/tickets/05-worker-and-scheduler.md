---
type: grilling
blocked_by: [03]
---

# Background worker and scheduler

## Question

**What runs the background work, and what schedules it?**

Blocked by the integration provider abstraction — the sync design determines what the queue is actually asked to do.

The workload: integration syncs, AI briefing generation, notifications, retries, and periodic polling. Note that **scheduling is not peripheral here** — the product's core loop is "poll these services on a cadence," so the scheduler is a primary component, not an add-on.

Memory is no longer a deciding factor. The earlier lean-queue argument assumed a constrained Pi; 8GB plus an available homelab removes it. Decide on ergonomics and on the scheduling story instead.

Candidates:

- **Celery + Redis** — heaviest, best-known, `beat` handles scheduling natively. The most written-about path.
- **Dramatiq + Redis** — nicer API, leaner, but **no built-in scheduler**; needs `dramatiq-crontab` or APScheduler bolted on.
- **Django-Q2** — scheduler integrated into Django Admin, which is genuinely pleasant for inspecting sync runs on a self-hosted box.

To resolve:

- Which queue, and the scheduler that goes with it.
- Where per-connection rate-limit budgeting is enforced, given Notion.
- Retry and backoff policy, and what a permanently failing sync does.
- Observability: how a failed sync surfaces to a human who is not reading logs.
- Whether the AI briefing shares this queue or wants its own, given very different latency and cost profiles.

## Done when

- The queue and scheduler are chosen, with the rejected options and reasons recorded.
- The enforcement point for rate limiting is named.
- The retry, backoff, and permanent-failure policy is written down.
- The mechanism by which a human learns a sync broke is decided.
- The AI briefing's queue placement is settled.
