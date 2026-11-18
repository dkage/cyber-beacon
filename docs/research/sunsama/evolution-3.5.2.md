# Sunsama 3.5.2 desktop findings (post-audit)

The main audit (`README.md`, `feature-inventory.md`, `integration-semantics.md`,
`sources.md`) covered the **installed macOS desktop 3.4.14** and the public manual on
2026-11-16. The installed client has since moved to **3.5.2** (build `261114z7ectipv2`).
This addendum records the differences found by fresh inspection of the 3.5.2
`app.asar`, so planning documents stay accurate without re-running reverse engineering
for every epic.

**Method and evidence.** REA was attempted against the full `app.asar`
(`/Applications/Sunsama.app/Contents/Resources/app.asar`, packaged 2026-11-14). The
full-bundle analysis hit the same retained-representation budget the audit already
documents, so findings below come from reading the extracted Electron source directly
(main process and bundled agent-host binaries are plain JavaScript). They are
**static/source observations of the installed client**, not witnessed runtime captures
and not private-server behavior.

## What changed / is new in 3.5.2

### Coding-agent host (F111)
Sunsama now ships a host that runs **coding agents on the user's machine** and lets
them read and write planning data:

- Bundled ACP (Agent Client Protocol) adapters for **Claude Code, Codex, and pi**
  (`bin/agent-host/{claude-code-acp,codex-acp,pi-acp}.mjs`), plus a generic CLI/daemon
  (`cli.mjs`, `daemon.mjs`, `adapter.mjs`).
- `main/agent-host.js` pairs the machine to the workspace via a device token
  (`mintAgentDeviceToken`), independent of web sign-in, and talks to a daemon over a
  Unix socket (`~/.sunsama/agent-host.sock` / named pipe on Windows).
- Machine-scoped preferences live in `~/.sunsama/desktop.json` (`enabled`, `onQuit`:
  ask/keep/stop).
- The bound agent library embeds secret/token guards (GitHub PAT, Slack bot tokens,
  etc.); agents must never receive source tokens.

This is **distinct** from Sunny/Autoplan (Sunsama's own assistant) and from external
execution meshes. It is the "bring your own coding agent" pattern. Effective decision:
**build it (parity 10, roadmap via the native-desktop epic).**

### Native desktop shell (F112)
- Global add-task window, menu-bar/tray app with a mini focus bar, window-close hides
  to tray (does not quit).
- Custom URL scheme `sunsama://` registered by the OS app: `sunsama://action/details/<id>`,
  `sunsama://action/navigate/<path>`, `sunsama://today`.
- Auto-update flow: background download on launch + every ~10 min; a "Relaunch to update"
  toast; install on the toast or next real quit; macOS ShipIt/Squirrel guard in
  `main/bootstrap.js` + `main/shipit-gate.js` to avoid an aborted install on relaunch.

### Local-OS connector pattern (F113)
- Native **Apple Reminders** integration via a Swift bridge
  (`native/osx/reminders/reminder_manager.swift` -> `bin/reminder_manager_*`).
- Per-minute auto-import per list while the app is open/focused; destructive
  delete-on-import option (off); recurring reminder completes its occurrence instead.
- macOS-only (TCC permission prompt); not a server-owned connector.

## Relevance to the roadmap

- The **Coding-agent host** and **Native desktop** epics should cite this file (and
  `F111`–`F113`) rather than require a fresh REA pass.
- Re-running REA is only needed to verify a *newer* Sunsama behavior later, on demand
  per epic — not as a prerequisite for drafting their sub-issues.