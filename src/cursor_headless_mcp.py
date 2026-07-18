#!/usr/bin/env python3
"""Thin MCP facade over cursor_headless.py — native tools, same fast path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = PLUGIN_ROOT / "skills" / "cursor-headless" / "scripts" / "cursor_headless.py"

mcp = FastMCP("cursor-headless")


def _run_wrapper(
    *,
    prompt: str,
    cwd: str,
    mode: str,
    model: str,
    prefer_fast: bool,
    force: bool,
    worktree: str | None,
    skip_preflight: bool,
    output_format: str,
    continue_session: bool,
    timeout: float,
) -> str:
    if not WRAPPER.is_file():
        return f"error: wrapper missing at {WRAPPER}"

    cmd = [
        sys.executable,
        str(WRAPPER),
        "--cwd",
        cwd,
        "--mode",
        mode,
        "--model",
        model,
        "--output-format",
        output_format,
        "--timeout",
        str(timeout),
    ]
    if prefer_fast:
        cmd.append("--fast")
    if force:
        cmd.append("--force")
    if skip_preflight:
        cmd.append("--skip-preflight")
    if continue_session:
        cmd.append("--continue-session")
    if worktree is not None:
        cmd.append("--worktree")
        if worktree:
            cmd.append(worktree)

    cmd.append(prompt)

    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout + 30,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        return f"error: timed out after {timeout:g}s\n{out}".strip()

    parts = []
    if proc.stdout:
        parts.append(proc.stdout.rstrip())
    if proc.stderr:
        parts.append(f"[stderr]\n{proc.stderr.rstrip()}")
    if proc.returncode != 0:
        parts.append(f"[exit {proc.returncode}]")
    return "\n".join(parts) if parts else f"[exit {proc.returncode}] (empty output)"


@mcp.tool()
def cursor_ask(
    prompt: str,
    cwd: str = ".",
    model: str = "cursor-grok-4.5-high",
    fast: bool = False,
    skip_preflight: bool = True,
    continue_session: bool = False,
    timeout: float = 600,
) -> str:
    """Read-only Cursor ask (--mode ask).

    Default model cursor-grok-4.5-high; caller picks low|medium|high and whether to use Fast
    (fast=true or *-fast id). Pass composer-2.5 for cheaper mechanical Q&A.
    """
    return _run_wrapper(
        prompt=prompt,
        cwd=cwd,
        mode="ask",
        model=model,
        prefer_fast=fast,
        force=False,
        worktree=None,
        skip_preflight=skip_preflight,
        output_format="text",
        continue_session=continue_session,
        timeout=timeout,
    )


@mcp.tool()
def cursor_plan(
    prompt: str,
    cwd: str = ".",
    model: str = "cursor-grok-4.5-high",
    fast: bool = False,
    skip_preflight: bool = True,
    continue_session: bool = False,
    timeout: float = 600,
) -> str:
    """Read-only Cursor plan/explore (--mode plan).

    Default model cursor-grok-4.5-high; caller picks low|medium|high and whether to use Fast
    (fast=true or *-fast id). Pass composer-2.5 for cheaper plans.
    """
    return _run_wrapper(
        prompt=prompt,
        cwd=cwd,
        mode="plan",
        model=model,
        prefer_fast=fast,
        force=False,
        worktree=None,
        skip_preflight=skip_preflight,
        output_format="text",
        continue_session=continue_session,
        timeout=timeout,
    )


@mcp.tool()
def cursor_implement(
    prompt: str,
    cwd: str = ".",
    model: str = "composer-2.5",
    fast: bool = False,
    worktree: str | None = None,
    force: bool = True,
    skip_preflight: bool = True,
    continue_session: bool = False,
    timeout: float = 600,
) -> str:
    """Write-capable Cursor implementation (--mode default).

    Caller picks the model by task complexity (see skill):
    - simple/mechanical → composer-2.5 (default); set fast=true or model=composer-2.5-fast when speed matters
    - light → cursor-grok-4.5-low (+ Fast optional)
    - medium → cursor-grok-4.5-medium (+ Fast optional)
    - hard/ambiguous/cross-cutting → cursor-grok-4.5-high (+ Fast optional)

    Set worktree for isolation; force defaults true. `fast` defaults false — opt in to upgrade to *-fast.
    """
    return _run_wrapper(
        prompt=prompt,
        cwd=cwd,
        mode="default",
        model=model,
        prefer_fast=fast,
        force=force,
        worktree=worktree,
        skip_preflight=skip_preflight,
        output_format="text",
        continue_session=continue_session,
        timeout=timeout,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
