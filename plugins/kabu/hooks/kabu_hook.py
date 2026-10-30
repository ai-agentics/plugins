#!/usr/bin/env python3
"""Kabu hooks for Claude Code and Copilot CLI: a push when the agent finishes a turn (stop) or needs you (input).

Off unless KABU_HOOKS=1. Never in the agent's way: it reads the event on stdin, starts `kabu send` in the background
and exits 0 at once, printing nothing, whatever happens. Usage: kabu_hook.py stop|input < event.json
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any, Dict, List, Tuple

KABU = Path(__file__).resolve().parents[1] / "bin" / "kabu"
DEFAULTS = {"stop": ("Turn finished", "Waiting for your next prompt."), "input": ("Needs your input", "The agent is waiting for you.")}
EXCERPT = 300  # characters of the agent's text that leave this machine and show on the Lock Screen


def load_kabu() -> ModuleType:
    """The bundled CLI as a module, for its project and agent detection. No bytecode is written into the plugin."""
    sys.dont_write_bytecode = True
    loader = importlib.machinery.SourceFileLoader("kabu_cli", str(KABU))
    spec = importlib.util.spec_from_loader("kabu_cli", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # Python 3.9's dataclasses look the module up while it loads
    loader.exec_module(module)
    return module


def command(event: str, payload: Dict[str, Any], cwd: Path) -> Tuple[List[str], str]:
    """The `kabu send` for one event, and the message it reads on stdin: never in argv, where ps shows it. Claude
    Code's Stop carries the last message, of which only an excerpt is sent; a Notification has its own text.

    The project and agent are resolved here, while this hook's parent is still the harness: the background send
    outlives it."""
    title, message = DEFAULTS[event]
    if event == "input":
        title = str(payload.get("title") or title).strip()[:120]
    text = str(payload.get("last_assistant_message" if event == "stop" else "message") or "").strip() or message
    if len(text) > EXCERPT:
        text = text[:EXCERPT - 1].rstrip() + "…"
    kabu = load_kabu()
    return [sys.executable, str(KABU), "send", f"--title={title}", "-", f"--project={kabu.detect_project(cwd)}",
            f"--agent={kabu.resolve_agent()}"], text


def main(argv: List[str]) -> int:
    if os.environ.get("KABU_HOOKS") != "1" or argv[1:2] not in (["stop"], ["input"]):
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        payload = payload if isinstance(payload, dict) else {}
        cwd = Path(str(payload.get("cwd") or os.getcwd()))  # a client may run hooks in the plugin's folder, not the project
        send, text = command(argv[1], payload, cwd)
        child = subprocess.Popen(send, cwd=cwd if cwd.is_dir() else None, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
        assert child.stdin is not None
        child.stdin.write(text.encode())  # a few hundred bytes: the pipe takes them without waiting for kabu
        child.stdin.close()
    except Exception:  # a hook must never fail the agent's turn
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
