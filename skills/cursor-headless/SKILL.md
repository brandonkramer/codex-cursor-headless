---
name: cursor-headless
description: >-
  Delegate to Cursor Agent from Codex via thin MCP tools (cursor_ask/plan/implement)
  or `cursor-agent --print` headless mode. Ask/plan default to Grok 4.5 High (Codex
  picks low|medium|high and Fast); implement defaults to Composer 2.5 (opt into Fast)
  and escalates to Grok 4.5 by complexity. Covers ask/plan/write modes, worktrees,
  cached preflight, and controlled write-capable runs. Use when the user asks for
  Cursor CLI, Cursor Agent, Cursor headless, Composer 2.5, Grok 4.5 via Cursor, or
  Cursor as a secondary agent.
---

# Cursor Headless

Codex orchestrates; Cursor Agent executes bounded headless work via
`cursor-agent --print`.

**Prefer MCP tools** (thin facade, same speed as the CLI wrapper):

| Tool | Use | Default model |
|------|-----|----------------|
| `cursor_ask` | Read-only Q&A (`--mode ask`) | `cursor-grok-4.5-high` — **you pick tier + Fast** |
| `cursor_plan` | Read-only explore/plan (`--mode plan`) | `cursor-grok-4.5-high` — **you pick tier + Fast** |
| `cursor_implement` | Writes (`--mode default`, `--force`) | `composer-2.5` — **you pick by complexity / when to use Fast** |

Fallback CLI wrapper: `scripts/cursor_headless.py` (also what the MCP server calls).

Never pass a Fable model to Cursor (`claude-fable-5-*`). Final high-taste review
can stay on Codex (`gpt-5.6-sol`); use Cursor models below for delegated work.

## Model routing (Composer vs Grok)

You choose the model — there is no `auto` heuristic.
**Defaults are non-Fast:** ask/plan → `cursor-grok-4.5-high`; implement → `composer-2.5`.
Opt into Fast with `fast=true` or a `*-fast` model id when latency matters.
Pick Grok tier (`low` / `medium` / `high`) by task complexity. Non-fast ids upgrade
when `fast` is true.

| Model id | When to use |
|----------|-------------|
| **`cursor-grok-4.5-high`** | **Default for `cursor_ask` / `cursor_plan`.** Also implement when work is hard/ambiguous/cross-cutting. |
| **`composer-2.5`** | Simple/mechanical implement (tool default). Override ask/plan when you want cheaper. |
| **`composer-2.5-fast`** / Grok `*-fast` | Same tier when speed matters — pass `fast=true` or the `*-fast` id. |
| `cursor-grok-4.5-low` | Light ask/plan/implement — small, mostly clear. |
| `cursor-grok-4.5-medium` | Medium ask/plan/implement — multi-file reasoning, normal designs. |

### Pick Grok tier (+ Fast) by complexity

| Complexity | Model | Examples |
|------------|-------|----------|
| Simple / mechanical | `composer-2.5` (ask/plan override or implement default; `*-fast` if latency-critical) | rename, typo, lint, one-file nit, copy tweak |
| Low | `cursor-grok-4.5-low` (+ Fast optional) | short clear Q&A/plan/change, light multi-step |
| Medium | `cursor-grok-4.5-medium` (+ Fast optional) | feature slice, multi-file refactor, wire an endpoint |
| High | `cursor-grok-4.5-high` (+ Fast optional) | architecture, migration, security, ambiguous root-cause |

MCP (preferred):

```text
cursor_ask(prompt="…", cwd="$PWD")  # grok 4.5 high (default)
cursor_ask(prompt="…", cwd="$PWD", model="cursor-grok-4.5-medium", fast=true)
cursor_plan(prompt="…", cwd="$PWD", model="cursor-grok-4.5-low")  # light plan
cursor_implement(prompt="…", cwd="$PWD", worktree="cursor-task")  # composer-2.5 (simple)
cursor_implement(prompt="…", cwd="$PWD", fast=true)  # composer-2.5-fast when speed matters
cursor_implement(prompt="…", cwd="$PWD", model="cursor-grok-4.5-medium-fast")  # medium work
```

CLI fallback (same wrapper the MCP uses):

```bash
PLUGIN_ROOT=/path/to/cursor-headless   # cloned plugin root
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" --cwd "$PWD" "…"
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" --cwd "$PWD" --model cursor-grok-4.5-medium --mode plan "…"
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" --cwd "$PWD" --model cursor-grok-4.5-high --fast "…"  # → high-fast
```

## Decision Path

1. Ask/plan → pick Grok low|medium|high (default high); opt into Fast when latency matters. Implement → `composer-2.5` by default; opt into Fast or escalate to Grok by complexity.
2. `--mode ask` — one-shot advisory, no edits.
3. `--mode plan` — read-only exploration / planning.
4. `--mode default` — write-capable implementation only.
5. Prefer `--worktree` for writes unless the user wants the current tree edited.
6. Multi-step on the same task → `--continue-session` / `--resume` (faster than new sessions).
7. Skip repeated preflight after the first success (wrapper caches ~1h).

## Performance defaults (keep it fast)

| Lever | Default | Why |
|-------|---------|-----|
| Model | `composer-2.5` | Full Composer tier; opt into Fast when latency matters |
| Output | `text` | Avoid JSON parse/pretty cost |
| Stdin | closed (`DEVNULL`) | Prevents stdin-wait hangs |
| Preflight | cached 1h | Avoid N× `cursor-agent` cold starts |
| Pretty JSON | off | Use `--pretty-json` only for debug |
| Worktree | opt-in via flag | Creating worktrees costs time |

Preflight runs automatically on cache miss (version + status + models, ~1h TTL).
Force refresh with `--preflight`. For maximum speed on a known-good machine:
`--skip-preflight`.

Do not print API keys. Prefer login state; if needed, `CURSOR_API_KEY` in the
environment (not `--api-key` on the command line).

## Safe Headless Defaults

```bash
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" \
  --cwd "$PWD" \
  --mode ask \
  "Return exactly: CURSOR_HEADLESS_OK"
```

Equivalent raw CLI:

```bash
cursor-agent --print \
  --mode ask \
  --model composer-2.5 \
  --output-format text \
  --sandbox enabled \
  --trust \
  --workspace "$PWD" \
  "Return exactly: CURSOR_HEADLESS_OK" </dev/null
```

Defaults unless the task needs more:

- `--model composer-2.5`
- `--mode ask` or `plan` for read-only; `default` + `--force` only for approved writes
- `--output-format text` (use `json` / `stream-json` when parsing)
- `--sandbox enabled --trust --workspace "$PWD"`
- Wrapper `--timeout 600`

Do **not** use `--force` / `--yolo` unless the user approved writes or the run is
in a disposable worktree.

## Write-Capable Delegation

Prefer an isolated worktree (git repo required):

```bash
git rev-parse --is-inside-work-tree
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" \
  --cwd "$PWD" \
  --mode default \
  --model composer-2.5 \
  --worktree cursor-task-name \
  --auto-review \
  --force \
  --output-format stream-json \
  "Implement the requested change. Do not revert unrelated changes. Return changed files and verification commands."
```

Smarter implementation when Composer is likely to struggle:

```bash
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" \
  --cwd "$PWD" \
  --mode default \
  --model cursor-grok-4.5-high \
  --worktree cursor-task-name \
  --auto-review \
  --force \
  --output-format stream-json \
  "Implement the requested change…"
```

Fast path in the **current** worktree (only if user approved and tree is OK):

```bash
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" \
  --cwd "$PWD" --mode default --force --skip-preflight \
  "…"
```

## Delegation Prompt Shape

```text
You are a delegated reviewer. Do not edit files. Use read-only inspection only.
Return:
1. Findings with file/line evidence
2. Commands you would run if given more tool access
3. Confidence and unresolved questions
```

```text
You are a delegated implementation agent. Keep changes scoped to the request.
Do not revert unrelated user changes. Prefer simple code that matches local patterns.
Return changed files, verification commands, failures, and remaining risks.
```

## MCP tools + CLI wrapper

Prefer plugin MCP tools `cursor_ask` / `cursor_plan` / `cursor_implement` (thin
facade over the script below; `--skip-preflight` by default).

CLI fallback:

```bash
python3 "$PLUGIN_ROOT/skills/cursor-headless/scripts/cursor_headless.py" \
  --cwd "$PWD" \
  --mode plan \
  "Review this change read-only and return file/line findings."
```

Useful wrapper flags:

| Flag | Purpose |
|------|---------|
| `--model` | Default `composer-2.5`; pass `--fast` or grok low|medium|high **`-fast`** when needed |
| `--fast` | Map model → `*-fast` variant when applicable |
| `--skip-preflight` / `--preflight` | Skip or force auth/model checks |
| `--prompt-file` | Long prompts out of argv/history |
| `--timeout` | Default 600s |
| `--raw` / `--pretty-json` | Output control |
| `--continue-session` / `--resume` | Faster multi-step |
| `--approve-mcps` | Headless MCP approval |
| `--force` | Only with `--mode default` after write approval |

## Stream Parsing

For `stream-json`, treat the final line with `type == "result"` as authoritative.
The wrapper streams lines to stdout and does not summarize them.

For `json`, default is compact (not pretty). Use `--pretty-json` only when debugging.

## Reporting

When returning Cursor results to the user, include:

- Invocation path (ask / plan / write, worktree, resume/continue)
- Model used (`composer-2.5` / `composer-2.5-fast` vs `cursor-grok-4.5-{low,medium,high}`[+`-fast`])
- Cursor Agent version (from cache or `--preflight`)
- Read-only vs auto-review vs force
- Workspace / worktree boundary
- Result, denials, failures, incomplete output
