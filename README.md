# cursor-headless (Codex plugin)

Thin MCP tools over the fast `cursor_headless.py` wrapper — native Codex tools without an extra agent loop.

## Tools

| Tool | Mode | Default model |
|------|------|----------------|
| `cursor_ask` | ask (read-only) | `cursor-grok-4.5-high` (Codex picks low\|medium\|high + Fast) |
| `cursor_plan` | plan (read-only) | `cursor-grok-4.5-high` (Codex picks low\|medium\|high + Fast) |
| `cursor_implement` | default + force | `composer-2.5` (opt into Fast; escalate to Grok 4.5 low/medium/high by complexity) |

Pass `model` explicitly: simple → `composer-2.5` (or `*-fast` / `fast=true` when latency matters); light → `cursor-grok-4.5-low`; medium → `…-medium`; hard → `…-high`.

## Slash command

| Command | What it does |
|---------|----------------|
| `/cursor-implement-workflow` | Codex orchestrates; fans out parallel `cursor_ask` / `cursor_plan` / `cursor_implement` workers (default `composer-2.5` + Fast; escalate to Grok 4.5 by difficulty) |

Example: `/cursor-implement-workflow split auth refactor into explore + implement + tests`

## Layout

- `commands/cursor-implement-workflow.md` — orchestration slash command
- `skills/cursor-headless/` — routing skill + CLI wrapper
- `src/cursor_headless_mcp.py` — FastMCP facade
- `bin/cursor-headless-mcp` — `uv run --with mcp` launcher

## Install

Dedicated marketplace: `cursor-headless` (plugin root is also the marketplace root).
Requires `uv` and `cursor-agent` on PATH. MCP launches via `uv run` (Mac + Windows).

Clone or copy this repo somewhere local, then point Codex at it:

### macOS / Linux

```toml
[marketplaces.cursor-headless]
source_type = "local"
source = "$HOME/path/to/cursor-headless"

[plugins."cursor-headless@cursor-headless"]
enabled = true
```

### Windows

```toml
[marketplaces.cursor-headless]
source_type = "local"
source = '%USERPROFILE%\path\to\cursor-headless'

[plugins."cursor-headless@cursor-headless"]
enabled = true
```

Replace the `source` path with the absolute path to your clone. After editing config, restart Codex.
