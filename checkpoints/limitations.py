"""Offline comparisons: change one mechanism, then retry the same task.

Run with read --mode messages|tool, paging --offset 1|4, or loop --mode once|loop.
Prepared model messages drive real student tools. Only submitted tool evidence
counts toward completion; the prepared final reply never does.
"""

import argparse
import json
import re
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Literal

from agent import MODEL, run_agent
from checkpoints.stage2_one_tool import round_trip
from tests.fakes import FakeClient, text, tool_turn
from tools import TOOL_SCHEMAS, read_file

DEFAULT_PATH = "checkpoints/notes.txt"
Reader = Callable[..., str]
RunLoop = Callable[..., list[Any]]


@dataclass(frozen=True)
class ComparisonResult:
    """Evidence captured when requests were sent, independent of later mutation."""

    prompt: str
    requests: list[dict[str, Any]]
    observed_results: dict[str, str]
    pending_ids: list[str]
    visible_lines: list[int]
    evidence_complete: bool
    error: str | None = None


class _ObservedReplay:
    def __init__(self, replies: list[Any], reader: Reader) -> None:
        self._client = FakeClient(replies)
        self._reader = reader
        self._reads: list[tuple[dict[str, Any], str]] = []
        self._reads_at_request: list[list[tuple[dict[str, Any], str]]] = []
        self.requests: list[dict[str, Any]] = []
        self.replies: list[Any] = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs: Any) -> Any:
        self.requests.append(deepcopy(kwargs))
        self._reads_at_request.append(deepcopy(self._reads))
        response = self._client.chat.completions.create(**kwargs)
        self.replies.append(response.choices[0].message)
        return response

    def read(self, path: str, offset: int = 1, limit: int = 3) -> str:
        arguments = {"path": path, "offset": offset, "limit": limit}
        try:
            content = self._reader(**arguments)
        except Exception as error:
            self._reads.append((arguments, f"Error: {error}"))
            raise
        self._reads.append((arguments, content))
        return content

    def result(self, prompt: str, required_lines: set[int], error: str | None = None) -> ComparisonResult:
        observed: dict[str, str] = {}
        pending: list[str] = []
        for index, reply in enumerate(self.replies):
            for call in reply.tool_calls or []:
                arguments = json.loads(call.function.arguments)
                # Count feedback only after this proposal, from an actual read
                # already completed when the next request was submitted.
                for later in range(index + 1, len(self.requests)):
                    for message in self.requests[later]["messages"]:
                        if not isinstance(message, dict) or message.get("role") != "tool":
                            continue
                        content = message.get("content")
                        if (message.get("tool_call_id") == call.id
                                and (arguments, content) in self._reads_at_request[later]):
                            observed[call.id] = content
                if call.id not in observed:
                    pending.append(call.id)
        visible = sorted({
            int(number)
            for content in observed.values()
            for number in re.findall(r"^(\d+): ", content, flags=re.MULTILINE)
        })
        return ComparisonResult(
            prompt=prompt, requests=self.requests, observed_results=observed,
            pending_ids=pending, visible_lines=visible,
            evidence_complete=required_lines.issubset(visible) and not pending and error is None,
            error=error,
        )


def _read_proposal(path: str, offset: int, call_id: str = "read-1") -> Any:
    return tool_turn((call_id, "read_file", {"path": path, "offset": offset, "limit": 3}))


def run_read(
    mode: Literal["messages", "tool"], path: str = DEFAULT_PATH, *, reader: Reader = read_file,
) -> ComparisonResult:
    """Compare naming a file with returning its first three lines as tool feedback."""
    prompt = f"What are the first three lines of {path}?"
    if mode == "messages":
        replay = _ObservedReplay([text("The request names a file but supplies no file contents.")], reader)
        replay.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    elif mode == "tool":
        replay = _ObservedReplay([
            _read_proposal(path, 1), text("Prepared reply: inspect the actual tool evidence below."),
        ], reader)
        round_trip(replay, prompt, reader=replay.read)
    else:
        raise ValueError("read mode must be messages or tool")
    return replay.result(prompt, {1, 2, 3})


def run_paging(offset: int, path: str = DEFAULT_PATH, *, reader: Reader = read_file) -> ComparisonResult:
    """Keep the question and three-line budget fixed; change only the page offset."""
    prompt = f"What does line six of {path} say?"
    replay = _ObservedReplay([
        _read_proposal(path, offset), text("Prepared reply: a page only supports the lines it contains."),
    ], reader)
    round_trip(replay, prompt, reader=replay.read)
    return replay.result(prompt, {6})


def run_loop_comparison(
    mode: Literal["once", "loop"], path: str = DEFAULT_PATH, *,
    reader: Reader = read_file, run_loop: RunLoop = run_agent,
) -> ComparisonResult:
    """Replay identical proposals through one exchange or the student's full loop."""
    prompt = f"Read the first six lines of {path} in pages of three."
    replay = _ObservedReplay([
        _read_proposal(path, 1), _read_proposal(path, 4, "read-2"),
        text("Prepared reply: I have read the first six lines. Verify that claim against the tool evidence."),
    ], reader)
    error = None
    if mode == "once":
        round_trip(replay, prompt, reader=replay.read)
    elif mode == "loop":
        schemas = [tool for tool in TOOL_SCHEMAS if tool["function"]["name"] == "read_file"]
        try:
            run_loop(
                client=replay, messages=[{"role": "user", "content": prompt}],
                tools=schemas, registry={"read_file": replay.read}, max_iters=3,
            )
        except Exception as exception:
            error = f"{type(exception).__name__}: {exception}"
    else:
        raise ValueError("loop mode must be once or loop")
    return replay.result(prompt, {1, 2, 3, 4, 5, 6}, error)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="comparison", required=True)
    read_parser = commands.add_parser("read", help="Messages alone versus a real tool result")
    read_parser.add_argument("--mode", choices=("messages", "tool"), required=True)
    paging_parser = commands.add_parser("paging", help="A three-line page versus the next page")
    paging_parser.add_argument("--offset", type=int, required=True)
    loop_parser = commands.add_parser("loop", help="One exchange versus the student loop")
    loop_parser.add_argument("--mode", choices=("once", "loop"), required=True)
    for command in (read_parser, paging_parser, loop_parser):
        command.add_argument("--path", default=DEFAULT_PATH)
    args = parser.parse_args()
    print("OFFLINE: prepared model messages; real Python reads and recorded requests. No API key needed.")
    if args.comparison == "read":
        result = run_read(args.mode, args.path)
    elif args.comparison == "paging":
        result = run_paging(args.offset, args.path)
    else:
        result = run_loop_comparison(args.mode, args.path)
    print(f"TASK: {result.prompt}")
    for index, request in enumerate(result.requests, start=1):
        print(f"MODEL REQUEST {index} (messages):")
        print(json.dumps(request["messages"], indent=2, default=vars))
    print(f"OBSERVED TOOL RESULTS: {', '.join(result.observed_results) or 'none'}")
    for call_id, content in result.observed_results.items():
        print(f"EVIDENCE {call_id}:\n{content}")
    print(f"PENDING TOOL CALLS: {', '.join(result.pending_ids) or 'none'}")
    print(f"LINES IN SUBMITTED EVIDENCE: {', '.join(map(str, result.visible_lines)) or 'none'}")
    if args.comparison == "paging":
        print(f"LINE SIX IN RETURNED EVIDENCE: {'yes' if 6 in result.visible_lines else 'no'}")
    if result.error:
        print(f"LOOP ERROR: {result.error}")
    print(f"EVIDENCE COMPLETE: {'yes' if result.evidence_complete else 'no'}")
    print("A prepared answer is not evidence. Inspect the actual matching tool results above.")


if __name__ == "__main__":
    main()
