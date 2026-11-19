# Cyber Beacon client

Static SvelteKit 2 + Svelte 5 client. Django owns authentication, persistence and jobs.
Setup and verification commands are maintained in the [root README](../README.md).

Read [Svelte conventions](../docs/agents/svelte.md) and
[the release contract](../docs/phase-one-contract.md) before changing planner behavior.
`src/lib/schema.d.ts` is generated from `backend/openapi.yaml`; regenerate it with
`bun run generate:api` and format it with Prettier after API changes.
