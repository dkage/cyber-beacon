# Commit messages

All commits in this repository use Conventional Commits with a succinct title and a
required body. When the change tackles a GitHub issue, reference it in the footer.
These rules also apply to squash commit messages and commits created by automation.

## Format

```text
<type>[(scope)][!]: <succinct description>

<One to three brief paragraphs explaining what changed and why.>

<Issue references and other footers, when applicable>
```

### Title

- Use a lowercase type from the table below. Scope is optional; choose a meaningful
  area such as `backend`, `frontend`, `auth`, `integrations` or `planning`.
- Write an imperative description: `add`, `fix`, `remove`, `document`.
- Aim for 50 characters; keep the complete title within 72 characters.
- Omit the trailing period. Put issue references in the footer, not the title.

| Type | Use |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `perf` | Performance improvement |
| `refactor` | Code restructuring without a feature or bug fix |
| `docs` | Documentation changes |
| `style` | Formatting without a behavior change |
| `test` | Test changes |
| `build` | Build system or dependency changes |
| `ci` | CI/CD configuration |
| `chore` | Maintenance outside the categories above |
| `revert` | Reverting an earlier commit |

### Body

Write one to three brief paragraphs describing the actual change and its purpose.
Include relevant behavior, decisions or tradeoffs so a reader can understand the commit
without the original conversation. A small change can use one short paragraph.

Describe the committed diff, not an intended future implementation. Mention validation
when it helps assess the change, and only claim checks actually performed. Separate
the title, body and footers with blank lines; wrap prose at roughly 72 characters.

### Footers

- Use `Refs: #123` when the commit contributes to or relates to an issue without
  completing it.
- Use `Closes: #123` only when the change satisfies the issue's acceptance criteria and
  should close it when merged. For several issues, use one footer line per issue.
- Use `owner/repository#123` for an issue in another repository.
- Omit the issue footer when no issue applies; never invent an issue reference.
- For breaking changes, append `!` before the title's colon and add a
  `BREAKING CHANGE:` footer explaining the incompatibility and required migration.

## Examples

Partial issue work:

```text
feat(backend): scaffold the Django API

Replace the abandoned Go scaffold with Django, DRF and an OpenAPI
endpoint. Configure PostgreSQL as the application's database so the
domain models can be added against the intended production stack.

Worker services and the remaining container acceptance criteria are
left for the next change.

Refs: #8
```

Completed issue work:

```text
feat(frontend): make the app a static API client

Remove the generated Better Auth, Drizzle and SQLite server stack.
Configure the static adapter and SPA fallback so Django can own
identity and persistence while the browser handles navigation.

Verify the static build and a direct refresh on a nested route.

Closes: #9
```

Documentation without an issue:

```text
docs: align agent guidance with the current roadmap

Document the approved worksheet and carry-forward baseline, distinguish
the planned stack from the existing scaffolds, and link both active
planning maps. Explain the first usable day and calendar planning
release boundaries so agents can find the relevant design gates.
```
