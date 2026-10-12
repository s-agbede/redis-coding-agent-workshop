"""Terminal display and command approval, called explicitly by the agent."""

import json
import os
from typing import Any

from rich.console import Console, Group
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

console = Console()


def banner(model: str) -> None:
    console.print(f"[bold cyan]coding-agent[/] · [dim]{model}[/] · type a task, or 'exit'")
    console.print("[dim]Shell commands ask for approval before they run.[/]")


def info(message: str) -> None:
    console.print(f"[dim]{message}[/]")


def prompt_user() -> str:
    return console.input("[bold green]you ›[/] ")


def show_answer(text: str) -> None:
    if text:
        markdown = Markdown(text)
        # Without an explicit code block, Markdown can flatten Python lines and
        # interpret comments as headings. Preserve the response literally then.
        has_code_block = any(token.type in {"fence", "code_block"} for token in markdown.parsed)
        body = markdown if has_code_block else Text(text)
        console.print(Panel(body, title="Answer", border_style="green", padding=(1, 2)))


def show_turn(number: int) -> None:
    console.print()
    console.rule(f"Model turn {number}", style="cyan", align="left")


def show_tool_request(call_id: str, name: str, arguments: str) -> None:
    try:
        formatted = json.dumps(json.loads(arguments), indent=2, ensure_ascii=False)
        body = Syntax(formatted, "json", word_wrap=True, background_color="default")
    except (ValueError, TypeError):
        body = Text(arguments)
    console.print(Panel(Group(Text(name, style="bold"), body),
                        title=Text(f"REQUEST {call_id}"), border_style="blue"))


def show_tool_result(call_id: str, result: str) -> None:
    failed = result.startswith("Error:")
    if result.startswith("exit "):
        failed = result.splitlines()[0] != "exit 0"
    console.print(Panel(
        Text(result), title=Text(f"RESULT {call_id}"),
        subtitle=f"{len(result)} characters, not tokens",
        border_style="red" if failed else "cyan",
    ))


def show_request(messages: list[Any]) -> None:
    """Show the outgoing history without modifying it or wrapping the SDK."""
    previews = [
        (message.get("role", ""), message.get("content") or "")
        if isinstance(message, dict) else (message.role, message.content or "")
        for message in messages
    ]
    show_turn(1 + sum(role == "assistant" for role, _ in previews))
    count = len(previews)
    console.print(f"REQUEST PREVIEW: {count} {'message' if count == 1 else 'messages'}", markup=False)
    console.print("Roles: " + " -> ".join(role for role, _ in previews), markup=False)
    if os.environ.get("AGENT_TRACE_MESSAGES") == "1":
        for index, (role, content) in enumerate(previews, start=1):
            console.print(f"[{index}] {role}: {content[:600]}", markup=False, highlight=False)
            if len(content) > 600:
                console.print("[preview shortened; full content sent]", markup=False)


def approve_command(command: str) -> bool:
    """Require consent before the loop executes a shell command."""
    if os.environ.get("AGENT_AUTO_APPROVE") == "1":
        return True
    console.print(Text(command))
    return Prompt.ask("Run this command?", choices=["y", "n"], default="y") == "y"
