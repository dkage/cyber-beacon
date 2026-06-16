# Contributing

## Commit Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to automate versioning and changelog generation via semantic-release.

### Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type       | Description                                     | Release                 |
|------------|-------------------------------------------------|-------------------------|
| `feat`     | A new feature                                   | Minor (`1.0.0 → 1.1.0`) |
| `fix`      | A bug fix                                       | Patch (`1.0.0 → 1.0.1`) |
| `perf`     | A performance improvement                       | Patch                   |
| `docs`     | Documentation changes only                      | —                       |
| `style`    | Formatting, missing semicolons, etc.            | —                       |
| `refactor` | Code change that is neither a fix nor a feature | —                       |
| `test`     | Adding or updating tests                        | —                       |
| `chore`    | Build process, dependency updates, tooling      | —                       |
| `ci`       | CI/CD configuration changes                     | —                       |
| `revert`   | Reverts a previous commit                       | —                       |

### Breaking Changes

Append `!` after the type, or add `BREAKING CHANGE:` in the footer. This triggers a major version bump (`1.0.0 → 2.0.0`).

```
feat!: redesign authentication API
```

```
feat: new auth flow

BREAKING CHANGE: the /login endpoint now requires an email field instead of username
```

### Scope (optional)

Use scope to indicate which part of the project the commit affects:

```
feat(frontend): add dark mode toggle
fix(backend): correct token expiration logic
chore(ci): update GitHub Actions workflow
```

### Examples

```
feat: add user profile page
fix: resolve incorrect date formatting on dashboard
perf: lazy load route components
docs: update getting started guide
chore: upgrade drizzle to v0.46
feat(auth)!: replace session tokens with JWT
```