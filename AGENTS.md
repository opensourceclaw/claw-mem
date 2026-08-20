# AGENTS.md — ClawMem

## Project

intelligent memory for OpenClaw — three-tier storage, retrieval, gating, decay, graph

## Commands

- `npm run build` — TypeScript compile
- `npm test` — vitest

## Conventions

- TypeScript, English-only code, comments sparse
- Plugin manifest: `openclaw.plugin.json`
- Plugin source: `openclaw_plugin/index.ts`
- Do not bypass tests to land changes

## Red Lines

- Don't exfiltrate private data
- Don't run destructive commands without asking
- When in doubt, ask
