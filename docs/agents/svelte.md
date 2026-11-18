# SvelteKit client conventions

Read this before changing frontend routes, components, API access, authentication UI,
planner interactions, kiosk behavior or frontend tests. These are Cyber Beacon
conventions; the linked framework documentation supplies mechanics.

## Start with the owning contract

1. Read `CLAUDE.md`, the relevant live issue and its linked planning tickets. Identify
   the behavior approved for this slice and any unresolved design gate before coding.
2. Inspect `frontend/CLAUDE.md`, the package manifest, lockfile and configuration for
   installed versions, available tools and executable commands. Use documentation that
   matches those versions; current online examples may target a newer SvelteKit major.
3. Find the nearest implemented example. The generated demos are tooling examples,
   not evidence of approved architecture or implemented product behavior.

Architecture and release sequencing live in [CLAUDE.md](../../CLAUDE.md). The frontend
cleanup is [issue #9](https://github.com/dkage/cyber-beacon/issues/9); until it lands,
the scaffold's Better Auth, Drizzle, SQLite and server modules are removal targets.
Follow the static API client direction. Keep production behavior independent of a
SvelteKit server: Django handles persistence, authorization and domain commands.

## Find the domain before designing the screen

Use this table to find contracts, then read the current issue and owning ticket.
Issue labels alone miss frontend work: Notion and Calendar issues also require UI.
This is a routing index, not a replacement specification or implementation checklist.

| Surface or operation | Buildable work | Decision owner |
|---|---|---|
| Static delivery and login/logout | [#9](https://github.com/dkage/cyber-beacon/issues/9), [#12](https://github.com/dkage/cyber-beacon/issues/12) | [Backend 12: packaging and browser session proof](../../.plan/maps/backend-architecture/tickets/12-static-frontend-and-packaging.md) |
| Today, Task forms, do-date assignment, ordering and completion | [#13](https://github.com/dkage/cyber-beacon/issues/13), API [#11](https://github.com/dkage/cyber-beacon/issues/11) | [Parity 09: planner surfaces](../../.plan/maps/sunsama-parity/tickets/09-planner-surfaces-and-dashboard.md), [backend 09: mutation contracts](../../.plan/maps/backend-architecture/tickets/09-task-lifecycle-on-our-api.md) |
| Connections, Mounts, Notion browsing/import and Calendar events | [#14](https://github.com/dkage/cyber-beacon/issues/14), [#15](https://github.com/dkage/cyber-beacon/issues/15) | [Parity 02: worksheets](../../.plan/maps/sunsama-parity/tickets/02-source-admission-and-worksheets.md), [03: provider actions](../../.plan/maps/sunsama-parity/tickets/03-provider-sync-and-actions.md) |
| Estimates, persisted order, work hours and capacity | [#16](https://github.com/dkage/cyber-beacon/issues/16) | [Parity 05: capacity and scheduling](../../.plan/maps/sunsama-parity/tickets/05-capacity-projections-and-timeboxing.md) |
| Running timer and actual Time entries | [#17](https://github.com/dkage/cyber-beacon/issues/17) | [Parity 06: actual time](../../.plan/maps/sunsama-parity/tickets/06-time-entries-and-focus-state.md) |
| Day refresh after midnight carry-forward | [#18](https://github.com/dkage/cyber-beacon/issues/18), Today/kiosk consumers | [Parity 04: day lifecycle](../../.plan/maps/sunsama-parity/tickets/04-day-lifecycle-and-meetings.md) |
| Kiosk day view, freshness and failures | [#19](https://github.com/dkage/cyber-beacon/issues/19) | Parity 09; [backend 11: kiosk authentication](../../.plan/maps/backend-architecture/tickets/11-kiosk-authentication.md) |
| Internal calendar, projections, commit/undo, calendar controls and auto-scheduling | [#20–#24](https://github.com/dkage/cyber-beacon/issues?q=is%3Aissue%20number%3A20..24) | Parity 05 |

For Board, Focus, rituals, weekly objectives, Backlog/archive, recurrence, capture,
notifications or AI surfaces, follow the relevant branch of the
[parity map](../../.plan/maps/sunsama-parity/map.md). A planning question or reference
feature does not authorize adding that surface to the current release.

## Components and state ownership

- Keep route files responsible for URL state, data loading and page composition.
  Place reusable presentation and feature logic under `$lib`, grouped by cohesive
  responsibility; establish folders as features appear rather than scaffolding every
  future domain. Keep transport details out of presentation components.
- Use Svelte 5 runes for new components: typed `$props`, `$state` for mutable UI state,
  and `$derived` for computed values. Use callback props for component events and
  snippets for supplied markup. Reserve `$bindable` for intentional two-way interfaces.
- Keep state with its owner. Pass values and callbacks through props; use typed context
  when a component subtree needs shared feature state. Reuse existing stores when they
  fit. Introduce an application-wide store or query library for a demonstrated shared
  lifecycle, with explicit invalidation and reset behavior.
- Treat props and API results as inputs. Edit a deliberate draft and submit an explicit
  command instead of mutating an ancestor's object through a child. Key Task lists by
  stable Task IDs so reorder preserves focus and draft identity.
- Put navigable day, selection and filters in the URL when they should survive reload
  or sharing. Keep transient dialogs and drag previews local. SvelteKit can reuse route
  components: react to changed parameters/data and reset drafts deliberately rather
  than assuming every navigation mounts a new component.
- Use effects to synchronize with external systems, such as a chart, timer display or
  event listener. Compute derived values with `$derived`; send writes from explicit
  actions. Clean up subscriptions, timers and listeners when their owner is destroyed
  or dependencies change. Account for effects tracking synchronous reads only.

## API, authentication and mutation feedback

Keep a shared transport boundary for API URLs, credentials/CSRF handling, response
parsing and error normalization. Use the `fetch` supplied to SvelteKit load functions
for route reads; use the same transport conventions for interaction-driven requests.
Cancel or discard obsolete reads so navigating days or changing source searches cannot
replace current results with an older response.

- Align domain request/response types with Django's OpenAPI schema. Use the project's
  generation workflow when available; establishing one belongs to contract setup.
  Keep allauth's separate API contract explicit. TypeScript types alone do not validate
  network data or prove an operation succeeded.
- Handle HTTP failure before treating a body as success, including empty responses
  and non-JSON failures. Map field validation to the relevant controls and distinguish
  authentication, permission/CSRF, conflict and network failures according to the API.
- Render Task notes, Source previews and API error text as untrusted content. Keep
  Svelte's escaping; rich text needs deliberate sanitization and safe link protocols
  before rendering HTML.
- Follow allauth's **browser** client contract for web sessions and its returned
  authentication flows. Keep session credentials in Django-managed cookies; browser
  token storage is not a substitute for the planned session/CSRF flow. Clear user-scoped
  data and pending work on logout or account change.
- Resolve token bootstrap, login/logout rotation, headers, development proxy behavior
  and static deep links through backend ticket 12 and issue #12. Keep CSRF enforced;
  send its token only to the trusted backend. Treat route guards as navigation UX;
  Django authorizes every operation.
- Give reads explicit loading, empty, error and stale states. Preserve usable last-known
  data during refresh while showing its freshness. Give writes pending, success and
  failure feedback, retain the user's draft on failure, and prevent accidental duplicate
  submissions.
- Use optimistic updates only where the settled mutation contract supports recovery.
  Restore or refetch canonical state on rejection; reconcile overlapping commands so
  an older rollback cannot erase a newer edit. Follow backend 09 for stale-write rules
  and the owning ticket for undo/idempotency rather than inventing client-only replay.

Static delivery still needs the packaging proof. Keep browser-only APIs behind browser
lifecycle boundaries, since build tooling can evaluate imports. Prove fallback behavior
on the actual serving stack; unknown API routes and missing assets must retain their
proper responses. API writes go to Django rather than SvelteKit form actions or server
endpoints that would require a production SvelteKit runtime.

## Planner semantics at the client boundary

Use [CONTEXT.md](../../CONTEXT.md) terms in types and interactions. Frontend feedback
may preview a command, while server operations and read models remain authoritative.

- Keep do, due and start dates as local calendar date values end to end. Avoid converting
  a date-only string through a UTC `Date` and back. Format instants in the intended user
  timezone; account for DST and midnight when grouping the timeline.
- Render local worksheet fields separately from the Source preview. Browsing does not
  create Tasks; importing is explicit. Completion updates the local Task; a provider
  action needs its own command, permissions and pending/failure feedback. Keep Connection
  management separate from signing in, including multiple accounts at one Provider.
- Keep Calendar events, proposed Task placement, committed Time blocks and actual Time
  entries distinct in types and visual treatment. A preview does not publish a calendar
  change. Use server-owned capacity/scheduling contracts; client rendering must not
  become a second scheduling engine with different rules.
- Show a running timer from authoritative state and elapsed timestamps, not by counting
  interval callbacks as recorded work. Refresh after sleep, reconnect and relevant
  visibility changes. The backend owns start/stop, actual totals and cross-day attribution.
- Refresh day state after rollover; the server performs carry-forward. Wrap-up remains
  optional. Reconcile changed dates/order from the response instead of implementing a
  browser-side midnight mutation or gating Today on a ritual.

## Interaction, identity and the kiosk

Apply the identity constraints in the parity map through shared tokens and components.
Keep semantic color consistent and accompany it with text or icons: amber attention,
cyan external state, magenta AI, green healthy/done and red late/failure. Maintain legible
monospace text, contrast, font scaling and reduced-motion behavior.

Use native buttons, links and labeled form controls. Preserve visible keyboard focus,
dialog focus return and descriptive page titles. Give reordering and scheduling a
keyboard path and a click/tap alternative to dragging. Keep shortcuts out of text-entry
contexts and make destructive actions discoverable without a shortcut. Address compiler
accessibility warnings at the semantic cause; suppression needs a concrete justification.

The kiosk consumes the same domain through suitable read models and stored Snapshots,
with distance-calibrated density and visible last-success/failure information. Its
cache is a passive stale view, not an editable offline planner. Scope credentials,
redaction and cached-data handling on revocation through backend ticket 11; a hidden
button is not an access boundary. For polling or other refresh mechanisms, clean up
work, avoid overlapping requests and back off failures rather than hammering an outage.

## Verification and delivery

Discover commands from package scripts, configuration and CI; use Bun as the project
package manager. Run the configured type/Svelte checks, formatting/lint checks and build
for frontend changes, with focused behavioral tests proportional to the risk.

- **Vitest:** pure formatting/state helpers and component behavior. Use the configured
  browser project for DOM interactions; assert rendered results and accessible controls.
- **Storybook:** reusable components and meaningful states such as empty, pending,
  validation failure, stale and narrow/kiosk presentation. Fixtures follow API contracts
  and require no live Provider credentials.
- **Playwright:** critical user journeys, keyboard/touch alternatives and relevant
  refresh/navigation behavior. Prefer role/label locators and retrying assertions over
  CSS internals and arbitrary sleeps. Isolate test data and replace external Provider
  calls with controlled fixtures.

Keep a real Django/browser integration check for login/logout and CSRF; mocked responses
cannot prove cookie or proxy behavior. For delivery changes, verify a nested-route hard
refresh on the intended static host. For planner changes, select relevant cases such as
rejected reorder, rapid day navigation, date-only values across timezones, timer recovery
or kiosk stale/reconnect behavior. Report checks run and any unavailable verification.

## References

Check installed versions before applying examples. These official sources explain
framework behavior; project contracts above determine product scope and ownership.

- Svelte [runes](https://svelte.dev/docs/svelte/what-are-runes),
  [effects](https://svelte.dev/docs/svelte/$effect) and
  [context](https://svelte.dev/docs/svelte/context): reactivity and component ownership.
- SvelteKit [state management](https://svelte.dev/docs/kit/state-management),
  [loading data](https://svelte.dev/docs/kit/load),
  [single-page apps](https://svelte.dev/docs/kit/single-page-apps) and
  [static adapter](https://svelte.dev/docs/kit/adapter-static): navigation and delivery.
- [allauth headless API](https://docs.allauth.org/en/latest/headless/openapi-specification/)
  and [Django CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/): browser sessions
  and protected writes; backend ticket 12 owns the tested project configuration.
- [SvelteKit accessibility](https://svelte.dev/docs/kit/accessibility) and
  [WCAG dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html):
  navigation, focus and alternatives to dragging.
- [Vitest browser testing](https://vitest.dev/guide/browser/)
  and [Playwright best practices](https://playwright.dev/docs/best-practices): observable
  behavior, isolation and browser assertions.
