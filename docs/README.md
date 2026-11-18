# Docs

| Path | What it is |
|---|---|
| [`adr/`](./adr/) | Architecture decision records. Authoritative on the decisions they record |
| [`glossary/`](./glossary/) | Quick-lookup index of settled terms, models, and infrastructure names. Not authoritative |
| [`research/`](./research/) | Cited findings from primary sources, written for planning tickets of type research |
| [`agents/`](./agents/) | Agent conventions for development, issue tracking and domain docs |

Product reference: [Sunsama audit](./research/sunsama/README.md),
[feature inventory](./research/sunsama/feature-inventory.md),
[integration semantics](./research/sunsama/integration-semantics.md), and
[source manifest](./research/sunsama/sources.md). These distinguish documented reference
behavior from current decisions and recommendations; they do not replace `CONTEXT.md`.

Backend development: [Django API conventions](./agents/django.md) defines the DRF
workflow and backend boundary with the SvelteKit client.

Frontend development: [SvelteKit client conventions](./agents/svelte.md) routes planner,
source, calendar and kiosk work to its owning contracts and defines client state,
API interaction, accessibility and verification conventions.

Related, outside `docs/`:

- [`CONTEXT.md`](../CONTEXT.md) is the authority on domain vocabulary.
- [`CLAUDE.md`](../CLAUDE.md) holds shared agent instructions and current project direction.
- [`COMMITS.md`](../COMMITS.md) defines the required commit message format.
- `.plan/maps/` holds planning decisions (chartr maps and tickets). Buildable work lives
  in GitHub Issues.

**Maintenance:** when a plan, ADR or `CONTEXT.md` changes, check [`glossary/`](./glossary/)
in the same commit for terms to add or amend.
