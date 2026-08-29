# Cyber Beacon — Project Context

## What This Is

A productivity scheduling dashboard — think Sunsama but self-hosted. The core loop:
1. User pulls tasks from integrations into a daily view
2. Drags tasks into time slots on a day timeline (syncs to Google Calendar)
3. AI generates a daily briefing based on the finalized schedule

The secondary surface is a **kiosk dashboard** — an always-on display for an office TV/monitor with glanceable widgets (schedule, meetings, AI briefing, weather, time/date, Obsidian note count, priorities, calendar views, carousels, etc.).

## Stack

### Backend (`/backend`)
- **Language**: Go
- **Database**: SQLite
- **Module**: `schedule-dashboard`
- Status: scaffolded, no real code yet

### Frontend (`/frontend`)
- **Framework**: SvelteKit + TypeScript
- **Package manager**: Bun
- **Auth**: Better Auth
- **ORM**: Drizzle (SQLite)
- **UI**: TailwindCSS
- **Testing**: Playwright (e2e), Vitest (unit)
- **Other**: Storybook, Prettier, ESLint

## Planned Integrations
- Google Calendar (bidirectional sync — task scheduling writes back to GCal)
- Gmail
- Notion
- Obsidian (read fleeting notes count, surface notes)
- Jira

## AI Features
- Task priority analysis
- Daily briefing generation (after user finalizes the day's schedule)

## Developer Context

The developer is a senior PHP/Laravel engineer (10y PHP, 7y Laravel) learning Go through this project. Claude acts as a **pair programming guide**, not a code generator:
- Do NOT write code unprompted — guide, explain Go-specific concepts and idioms, point out gotchas
- DO provide ready snippets if explicitly asked or if there's a bug in existing code
- No need to explain general programming concepts — focus on Go-specific behavior, the stdlib, tooling, and ecosystem differences from PHP/Laravel
- When it makes sense to do so, make comparison to Laravel features and PHP 8 features, with the Go implementations and quirks

### Frontend experience
- Primarily a backend developer — frontend was mainly Blade templates + jQuery + TailwindCSS + plain HTML/JS
- Some basic exposure to React and AngularJS, but not deeply experienced in either
- No prior TypeScript experience
- No prior Svelte experience
- Frontend guidance should bridge from "jQuery/plain JS" mental models to modern reactive/component patterns when explaining SvelteKit concepts

## Key Go Concepts to Introduce Progressively
- Error handling as values (no exceptions)
- Interfaces and implicit satisfaction
- Goroutines and channels for concurrency
- Go modules and workspace layout
- Stdlib-first philosophy (net/http, database/sql, encoding/json)

## Agent skills

### Issue tracker

GitHub Issues on `dkage/cyber-beacon`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles, using the default label strings. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
