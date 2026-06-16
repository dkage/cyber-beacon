# Cyber Beacon

## Stack

### Backend

- Golang
- Sqlite


### Frontend

Packages installed using Bun

- SvelteKit
- TailwindCSS
- Drizzle
- Better Auth
- Playwright

## Getting Started

### Frontend

```bash
cd frontend
bun run dev --open
```

Hit `Ctrl-C` to stop the dev server.

## Add-on Setup

### Playwright
- Run `npx playwright install` to download browsers
- Visit `/demo/playwright` to see the demo page
- Run `npm run test:e2e` to execute the example tests

### Drizzle
- Check `DATABASE_URL` in `.env` and adjust it to your needs
- Run `bun run db:push` to update your database schema

### Better Auth
- Run `bun run auth:schema` to generate the auth schema
- Run `bun run db:push` to update your database
- Check `ORIGIN` & `BETTER_AUTH_SECRET` in `.env` and adjust to your needs
- Visit `/demo/better-auth` to view the demo

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for commit conventions and guidelines.

Stuck? Visit https://svelte.dev/chat