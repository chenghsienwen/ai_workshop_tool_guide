# Plan: Add macOS Tool Guide (Implemented 2026-07-14)

**Status: implemented as described below.** Open questions were resolved as: (1) OS-picker landing page — done; (2) full content pass now, written for total beginners — done; (3) no screenshots yet, placeholders left in place — done; (4) README updated with both links — done.

## Current state

- `ai_workshop_guide_windows.html` — single self-contained HTML file, Traditional Chinese, Windows 11 install guide (Node.js, VS Code, Python, PowerShell commands, Git for Windows, Claude Code, Codex CLI, Antigravity CLI, corporate network restriction notes, etc.)
- `index.html` — mirror of the Windows guide, synced by CI on every push (`cp ai_workshop_guide_windows.html index.html`). This is what GitHub Pages serves at the site root.
- `.github/workflows/deploy.yml` — one workflow: build job copies the source file to `index.html`, uploads the whole repo as a Pages artifact, deploy job publishes it. Triggers on every push to `main`.
- One live site: `https://chenghsienwen.github.io/ai_workshop_tool_guide/`
- `assets/` holds screenshots referenced by relative path.

## Goal

Publish a second guide for macOS users, alongside the existing Windows one, with **two separate GitHub workflows** as requested — one per OS guide — instead of the current single combined workflow.

## Proposed file layout

| File | Purpose |
|---|---|
| `ai_workshop_guide_windows.html` | Existing Windows source (unchanged, stays source of truth for Windows) |
| `ai_workshop_guide_macos.html` | **New** macOS source (new file, adapted content — see below) |
| `index.html` | **New**: static OS-picker landing page, committed directly (not CI-generated), linking to `windows.html` and `macos.html` |
| `windows.html` | **New**: served copy of the Windows guide, synced from `ai_workshop_guide_windows.html` |
| `macos.html` | **New**: served copy of the macOS guide, synced from `ai_workshop_guide_macos.html` |

Result: three pages under one Pages site —
- `https://chenghsienwen.github.io/ai_workshop_tool_guide/` (OS picker, new root)
- `https://chenghsienwen.github.io/ai_workshop_tool_guide/windows.html` (Windows — URL changed from the old root, old bookmarks to `/` now land on the picker instead of the guide directly)
- `https://chenghsienwen.github.io/ai_workshop_tool_guide/macos.html` (macOS, new)

## Workflow split (2 workflows)

Split `deploy.yml` into two workflow files, each scoped to its own source file via `paths:` filter (so an edit to one guide's source is what triggers a rebuild):

**`.github/workflows/deploy-windows.yml`** — triggers on `ai_workshop_guide_windows.html`, `index.html`, `assets/**`, or itself
**`.github/workflows/deploy-macos.yml`** — triggers on `ai_workshop_guide_macos.html`, `assets/**`, or itself

Both run the **same** build step regardless of which one fires:
```
cp ai_workshop_guide_windows.html windows.html
cp ai_workshop_guide_macos.html macos.html
```
This is required, not just belt-and-suspenders: the Pages artifact is the entire checked-out repo, and `windows.html`/`macos.html` are never committed — only generated at build time. If each workflow only synced its "own" file, whichever workflow fires would upload an artifact missing the *other* guide's served page. Both share `concurrency: group: pages` to serialize, since they publish to the same Pages deployment.

## Content plan for the macOS guide

Clone `ai_workshop_guide_windows.html` → `ai_workshop_guide_macos.html` as a starting point, then adapt OS-specific parts:

- PowerShell (admin) → Terminal / zsh
- Node.js Windows installer → Node.js macOS `.pkg` or Homebrew (`brew install node`)
- Python Windows installer + "Add to PATH" checkbox → macOS installer or `brew install python`, PATH via shell profile
- "Git for Windows" install step → Xcode Command Line Tools (`xcode-select --install`) or `brew install git`
- VS Code install/extensions steps → same tool, macOS download/drag-to-Applications flow
- Claude Code / Codex CLI / Antigravity CLI install + login steps → same CLIs, macOS terminal commands
- Corporate network restriction screenshots/IT ticket notes → check if these are Windows-specific (proxy/firewall config) or apply to macOS too
- Screenshots in `assets/` → new macOS-specific screenshots needed for anything showing OS chrome (installer dialogs, terminal, etc.); reuse where the tool's UI is identical (e.g. web pages)

## Open questions

1. **Root page behavior**: keep `index.html` = Windows guide (current default, zero broken links), or replace root with a small OS-picker landing page and move Windows to e.g. `windows.html`? (This plan assumes the former — no breaking change.)
2. **Content source for macOS guide**: should I do a full pass adapting every Windows-specific step now, or scaffold the structure/headings first and fill in content section by section for your review?
3. **Screenshots**: do you have macOS screenshots ready to drop into `assets/`, or should placeholders/TODO markers be left where new screenshots are needed?
4. **README**: update to list both guide links?

## Not doing (unless you want it)

- No shared "OS switcher" nav link injected into both HTML files — can add later once both pages exist, if wanted.
- No build tooling / templating to de-duplicate shared content between the two HTML files — both stay fully self-contained per current repo convention.
