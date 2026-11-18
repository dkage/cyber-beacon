# Django API conventions

Read this before changing backend models, APIs, authentication, jobs or tests. These
are Cyber Beacon conventions, informed by the references below; services and selectors
are project choices rather than requirements imposed by Django.

## Start with the owning contract

1. Read `CLAUDE.md` and the relevant issue, ADR and planning ticket. Follow its design
   gates; a convention here does not settle missing product behavior.
2. Inspect the actual backend, dependency lockfile and configuration. At the time this
   guide was introduced, `backend/` still held the abandoned Go scaffold. Resolve Python,
   Django and dependency versions during the Django foundation work (`#8`), and update this
   guide with the concrete app layout and test/lint/schema commands once `#8` lands.
3. Find the nearest implemented example of the same operation. Follow its conventions
   unless the task calls for changing them; explain any necessary departure.

Architecture boundaries and settled stack live in [CLAUDE.md](../../CLAUDE.md#architecture);
browser session/CSRF and static delivery details remain subject to
[backend ticket 12](../../.plan/maps/backend-architecture/tickets/12-static-frontend-and-packaging.md).

## Domain apps and placement of logic

Keep Django apps and models aligned with [`CONTEXT.md`](../../CONTEXT.md) vocabulary and
cohesive domain responsibilities. Start with ordinary modules; turn a module into a
package when its size or responsibilities justify it.

| Location | Responsibility |
|---|---|
| `models.py` | Persistence, database constraints and cohesive instance behavior |
| `querysets.py` or `managers.py` | Composable, reusable ORM queries and visibility scopes |
| `services.py` | Business workflows, state transitions and transaction boundaries |
| `selectors.py`, when useful | Substantial read operations, projections or queries spanning models |
| `serializers.py` | Explicit API input/output fields and transport validation |
| `views.py` | HTTP orchestration, permissions, serialization and responses |
| `tasks.py` | Thin queue entry points invoking services or integration engines |

Services use domain arguments and explicit actor/owner context where authorization
depends on it, rather than accepting a DRF request or returning a DRF response. Keep
business invariants shared by API, jobs and admin paths in the domain operation, with
database constraints where applicable. Avoid duplicating them in each caller.

Use services for meaningful workflows; simple CRUD can use DRF's normal hooks when
there is no shared workflow to extract. Add a selector when it provides a useful read
interface, rather than wrapping every QuerySet call. Prefer explicit calls over signals
for business workflows so execution and failure handling remain visible.

Use lazy string references for model relationships across apps. Reference the user
model with `settings.AUTH_USER_MODEL` in model fields and `get_user_model()` when the
model class is needed at runtime. In data migrations use historical models from
`apps.get_model()`.

## API contract for the SvelteKit client

- Put domain endpoints under `/api/v1/` and name routes for reverse lookup. Follow
  allauth's own routing contract for authentication endpoints.
- Use DRF serializers to validate bodies and typed query parameters. Declare writable
  fields explicitly. Keep ownership, credentials and internal synchronization state
  outside client-writable fields.
- Use ViewSets/generic views for resource operations where they fit. Use explicit
  actions or APIViews for domain commands; keep orchestration small in either case.
- Use separate input/output serializers when their fields or validation differ; avoid
  multiplying classes without a concrete distinction.
- Describe request/response serializers, parameters, named enums/components and material
  error responses in `drf-spectacular`. Use explicit `operation_id`s where needed and keep
  schema generation warning-free so SvelteKit and future native clients generate cleanly.
- Use bounded pagination and deterministic ordering with a tie-breaker on collection
  endpoints. Allowlist filters and ordering fields; bound expensive input sizes.
- Return consistent DRF validation and permission errors. Define any shared exception
  shape centrally and document it in the schema. Sanitize errors and logs so credentials
  and provider secrets are never exposed.
- Keep GET/HEAD free of domain mutations. Enforce authoritative rules server-side even
  when Svelte supplies immediate client-side feedback.
- Follow the domain distinction between local calendar dates and instants in
  `CONTEXT.md`; serialize dates and timezone-aware datetimes consistently in the schema.

Before Task migrations or mutation contracts, resolve the applicable gates in
[backend ticket 09](../../.plan/maps/backend-architecture/tickets/09-task-lifecycle-on-our-api.md).
This guide does not select stale-write, deletion, undo or offline replay semantics.

## Authentication and per-user access

Require authenticated access by default for domain APIs. Declare public exceptions
explicitly, such as sign-in flows or verified provider callbacks.

- Scope querysets to the actor's permitted data for lists, detail lookups, updates and
  deletes. `IsAuthenticated` alone does not establish ownership.
- Validate ownership/access for related object IDs supplied by the client. Assign the
  owner from trusted server context rather than accepting a submitted owner ID.
- Enforce operation-specific permissions as well as visibility. DRF object permissions
  are not automatically applied to each list result or during creation. Custom object
  lookup code must preserve the appropriate permission checks.
- Apply equivalent ownership boundaries to selectors, services and background jobs;
  pass stable IDs and load the authorized records rather than trusting client objects.
- Preserve CSRF protection for browser cookie authentication, including login/logout
  as required by the chosen auth flow. Follow the proven allauth/session contract when
  ticket 12 closes rather than weakening CSRF or broadening CORS for local development.
- Verify webhook authenticity according to the provider protocol before processing
  it. Limit any CSRF exemption to the endpoint that uses that alternative verification.

For provider connections and credentials, read
[ADR-0002](../adr/0002-integration-connections-separate-from-identity.md) and
[ADR-0003](../adr/0003-credential-encryption-at-rest.md) before changing auth or sync
models:

- **Connections vs identity (ADR-0002):** Implement provider connections on our own
  connection model and OAuth client; keep `django-allauth` (`SocialApp`, `SocialAccount`,
  `SocialToken`) strictly for user sign-in.
- **Credentials at rest (ADR-0003):** Store provider tokens as an opaque JSON blob in the
  project's `MultiFernet`-backed field (`settings.FERNET_KEYS`) rather than adding
  third-party Fernet packages or `pgcrypto`. Keep searchable user content (`notes`,
  `TaskSource.raw`) in plaintext.

## ORM, validation and transactions

- Fetch relationships the operation actually uses. Use `select_related()` for suitable
  single-valued relationships and `prefetch_related()` for collections; inspect serializer
  access too. Measure representative queries and add a regression assertion when query
  growth is a material risk. Avoid unconditional eager loading on every query.
- Use database uniqueness/check constraints for invariants the database can enforce.
  Serializer validation improves errors but cannot prevent concurrent writers racing.
  `Model.save()` does not call `full_clean()` automatically; choose validation entry
  points explicitly. Account for `update()`/bulk operations bypassing model `save()`
  and its signals.
- Use `transaction.atomic()` for writes that must succeed or roll back together. Keep
  transactions short and avoid holding locks during external HTTP/LLM calls.
- Treat atomicity and concurrency control separately. Use conditional updates, `F()`
  expressions or row locks where the settled operation requires them; `atomic()` alone
  does not prevent lost updates. Follow the owning contract for client preconditions.
- Schedule callbacks with `transaction.on_commit()` when they must observe committed
  data. A callback is not a durable delivery guarantee: persist recoverable intent when
  losing a dispatch would lose required work.
- Prefer ORM expressions and parameterized queries. Use raw SQL when there is a concrete
  need, with bound parameters and tests for its behavior.

Use synchronous DRF and ORM workflows as the starting point. Introduce async only for
a concrete benefit after checking the installed Django, DRF, middleware and driver
support (in Django 5.2, transactional work must remain synchronous).
Choose features such as `GeneratedField` and `db_default` for a requirement, rather
than because they are newer.

## Migrations

Generate schema migrations and review the operations, defaults, constraints, indexes
and deletion behavior. Preserve migrations already applied or shared with others;
add a new migration for corrections. Local unshared migrations can be revised while
developing a change. Check for uncommitted model changes before declaring completion.

Use historical models in data migrations and the schema editor's database alias.
Consider existing rows, migration ordering, locking and deployment compatibility.
Make irreversible data operations explicit and test migrations with meaningful data
when the transformation warrants it. Use PostgreSQL for database verification.

## Background jobs and integrations

Follow [backend ticket 05](../../.plan/maps/backend-architecture/tickets/05-worker-and-scheduler.md)
for queue configuration and the applicable parity tickets for current behavior. Its
older sweep/sync examples do not override the product baseline.

- Route dispatch through the shared `enqueue()` helper to the `default` (`worker`) or
  `ai` (`worker-ai`) cluster; keep task wrappers thin and pass stable identifiers rather
  than requests or serialized model instances. Keep `retry > timeout` on every cluster.
- Define periodic schedules in code (`ensure_schedules()`) rather than relying on Admin
  edits, and derive recoverable work from PostgreSQL state. Record human-facing run
  history in `JobRun` rather than Django-Q2 result tables.
- Make repeated delivery safe. Persist progress and recoverable intent in PostgreSQL
  where work must survive worker crashes or dispatch failures.
- When rate-limited, checkpoint the cursor, advance `next_attempt_at` and exit to free
  the worker slot—never sleep inside a throttled job. Keep timeout, retry and rate-limit
  behavior explicit, and reconcile or use provider idempotency before retrying timed-out
  external writes. Avoid generic retries for every exception.
- Use explicit HTTP timeouts and classify provider failures. Keep credentials and raw
  sensitive payloads out of job arguments, exception messages and logs.

## Verification and delivery

Discover executable commands from backend configuration, scripts and CI. Until the
Django foundation exists, proposed commands are setup work rather than working tooling.
Use the configured test runner, formatter and linter; add type hints to service,
selector and utility interfaces without introducing a new toolchain incidentally.

Test observable behavior at the relevant boundary:

- Domain operations: invariants, state transitions and failure/rollback behavior.
- APIs: serializer validation, status/output contracts, unauthenticated access and
  cross-user access, including submitted related IDs and list visibility.
- Jobs/integrations: duplicate delivery, relevant partial failures and retry behavior;
  mock external HTTP/LLM boundaries while exercising the real ORM.
- Database-sensitive behavior: PostgreSQL constraints and, where relevant, real
  transaction/locking behavior. Use transaction-capable tests for concurrency and
  capture/execute commit callbacks deliberately when testing dispatch.

Use factories or small explicit builders when they clarify setup. Add tests proportional
to behavior and risk; avoid tests that only mirror implementation or trivial delegation.
Run focused tests, Django system checks, migration drift checks (`makemigrations --check --dry-run`)
and OpenAPI schema validation (`spectacular --validate --fail-on-warn`, or the repo's
configured equivalents) before finishing. Report commands run and any checks that remain
unavailable.

## References

Consult official documentation for the installed versions when behavior is uncertain.
These references inform this guide; their optional architecture choices do not override
the conventions above.

- [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide): services,
  selectors and API organization, selectively adapted here.
- [Django database optimization](https://docs.djangoproject.com/en/5.2/topics/db/optimization/),
  [transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/),
  [model validation](https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects)
  and [async support](https://docs.djangoproject.com/en/5.2/topics/async/).
- [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/): visibility,
  object permission checks and their list/create limitations.
- [Cookiecutter Django](https://github.com/cookiecutter/cookiecutter-django): configuration
  examples to evaluate during scaffolding, rather than a second prescribed stack.
