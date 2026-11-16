---
type: grilling
blocked_by: [04, 06, 09]
---

# Capture, reminders, sharing and desktop/mobile scope

## Question

**How do tasks arrive and attention leave the planner without eroding WireGuard-only access or kiosk safety?**

F043, F076–F078, F092–F095, F103–F107. Backend 09 owns stale writes; 11 owns kiosk credentials; 12 owns static packaging. Those constraints apply to every proposed capture/delivery surface.

Read the [reference audit](../../../../docs/research/sunsama/README.md) and the
[feature inventory](../../../../docs/research/sunsama/feature-inventory.md). Recommendations
below are starting points for confirmation, not silently approved schema decisions.

### To resolve

- Define generic/source URL and deep-link capture now vs desktop global add/timer shortcuts/focus bar/menu tray later; web alone cannot supply OS-wide shortcuts.

- Decide forwarded-email ingestion or equivalent; address-secret rotation, sender/spam/size/rate limits and inbound mail gateway under private-network topology. Do not promise direct provider webhooks to a private host.

- Define Telegram notification vs inbound capture, Slack/Teams message actions and summary sharing, email delivery, destination privacy and allowed title/content exposure.

- Define ritual/timer/break/overdue/connection reminders, quiet hours, snooze/dismiss/escalate, multi-device dedupe and no full-screen strobe.

- Define focus presence/DND side effects and restoration on timer stop/crash/end-of-day; per-action consent and personal title privacy.

- Separate responsive web from native share sheet/Siri/Live Activities/Android notification/widgets; offline editing replay is not kiosk stale-cache mode.

## Done when

- Write delivery/capture event and permission contracts, ownership, retries and visible failure for each in-scope route.

- Resolve cross-map implications with backend 09/11/12; keep paired kiosk read-only if that remains its decision.

- Produce explicit now/later/not-planned client feature table; explain any new public ingress and obtain approval before topology changes.
