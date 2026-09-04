# OAuth credentials are encrypted at rest; content is not

Integration credentials are the one category of data in this database worth stealing on
its own: a refresh token is durable, silent, and grants access to a calendar or a
workspace from anywhere. They are stored in PostgreSQL alongside everything else.

**We decided to encrypt credentials with a small field type of our own over
`cryptography`'s `MultiFernet`, keyed from outside the database, and to encrypt nothing
else at the field level.**

## Considered Options

**A third-party encrypted-field library.** `django-fernet-fields` and its fork
`djfernet` are the obvious candidates and both are effectively unmaintained — djfernet's
last release was February 2022. The library is a `get_prep_value`/`from_db_value` pair
over `MultiFernet`, some forty lines; taking a stale dependency for that is the worst
trade available, because an encryption dependency going quiet is precisely the kind that
must not.

**PostgreSQL `pgcrypto`.** Encrypting in SQL means the key travels inside the statement,
which puts it in `pg_stat_activity` and in any query log — it moves the secret to more
places than it protects it from.

**An external secret manager (Vault, KMS) holding the tokens themselves.** Correct at a
scale this is not, and reachable later without touching the field: only the source of
the key material changes.

**Encrypting user content too** — a Task's or a Calendar event's `notes`, and uploaded
attachments. Rejected as the wrong mechanism rather than as too much work. Field-level
encryption suits values fetched only by primary key and never searched; a token
qualifies, `notes` does not. Encrypting it forfeits `icontains` and full-text search
permanently, which both the AI briefing and the dashboard will want. It would also be
theatre: `TaskSource.raw` deliberately retains the untouched upstream payload for
replayability, so the sensitive content is mostly there — as queryable JSONB that no
field-level scheme can cover. The threat that actually motivates the request (a leaked
dump, a stolen disk, an off-box backup) is covered completely and without query cost by
encryption underneath the database: ZFS native encryption on the dataset, or LUKS. That
belongs to the deployment decision, not to the ORM.

## Consequences

- Credentials are stored as a **single opaque encrypted JSON blob**, not as
  `access_token` / `refresh_token` columns. Providers disagree about shape — Notion
  returns `bot_id`, `workspace_id` and `owner` that its documentation warns are hard or
  impossible to retrieve again, Obsidian has a filesystem path and no OAuth at all — and
  a blob absorbs that without a migration per provider.
- Keys live in `settings.FERNET_KEYS`, read from a root-owned file or a systemd
  `LoadCredential`, never in the repository and never in the database. `MultiFernet`
  encrypts with the first and decrypts with any, so rotation is prepend-and-re-save.
- The protection is real but bounded, and stating the bound is part of the decision:
  **this defends database dumps, backups, and replicas — not a compromised host**, since
  the process that reads the database can also read the key. Anyone extending this should
  not mistake it for more.
- Encrypted columns cannot be indexed, compared, or filtered. Nothing queries a
  credential, so the cost is zero here and would not be elsewhere — which is the same
  reason content stays in plaintext.
