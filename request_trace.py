"""Opt-in previews of the text messages passed to the workshop's SDK calls."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

PREVIEW_CHARACTERS = 600


@dataclass
class _PreviewCompletions:
    send: Callable[..., Any]

    def create(self, **kwargs: Any) -> Any:
        messages = kwargs["messages"]
        previews: list[tuple[str, str]] = []
        for message in messages:
            if isinstance(message, dict):
                role, content = message["role"], message.get("content")
            else:
                role, content = message.role, message.content
            previews.append((role, content or ""))

        count = len(previews)
        lines = [
            f"REQUEST PREVIEW: {count} {'message' if count == 1 else 'messages'}",
            "Roles: " + " -> ".join(role for role, _ in previews),
        ]
        for number, (role, content) in enumerate(previews, start=1):
            lines.append(f"[{number}] {role}: {content[:PREVIEW_CHARACTERS]}")
            if len(content) > PREVIEW_CHARACTERS:
                lines.append("[preview shortened; full content sent]")
        print("\n".join(lines), flush=True)
        return self.send(**kwargs)


@dataclass
class _PreviewChat:
    completions: _PreviewCompletions


@dataclass
class RequestPreviewClient:
    chat: _PreviewChat


def with_request_preview(client: Any) -> RequestPreviewClient:
    """Preview outgoing messages before forwarding the original SDK request.

    Only the terminal display is shortened; messages and responses are unchanged.
    A request preview does not confirm provider receipt or success.
    """
    return RequestPreviewClient(_PreviewChat(_PreviewCompletions(client.chat.completions.create)))
