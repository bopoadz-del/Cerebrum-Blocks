# Modular Agent Pack — Audit

## Source material (from `C:\Users\shimm\The_Fork`)

The hat designs were extracted from the runtime agent configs at:

- `app/agents/configs/project-assistant.md`
- `app/agents/configs/construction-pm.md`
- `app/agents/configs/contracts-manager.md`
- `app/agents/configs/quantity-surveyor.md`
- `app/agents/configs/bim-analyst.md`
- `app/agents/configs/document-analyst.md`
- `app/agents/configs/document-ingestion.md`
- `app/agents/configs/safety-officer.md`
- `app/agents/configs/heavy-reasoning.md`
- `app/agents/configs/learning.md`
- `app/agents/configs/validation.md`

The portable agent pattern (`.agent-core` canonical files + JSON manifests) was adapted from:

- `.agent-core/construction-expert.md`
- `.agent-core/block-architect.md`
- `.agent-core/block-implementer.md`
- `docs/agents/README.md`
- `docs/agents/construction-expert-audit.md`

## What changed

1. **Introduced `core-agent`** — a new shared kernel that did not exist as a separate file in the fork.
2. **Refactored 11 runtime personas into hats** — each now explicitly `extends: core-agent` and keeps only domain-specific rules/tools.
3. **Added JSON manifests** for every canonical agent (`core-agent` + 11 hats), capturing `description`, `examples`, activation, allowed paths, handoffs, verification, and portability notes.
4. **Removed platform-specific wrapper directories** — no `.claude/` or `.cursor/` folders; the pack is now purely platform-agnostic.
5. **Preserved useful wrapper content** — frontmatter `description` and `<example>` blocks were migrated into each JSON manifest so host stores can generate their own wrappers without losing auto-delegation signal.

## What was left out of the hats

The following fork agents were treated as shared utilities, not hats:

- `external-mcp` — single integration surface for all external APIs.
- `self-coding` — on-the-fly sandboxed Python for unsupported calculations.
- `smart-orchestrator` — free-form intent router to blocks.

These can still be referenced by hats but are not part of the 12 canonical blocks.

## Platform-specific assumptions

- Any host (Claude Code, Cursor, Kimi, etc.) can generate wrappers from `.agent-core/<id>.md` body + `.agent-core/<id>.json` metadata.
- Hidden host system prompts / private routing internals are **NOT AVAILABLE** and are not claimed.

## Verification

- 1 core agent + 11 hats = 12 canonical blocks.
- Each canonical block has `.md` + `.json`.
- Each JSON has `description` and `examples`.
- No platform-specific wrapper directories remain in the pack.
