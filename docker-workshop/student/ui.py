"""The pretty-REPL: a thin rich layer over the agent loop.

Deliberately linear (no full-screen TUI) so control flow stays legible and a bug
in the loop produces a clean traceback. All display and human-in-the-loop gating
live here, wrapped around the model client and the tool registry — the agent loop
itself stays pure.

By default it shows a spinner while the model is thinking and a one-line summary
per tool action. Set AGENT_VERBOSE=1 to also print raw tool arguments and results
(useful when teaching the mechanism).
"""

import os
import re

from rich.console import Console
from rich.markup import escape
from rich.prompt import Prompt

console = Console()
VERBOSE = bool(os.environ.get("AGENT_VERBOSE"))
AUTO_APPROVE = bool(os.environ.get("AGENT_AUTO_APPROVE"))


def banner(model):
    console.print(f"[bold cyan]coding-agent[/] · [dim]{model}[/] · type a task, or 'exit'")
    console.print("[dim]/auto turns automatic approval on or off · when asked: y = allow, n = refuse, a = allow all[/]")


def info(message):
    console.print(f"[dim]{message}[/]")


class Approvals:
    """Session approval state. Shared with the tool registry and toggled at
    runtime with the /auto command."""

    def __init__(self, auto=None):
        self.auto = AUTO_APPROVE if auto is None else auto

    def toggle(self):
        self.auto = not self.auto
        return self.auto


def prompt_user():
    return console.input("[bold green]you ›[/] ")


def show_answer(text):
    if text:
        console.print(f"[bold]🤖[/] {text}")


def _summarize(name, args):
    """A short, human-readable phrase for what a tool call is about to do."""
    if name == "list_files":
        return f"Listing files in {args.get('path', '.')}"
    if name == "read_file":
        return f"Reading {args.get('path', '?')}"
    if name == "write_file":
        return f"Writing {args.get('path', '?')}"
    if name == "str_replace":
        return f"Editing {args.get('path', '?')}"
    if name == "run_bash":
        cmd = str(args.get("command", "")).strip().splitlines()[0] if args.get("command") else ""
        return f"Running: {cmd[:70]}"
    if name == "web_fetch":
        return f"Fetching {args.get('url', '?')}"
    return name


# --- model "thinking" spinner, via a transparent client proxy ----------------
# run_agent calls client.chat.completions.create(...); we wrap that call so the
# wait shows a spinner, without changing the loop.

class _SpinnerCompletions:
    def __init__(self, inner):
        self._inner = inner

    def create(self, **kwargs):
        with console.status("[dim]thinking…[/]", spinner="dots"):
            return self._inner.create(**kwargs)


class _SpinnerChat:
    def __init__(self, inner):
        self.completions = _SpinnerCompletions(inner.completions)


class _SpinnerClient:
    def __init__(self, inner):
        self.chat = _SpinnerChat(inner.chat)


def with_spinner(client):
    """Wrap a model client so each request shows a 'thinking…' spinner."""
    return _SpinnerClient(client)


# --- tool display + human-in-the-loop gating ---------------------------------

def wrap_registry(registry, gated, approvals=None):
    """Return a registry whose tools show a summary + spinner and (if gated) ask
    approval — without changing the agent loop that calls them.

    Gated tools (run_bash, web_fetch) prompt [y/n/a] unless auto-approve is on,
    via the AGENT_AUTO_APPROVE env var, the /auto command, or the user answering
    'a' (approve all) once. Pass a shared Approvals instance to toggle at runtime.
    """
    approvals = approvals or Approvals()

    def wrap(name, func):
        def wrapped(**args):
            summary = _summarize(name, args)
            if VERBOSE:
                detail = ", ".join(f"{k}={v!r}" for k, v in args.items())
                console.print(f"[blue]🔧 {name}[/] › {detail}")

            if name in gated and not approvals.auto:
                console.print(f"[blue]• {summary}[/]")
                choice = Prompt.ask("   approve?", choices=["y", "n", "a"], default="y")
                if choice == "n":
                    console.print("   [yellow]↳ declined[/]")
                    return "User declined to run this tool."
                if choice == "a":
                    approvals.auto = True
                    console.print("   [dim]↳ auto-approving tools for the rest of this session[/]")

            try:
                with console.status(f"[dim]{escape(summary)}…[/]", spinner="dots"):
                    result = func(**args)
            except Exception as error:
                console.print(f"[red]✗[/] {escape(summary)} — failed: {escape(str(error))}")
                raise  # The loop converts this into feedback for the next model turn.

            if name == "run_bash":
                # run_bash's public string contract starts with the process exit code.
                status = re.match(r"^exit (-?\d+)(?:\n|$)", str(result))
                succeeded = status is not None and int(status[1]) == 0
                marker = "[green]✓[/]" if succeeded else "[red]✗[/]"
                console.print(f"{marker} {escape(summary)}")
                tail = str(result)[-1200:]
                if len(str(result)) > 1200:
                    tail = str(result).splitlines()[0] + "\n… [showing output tail]\n" + tail
                console.print(tail, markup=False, highlight=False)
            else:
                console.print(f"[green]✓[/] {escape(summary)}")
                if VERBOSE:
                    console.print(f"   ↳ {result}", markup=False, highlight=False)
            return result

        return wrapped

    return {name: wrap(name, func) for name, func in registry.items()}
